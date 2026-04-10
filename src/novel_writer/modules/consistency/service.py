"""一致性检查 Service - LLM 驱动的矛盾检测."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from novel_writer.db import get_session
from novel_writer.llm.router import get_router
from novel_writer.models import Chapter, Character, Novel, Scene, WorldSetting

logger = logging.getLogger(__name__)

_template_dir = Path(__file__).parent.parent.parent / "llm" / "prompts"
_jinja_env = Environment(loader=FileSystemLoader(str(_template_dir)), autoescape=False)


@dataclass
class ConsistencyIssue:
    """一个一致性问题."""
    category: str       # 角色/世界观/时间/称谓/伏笔
    description: str
    quote: str = ""     # 相关原文
    suggestion: str = ""


@dataclass
class ConsistencyReport:
    """一致性检查报告."""
    chapter_number: int
    issues: list[ConsistencyIssue] = field(default_factory=list)
    raw_response: str = ""
    is_clean: bool = False


def _get_previous_summary(novel_id: str, chapter_number: int) -> str:
    session = get_session()
    prev_chapters = (
        session.query(Chapter)
        .filter(Chapter.novel_id == novel_id, Chapter.number < chapter_number)
        .order_by(Chapter.number.desc())
        .limit(3)
        .all()
    )
    summaries = []
    for ch in reversed(prev_chapters):
        if ch.summary and ch.summary.content:
            summaries.append(f"第{ch.number}章《{ch.title}》:\n{ch.summary.content}")
    session.close()
    return "\n\n".join(summaries)


async def check_chapter_consistency(chapter_id: str) -> ConsistencyReport:
    """检查一个章节的一致性."""
    session = get_session()
    chapter = session.query(Chapter).filter_by(id=chapter_id).first()
    if not chapter:
        session.close()
        raise ValueError("章节不存在")

    novel = session.query(Novel).filter_by(id=chapter.novel_id).first()
    scenes = list(
        session.query(Scene)
        .filter_by(chapter_id=chapter_id)
        .order_by(Scene.order_index)
        .all()
    )
    scene_content = "\n\n".join(s.content for s in scenes if s.content)
    if not scene_content:
        session.close()
        raise ValueError("章节没有正文")

    characters = list(
        session.query(Character)
        .filter_by(novel_id=chapter.novel_id)
        .all()
    )
    world_settings = list(
        session.query(WorldSetting)
        .filter_by(novel_id=chapter.novel_id)
        .all()
    )
    novel_title = novel.title if novel else ""
    novel_id = chapter.novel_id
    ch_number = chapter.number
    session.close()

    previous_summary = _get_previous_summary(novel_id, ch_number)

    template = _jinja_env.get_template("check_consistency.j2")
    prompt = template.render(
        novel_title=novel_title,
        chapter_number=ch_number,
        scene_content=scene_content,
        characters=characters,
        world_settings=world_settings,
        previous_summary=previous_summary,
    )

    router = get_router()
    client = router.get_client("consistency_check")
    response = await client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    is_clean = "未发现一致性问题" in response or "✅" in response

    return ConsistencyReport(
        chapter_number=ch_number,
        raw_response=response,
        is_clean=is_clean,
    )
