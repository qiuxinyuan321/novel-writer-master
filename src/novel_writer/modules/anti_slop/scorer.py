"""AI 风险评分器 - 逐段评估 AI 生成痕迹.

基于本地统计指标加权计算风险分数，不消耗 API。
评分指标对标朱雀AI检测的核心维度。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

from novel_writer.config import AntiSlopConfig, get_config
from novel_writer.modules.anti_slop.analyzer import (
    SegmentMetrics,
    analyze_segment,
    split_paragraphs,
)
from novel_writer.modules.anti_slop.dictionary import get_dictionary

logger = logging.getLogger(__name__)

RiskLevel = Literal["low", "medium", "high"]


@dataclass
class SegmentScore:
    """单个段落的评分结果."""

    text: str
    index: int  # 段落序号（0-based）
    risk_score: float  # 0.0-1.0，越高越像 AI
    risk_level: RiskLevel
    metrics: SegmentMetrics

    # 各维度得分明细（0-1，越高越像 AI）
    detail: dict[str, float] = field(default_factory=dict)

    # 主要风险因素（人类可读的提示）
    risk_factors: list[str] = field(default_factory=list)


@dataclass
class DocumentScore:
    """整篇文档的评分结果."""

    segments: list[SegmentScore]
    overall_score: float  # 所有段落的加权平均
    overall_level: RiskLevel
    total_chars: int
    total_paragraphs: int

    # 统计
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0


def _normalize(value: float, low: float, high: float, invert: bool = False) -> float:
    """将原始值归一化到 0-1.

    Args:
        value: 原始值
        low: 人类写作的典型下界
        high: 人类写作的典型上界
        invert: True 时低值=高风险（如 TTR 低=AI）
    """
    if high <= low:
        return 0.5
    normalized = max(0.0, min(1.0, (value - low) / (high - low)))
    return 1.0 - normalized if invert else normalized


def score_segment(text: str, config: AntiSlopConfig | None = None) -> SegmentScore:
    """评分单个段落.

    Returns:
        SegmentScore，risk_score 越接近 1.0 越像 AI 生成。
    """
    if config is None:
        config = get_config().anti_slop

    # 获取黑名单命中
    dictionary = get_dictionary()
    blacklist_hits = dictionary.count_hits(text)

    # 分析文本指标
    metrics = analyze_segment(text, blacklist_hits)

    # 各维度评分（归一化到 0-1，越高越像 AI）
    detail: dict[str, float] = {}
    risk_factors: list[str] = []

    # 1. 黑名单密度 - 命中词越多越像 AI
    # 人类写作中偶尔也会用，但密度不会太高
    bl_score = _normalize(metrics.blacklist_density, 0.0, 0.05)
    detail["blacklist_density"] = bl_score
    if bl_score > 0.5:
        top_hits = sorted(blacklist_hits.items(), key=lambda x: -x[1])[:5]
        hit_str = ", ".join(f"「{w}」×{c}" for w, c in top_hits)
        risk_factors.append(f"AI高频词密度偏高: {hit_str}")

    # 2. TTR (词汇多样性) - TTR 低=用词重复=AI
    # 人类小说 TTR 通常在 0.4-0.7，AI 通常 0.3-0.5
    ttr_score = _normalize(metrics.ttr, 0.35, 0.65, invert=True)
    detail["ttr"] = ttr_score
    if ttr_score > 0.6:
        risk_factors.append(f"词汇多样性偏低 (TTR={metrics.ttr:.2f})")

    # 3. 句长变异系数 - 低变异=句式节奏均匀=AI
    # 人类写作 CV 通常在 0.3-0.8，AI 通常 0.1-0.4
    sv_score = _normalize(metrics.sentence_len_cv, 0.25, 0.70, invert=True)
    detail["sentence_variance"] = sv_score
    if sv_score > 0.6:
        risk_factors.append(f"句式节奏过于均匀 (CV={metrics.sentence_len_cv:.2f})")

    # 4. 结构模式 - 命中越多越像 AI
    pattern_ratio = len(metrics.structure_patterns) / max(1, metrics.sentence_count / 5)
    sp_score = min(1.0, pattern_ratio)
    detail["structure_pattern"] = sp_score
    if metrics.structure_patterns:
        pattern_names = {
            "three_parallel": "三段并列",
            "total_sub_total": "总分总结构",
            "not_only_but_also": "不仅…而且",
            "not_x_but_y": "不是…而是",
            "on_one_hand": "一方面…另一方面",
            "although_but": "虽然…但是",
            "because_so": "因为…所以",
        }
        names = [pattern_names.get(p, p) for p in metrics.structure_patterns]
        risk_factors.append(f"命中AI典型句式: {', '.join(names)}")

    # 5. 句式重复度 - 相邻句子结构越相似越像 AI
    # 人类通常 0.1-0.4，AI 通常 0.3-0.6
    rep_score = _normalize(metrics.repetition_score, 0.15, 0.55)
    detail["repetition"] = rep_score
    if rep_score > 0.5:
        risk_factors.append(f"相邻句式重复度偏高 ({metrics.repetition_score:.2f})")

    # 加权总分
    weights = config.weights
    risk_score = (
        detail.get("blacklist_density", 0) * weights.get("blacklist_density", 0.3)
        + detail.get("ttr", 0) * weights.get("ttr", 0.25)
        + detail.get("sentence_variance", 0) * weights.get("sentence_variance", 0.2)
        + detail.get("structure_pattern", 0) * weights.get("structure_pattern", 0.15)
        + detail.get("repetition", 0) * weights.get("repetition", 0.1)
    )
    risk_score = max(0.0, min(1.0, risk_score))

    # 风险等级
    thresholds = config.thresholds
    if risk_score >= thresholds.get("high", 0.6):
        risk_level: RiskLevel = "high"
    elif risk_score >= thresholds.get("low", 0.3):
        risk_level = "medium"
    else:
        risk_level = "low"

    return SegmentScore(
        text=text,
        index=0,
        risk_score=risk_score,
        risk_level=risk_level,
        metrics=metrics,
        detail=detail,
        risk_factors=risk_factors,
    )


def score_document(text: str, config: AntiSlopConfig | None = None) -> DocumentScore:
    """评分整篇文档（逐段评分后汇总）."""
    if config is None:
        config = get_config().anti_slop

    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return DocumentScore(
            segments=[],
            overall_score=0.0,
            overall_level="low",
            total_chars=0,
            total_paragraphs=0,
        )

    segments: list[SegmentScore] = []
    for i, para in enumerate(paragraphs):
        seg_score = score_segment(para, config)
        seg_score.index = i
        segments.append(seg_score)

    # 加权平均（按段落长度加权）
    total_chars = sum(s.metrics.char_count for s in segments)
    if total_chars > 0:
        overall = sum(s.risk_score * s.metrics.char_count for s in segments) / total_chars
    else:
        overall = 0.0

    # 统计
    thresholds = config.thresholds
    high_count = sum(1 for s in segments if s.risk_level == "high")
    medium_count = sum(1 for s in segments if s.risk_level == "medium")
    low_count = sum(1 for s in segments if s.risk_level == "low")

    if overall >= thresholds.get("high", 0.6):
        overall_level: RiskLevel = "high"
    elif overall >= thresholds.get("low", 0.3):
        overall_level = "medium"
    else:
        overall_level = "low"

    return DocumentScore(
        segments=segments,
        overall_score=overall,
        overall_level=overall_level,
        total_chars=total_chars,
        total_paragraphs=len(paragraphs),
        high_risk_count=high_count,
        medium_risk_count=medium_count,
        low_risk_count=low_count,
    )
