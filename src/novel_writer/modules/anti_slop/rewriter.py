"""高风险段落改写器 - 仅对 AI 痕迹重的段落调用 LLM 改写.

改写策略针对具体风险点：词汇替换、句式打乱、口语化注入、模糊性注入。
改写后重新评分，最多循环 max_rewrite_rounds 次。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from novel_writer.config import get_config
from novel_writer.llm.router import get_router
from novel_writer.modules.anti_slop.scorer import (
    DocumentScore,
    SegmentScore,
    score_document,
    score_segment,
)

logger = logging.getLogger(__name__)

REWRITE_SYSTEM_PROMPT = """\
你是一位经验丰富的中文小说编辑，专门负责润色文本使其更像人类手写。
你的任务是改写以下段落，降低其 AI 生成痕迹，同时保持原文含义不变。

## 改写规则（必须严格遵守）

1. **保持原意**：不改变情节、人物行为、对话含义
2. **打乱句式**：交替使用长句（>30字）和短句（<10字），制造节奏变化
3. **替换AI高频词**：将标注的高频词替换为更自然的表达
4. **注入口语化**：适当加入语气词、停顿词（"嗯"、"呃"、"那个"、"反正"）
5. **注入模糊性**：用"大概"、"好像"、"差不多"替代过于精确的表述
6. **打破结构模板**：避免"首先/其次/最后"、"不仅…而且"等模板句式
7. **增加不完美**：可以有轻微的口语语法、不完整句、省略句
8. **控制篇幅**：改写后字数应与原文相近（±20%）

## 输出要求
直接输出改写后的文本，不要输出解释或标注。"""


def _build_rewrite_prompt(segment: SegmentScore) -> str:
    """根据段落的具体风险点构建改写 prompt."""
    lines = ["请改写以下段落：\n"]

    # 标注具体风险点
    if segment.risk_factors:
        lines.append("### 需要重点修改的问题：")
        for factor in segment.risk_factors:
            lines.append(f"- {factor}")
        lines.append("")

    # 标注命中的黑名单词
    if segment.metrics.blacklist_hits:
        top_hits = sorted(segment.metrics.blacklist_hits.items(), key=lambda x: -x[1])[:10]
        hit_words = [f"「{w}」" for w, _ in top_hits]
        lines.append(f"### 需要替换的AI高频词：{', '.join(hit_words)}\n")

    lines.append("### 原文：")
    lines.append(segment.text)

    return "\n".join(lines)


@dataclass
class RewriteResult:
    """改写结果."""

    original: str
    rewritten: str
    original_score: float
    new_score: float
    rounds: int  # 实际改写轮数
    improved: bool  # 是否有效降低风险


async def rewrite_segment(segment: SegmentScore) -> RewriteResult:
    """改写单个高风险段落.

    调用 LLM 改写，改写后重新评分。
    如果仍为高风险，最多再尝试 max_rewrite_rounds-1 次。
    """
    config = get_config()
    router = get_router()
    client = router.get_client("rewrite")
    max_rounds = config.anti_slop.max_rewrite_rounds

    current_text = segment.text
    current_score = segment.risk_score
    original_score = current_score

    for round_num in range(1, max_rounds + 1):
        prompt = _build_rewrite_prompt(segment)

        try:
            rewritten = await client.chat(
                messages=[
                    {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,  # 略高温度增加随机性
            )
        except Exception as e:
            logger.error(f"改写失败 (第{round_num}轮): {e}")
            break

        rewritten = rewritten.strip()
        if not rewritten:
            break

        # 重新评分
        new_seg = score_segment(rewritten, config.anti_slop)
        new_score = new_seg.risk_score

        logger.info(
            f"改写第{round_num}轮: {current_score:.2f} -> {new_score:.2f} "
            f"({'改善' if new_score < current_score else '未改善'})"
        )

        if new_score < current_score:
            current_text = rewritten
            current_score = new_score
            segment = new_seg  # 更新 segment 用于下一轮

        # 如果已降到低风险，停止
        if current_score < config.anti_slop.thresholds.get("low", 0.3):
            break

    return RewriteResult(
        original=segment.text if round_num == 1 else segment.text,
        rewritten=current_text,
        original_score=original_score,
        new_score=current_score,
        rounds=round_num,
        improved=current_score < original_score,
    )


async def rewrite_document(doc_score: DocumentScore) -> list[RewriteResult]:
    """改写文档中所有高风险和中风险段落.

    低风险段落保持不变。

    Returns:
        改写结果列表，与 doc_score.segments 一一对应。
        未改写的段落 original == rewritten。
    """
    results: list[RewriteResult] = []

    for seg in doc_score.segments:
        if seg.risk_level in ("high", "medium"):
            result = await rewrite_segment(seg)
            results.append(result)
        else:
            # 低风险段保持不变
            results.append(
                RewriteResult(
                    original=seg.text,
                    rewritten=seg.text,
                    original_score=seg.risk_score,
                    new_score=seg.risk_score,
                    rounds=0,
                    improved=False,
                )
            )

    return results
