"""生成引擎 Service - 场景生成 + 摘要 + 检查点验证."""

from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from novel_craft.config import get_config
from novel_craft.db import get_session
from novel_craft.llm.router import get_router
from novel_craft.models import (
    Chapter,
    ChapterSummary,
    Character,
    Foreshadowing,
    Novel,
    Outline,
    Scene,
    WorldSetting,
)
from novel_craft.modules.anti_slop.dictionary import get_dictionary
from novel_craft.modules.anti_slop.scorer import score_document

logger = logging.getLogger(__name__)

# Jinja2 模板环境
_template_dir = Path(__file__).parent.parent.parent / "llm" / "prompts"
_jinja_env = Environment(loader=FileSystemLoader(str(_template_dir)), autoescape=False)


def _get_previous_summary(novel_id: str, chapter_number: int) -> str:
    """获取前几章的摘要（滑动窗口）."""
    session = get_session()
    # 获取前 3 章的摘要
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
    result = "\n\n".join(summaries) if summaries else ""
    session.close()
    return result


def _get_previous_ending(novel_id: str, chapter_number: int) -> str:
    """获取上一个场景的结尾文本（约500字）."""
    session = get_session()
    prev_chapter = (
        session.query(Chapter)
        .filter(Chapter.novel_id == novel_id, Chapter.number == chapter_number - 1)
        .first()
    )
    if not prev_chapter:
        session.close()
        return ""
    last_scene = (
        session.query(Scene)
        .filter_by(chapter_id=prev_chapter.id)
        .order_by(Scene.order_index.desc())
        .first()
    )
    if last_scene and last_scene.content:
        result = last_scene.content[-500:]
        session.close()
        return result
    session.close()
    return ""


async def generate_scene(
    novel_id: str,
    chapter_id: str,
    outline_id: str | None = None,
    character_ids: list[str] | None = None,
    target_words: int = 1500,
) -> Scene:
    """生成一个场景的正文.

    完整流水线：收集上下文 → 组装 Prompt → 调用 LLM → 评分 → 保存
    """
    session = get_session()
    novel = session.query(Novel).filter_by(id=novel_id).first()
    chapter = session.query(Chapter).filter_by(id=chapter_id).first()

    if not novel or not chapter:
        session.close()
        raise ValueError("小说或章节不存在")

    # 收集大纲信息
    outline = None
    narrative_goal = ""
    emotion_target = ""
    checkpoints = []
    scene_title = ""

    if outline_id:
        outline = session.query(Outline).filter_by(id=outline_id).first()
        if outline:
            narrative_goal = outline.narrative_goal
            emotion_target = outline.emotion_target
            checkpoints = outline.checkpoints or []
            scene_title = outline.title

    # 如果没有场景大纲，使用章级大纲
    if not narrative_goal and chapter.outline_id:
        ch_outline = session.query(Outline).filter_by(id=chapter.outline_id).first()
        if ch_outline:
            narrative_goal = ch_outline.narrative_goal
            emotion_target = ch_outline.emotion_target
            checkpoints = ch_outline.checkpoints or []

    # 收集角色
    characters = []
    if character_ids:
        characters = list(
            session.query(Character)
            .filter(Character.id.in_(character_ids))
            .all()
        )
    else:
        # 默认取所有主角和反派
        characters = list(
            session.query(Character)
            .filter_by(novel_id=novel_id)
            .filter(Character.role.in_(["protagonist", "antagonist"]))
            .all()
        )

    # 世界观设定（硬规则优先）
    world_settings = list(
        session.query(WorldSetting)
        .filter_by(novel_id=novel_id)
        .order_by(WorldSetting.is_hard_rule.desc())
        .limit(10)
        .all()
    )

    # 待回收伏笔
    foreshadowings = list(
        session.query(Foreshadowing)
        .filter(
            Foreshadowing.novel_id == novel_id,
            Foreshadowing.status == "planted",
            Foreshadowing.target_chapter == chapter.number,
        )
        .all()
    )
    session.close()

    # 前文上下文
    previous_summary = _get_previous_summary(novel_id, chapter.number)
    previous_ending = _get_previous_ending(novel_id, chapter.number)

    # Anti-slop 词汇（随机抽取）
    dictionary = get_dictionary()
    banned_words = dictionary.sample_for_prompt(50)

    # 组装 Prompt
    template = _jinja_env.get_template("generate_scene.j2")
    prompt = template.render(
        novel_title=novel.title,
        genre=novel.genre,
        style_reference=novel.style_reference,
        chapter_number=chapter.number,
        chapter_title=chapter.title,
        scene_title=scene_title,
        narrative_goal=narrative_goal,
        emotion_target=emotion_target,
        checkpoints=checkpoints,
        characters=characters,
        world_settings=world_settings,
        foreshadowings=foreshadowings,
        previous_summary=previous_summary,
        previous_ending=previous_ending,
        banned_words=banned_words,
        target_words=target_words,
    )

    # 调用 LLM
    router = get_router()
    client = router.get_client("generation")
    content = await client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=target_words * 3,  # 中文约 1.5 token/字
    )

    # AI 风险评分
    doc_score = score_document(content)
    risk_score = doc_score.overall_score

    # 保存场景
    session = get_session()
    # 计算排序序号
    existing_count = session.query(Scene).filter_by(chapter_id=chapter_id).count()

    scene = Scene(
        chapter_id=chapter_id,
        outline_id=outline_id,
        order_index=existing_count,
        content=content,
        word_count=len(content),
        characters_present=[c.id for c in characters] if characters else [],
        emotion_actual=emotion_target,
        ai_risk_score=risk_score,
    )
    session.add(scene)

    # 更新章节字数
    chapter = session.query(Chapter).filter_by(id=chapter_id).first()
    if chapter:
        total_words = sum(
            s.word_count for s in session.query(Scene).filter_by(chapter_id=chapter_id).all()
        ) + len(content)
        chapter.word_count = total_words
        chapter.status = "draft"

    session.commit()
    session.refresh(scene)
    session.close()
    return scene


async def generate_chapter_summary(chapter_id: str) -> ChapterSummary:
    """生成章节摘要."""
    session = get_session()
    chapter = session.query(Chapter).filter_by(id=chapter_id).first()
    if not chapter:
        session.close()
        raise ValueError("章节不存在")

    scenes = list(
        session.query(Scene)
        .filter_by(chapter_id=chapter_id)
        .order_by(Scene.order_index)
        .all()
    )
    chapter_content = "\n\n".join(s.content for s in scenes if s.content)

    if not chapter_content:
        session.close()
        raise ValueError("章节没有正文内容")

    session.close()

    # 组装 Prompt
    template = _jinja_env.get_template("summarize_chapter.j2")
    prompt = template.render(
        chapter_number=chapter.number,
        chapter_title=chapter.title,
        chapter_content=chapter_content,
    )

    # 调用 LLM
    router = get_router()
    client = router.get_client("summary")
    summary_text = await client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    # 保存摘要
    session = get_session()
    existing = session.query(ChapterSummary).filter_by(chapter_id=chapter_id).first()
    if existing:
        existing.content = summary_text
        session.commit()
        session.refresh(existing)
        session.close()
        return existing
    else:
        summary = ChapterSummary(
            chapter_id=chapter_id,
            content=summary_text,
        )
        session.add(summary)
        session.commit()
        session.refresh(summary)
        session.close()
        return summary
