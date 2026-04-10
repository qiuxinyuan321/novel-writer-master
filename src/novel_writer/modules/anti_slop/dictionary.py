"""Anti-slop 黑名单词库管理.

从 JSON 文件加载 AI 高频词/句式黑名单，支持按分类和严重级别过滤。
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

Severity = Literal["ban", "warn", "limit"]
Category = Literal["connector", "filler", "cliche", "emotion", "action", "narration", "dialogue"]


@dataclass
class SlopWord:
    """一个黑名单词条."""

    word: str
    category: Category
    severity: Severity
    max_per_chapter: int = 0  # severity=limit 时有效

    @property
    def is_banned(self) -> bool:
        return self.severity == "ban"


@dataclass
class SlopDictionary:
    """黑名单词库."""

    words: list[SlopWord] = field(default_factory=list)
    _word_set: set[str] = field(default_factory=set, repr=False)
    _ban_set: set[str] = field(default_factory=set, repr=False)

    def __post_init__(self) -> None:
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """重建查找索引."""
        self._word_set = {w.word for w in self.words}
        self._ban_set = {w.word for w in self.words if w.is_banned}

    @property
    def total(self) -> int:
        return len(self.words)

    @property
    def ban_count(self) -> int:
        return len(self._ban_set)

    def contains(self, text: str) -> list[SlopWord]:
        """检查文本中包含的黑名单词，返回匹配列表."""
        matches = []
        for sw in self.words:
            if sw.word in text:
                matches.append(sw)
        return matches

    def count_hits(self, text: str) -> dict[str, int]:
        """统计文本中每个黑名单词的出现次数."""
        hits: dict[str, int] = {}
        for sw in self.words:
            count = text.count(sw.word)
            if count > 0:
                hits[sw.word] = count
        return hits

    def by_category(self, category: Category) -> list[SlopWord]:
        """按分类过滤."""
        return [w for w in self.words if w.category == category]

    def by_severity(self, severity: Severity) -> list[SlopWord]:
        """按严重级别过滤."""
        return [w for w in self.words if w.severity == severity]

    def sample_for_prompt(self, n: int = 50) -> list[str]:
        """随机抽取 n 个 ban 级别的词，用于注入 prompt.

        每次随机抽取避免模型形成固定规避模式。
        """
        banned = list(self._ban_set)
        if len(banned) <= n:
            return banned
        return random.sample(banned, n)


def load_dictionary(path: str | Path | None = None) -> SlopDictionary:
    """从 JSON 文件加载词库."""
    if path is None:
        # 默认路径：项目根目录/data/anti_slop_zh.json
        candidates = [
            Path("data/anti_slop_zh.json"),
            Path(__file__).parent.parent.parent.parent.parent / "data" / "anti_slop_zh.json",
        ]
        for p in candidates:
            if p.exists():
                path = p
                break

    if path is None or not Path(path).exists():
        logger.warning("未找到 anti_slop_zh.json 词库文件，使用空词库")
        return SlopDictionary()

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    words = []
    for item in data.get("words", []):
        words.append(
            SlopWord(
                word=item["word"],
                category=item.get("category", "cliche"),
                severity=item.get("severity", "warn"),
                max_per_chapter=item.get("max_per_chapter", 0),
            )
        )

    dictionary = SlopDictionary(words=words)
    logger.info(f"已加载 anti-slop 词库: {dictionary.total} 词条 ({dictionary.ban_count} 个禁用)")
    return dictionary


# 全局单例
_dict: SlopDictionary | None = None


def get_dictionary() -> SlopDictionary:
    """获取全局词库单例."""
    global _dict
    if _dict is None:
        _dict = load_dictionary()
    return _dict
