"""文本统计分析器 - 本地计算 AI 写作特征指标.

所有分析在本地完成，不消耗 API，毫秒级响应。
指标体系对标朱雀AI检测的核心维度：困惑度(词汇多样性)、突发性(句长变异)、语义指纹(结构模式)。
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

import jieba


@dataclass
class SegmentMetrics:
    """单个段落的分析指标."""

    text: str
    char_count: int = 0
    word_count: int = 0

    # 词汇多样性
    ttr: float = 0.0  # Type-Token Ratio (unique_words / total_words)
    hapax_ratio: float = 0.0  # 只出现一次的词占比

    # 句长变异（突发性 burstiness）
    sentence_count: int = 0
    avg_sentence_len: float = 0.0
    sentence_len_cv: float = 0.0  # 变异系数 (std/mean)，低=AI

    # 黑名单命中
    blacklist_hits: dict[str, int] = field(default_factory=dict)
    blacklist_density: float = 0.0  # 命中词数 / 总字数

    # 结构模式
    structure_patterns: list[str] = field(default_factory=list)  # 命中的模式名

    # 句式重复
    repetition_score: float = 0.0  # 相邻句子结构相似度


# 中文句子分割（按句号、问号、感叹号、省略号分割）
_SENTENCE_SPLIT = re.compile(r"[。！？…]+|[.!?]+")

# 段落结构模式检测
_STRUCTURE_PATTERNS = {
    "three_parallel": re.compile(
        r"(?:首先|第一|其一).{5,}?(?:其次|第二|其二).{5,}?(?:再次|第三|其三|最后)"
    ),
    "total_sub_total": re.compile(r".{10,}?[：:].{20,}?(?:总之|综上|总而言之|由此可见)"),
    "not_only_but_also": re.compile(r"不仅.{3,}?而且"),
    "not_x_but_y": re.compile(r"不是.{3,}?而是"),
    "on_one_hand": re.compile(r"一方面.{5,}?另一方面"),
    "although_but": re.compile(r"(?:虽然|尽管).{3,}?(?:但是|然而|却)"),
    "because_so": re.compile(r"因为.{3,}?所以"),
}


def split_sentences(text: str) -> list[str]:
    """将文本分割为句子列表."""
    parts = _SENTENCE_SPLIT.split(text.strip())
    return [s.strip() for s in parts if s.strip() and len(s.strip()) > 1]


def split_paragraphs(text: str) -> list[str]:
    """将文本分割为段落列表."""
    paragraphs = re.split(r"\n\s*\n|\n", text.strip())
    return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 5]


def calc_ttr(words: list[str]) -> float:
    """计算 Type-Token Ratio（词汇多样性）.

    TTR = unique_words / total_words
    AI 文本通常 TTR 偏低（用词重复）。
    """
    if not words:
        return 0.0
    unique = set(words)
    return len(unique) / len(words)


def calc_hapax_ratio(words: list[str]) -> float:
    """计算 Hapax Legomena 比率（只出现一次的词占比）.

    高 hapax 比率意味着用词更多样、更"人类"。
    """
    if not words:
        return 0.0
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    hapax = sum(1 for v in freq.values() if v == 1)
    return hapax / len(words)


def calc_sentence_variance(sentences: list[str]) -> tuple[float, float]:
    """计算句子长度的变异系数.

    返回 (平均句长, 变异系数)。
    变异系数 = 标准差 / 均值。低变异 = 句式节奏均匀 = AI 特征。
    """
    if len(sentences) < 2:
        return (len(sentences[0]) if sentences else 0, 0.0)

    lengths = [len(s) for s in sentences]
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return (0.0, 0.0)

    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std = math.sqrt(variance)
    cv = std / mean
    return (mean, cv)


def detect_structure_patterns(text: str) -> list[str]:
    """检测段落中的 AI 典型结构模式."""
    detected = []
    for name, pattern in _STRUCTURE_PATTERNS.items():
        if pattern.search(text):
            detected.append(name)
    return detected


def calc_repetition_score(sentences: list[str]) -> float:
    """计算相邻句子的结构相似度.

    通过比较相邻句子的长度比和词汇重叠来评估。
    高相似度 = AI 特征（句式重复）。
    """
    if len(sentences) < 2:
        return 0.0

    similarities = []
    for i in range(len(sentences) - 1):
        s1, s2 = sentences[i], sentences[i + 1]
        # 长度相似度
        len1, len2 = len(s1), len(s2)
        if max(len1, len2) == 0:
            continue
        len_sim = min(len1, len2) / max(len1, len2)

        # 词汇重叠度
        words1 = set(jieba.cut(s1))
        words2 = set(jieba.cut(s2))
        union = words1 | words2
        if not union:
            continue
        overlap = len(words1 & words2) / len(union)

        # 综合相似度
        similarity = 0.4 * len_sim + 0.6 * overlap
        similarities.append(similarity)

    return sum(similarities) / len(similarities) if similarities else 0.0


def analyze_segment(text: str, blacklist_hits: dict[str, int] | None = None) -> SegmentMetrics:
    """分析一个文本段落，返回所有指标.

    Args:
        text: 段落文本
        blacklist_hits: 预计算的黑名单命中（可选，由 scorer 传入）

    Returns:
        SegmentMetrics 包含所有分析指标
    """
    words = list(jieba.cut(text))
    # 过滤标点和空白
    words = [w for w in words if w.strip() and not re.match(r"^[\s\W]+$", w)]

    sentences = split_sentences(text)

    ttr = calc_ttr(words)
    hapax = calc_hapax_ratio(words)
    avg_len, cv = calc_sentence_variance(sentences)
    patterns = detect_structure_patterns(text)
    rep_score = calc_repetition_score(sentences)

    # 黑名单密度
    total_hits = sum((blacklist_hits or {}).values())
    density = total_hits / len(text) if text else 0.0

    return SegmentMetrics(
        text=text,
        char_count=len(text),
        word_count=len(words),
        ttr=ttr,
        hapax_ratio=hapax,
        sentence_count=len(sentences),
        avg_sentence_len=avg_len,
        sentence_len_cv=cv,
        blacklist_hits=blacklist_hits or {},
        blacklist_density=density,
        structure_patterns=patterns,
        repetition_score=rep_score,
    )
