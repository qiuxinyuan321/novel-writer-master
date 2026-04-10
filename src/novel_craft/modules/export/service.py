"""导出 Service - 合并章节为完整文本."""

from __future__ import annotations

from novel_craft.db import get_session
from novel_craft.models import Chapter, Novel, Scene


def export_novel_txt(novel_id: str) -> str:
    """导出小说为纯文本格式."""
    session = get_session()
    novel = session.query(Novel).filter_by(id=novel_id).first()
    if not novel:
        session.close()
        raise ValueError("小说不存在")

    chapters = list(
        session.query(Chapter)
        .filter_by(novel_id=novel_id)
        .order_by(Chapter.number)
        .all()
    )

    lines = [f"《{novel.title}》", ""]
    if novel.synopsis:
        lines.extend(["简介：", novel.synopsis, ""])
    lines.append("=" * 40)
    lines.append("")

    total_words = 0
    for ch in chapters:
        scenes = list(
            session.query(Scene)
            .filter_by(chapter_id=ch.id)
            .order_by(Scene.order_index)
            .all()
        )
        if not scenes:
            continue

        lines.append(f"第{ch.number}章 {ch.title}")
        lines.append("")

        for scene in scenes:
            if scene.content:
                lines.append(scene.content)
                lines.append("")
                total_words += scene.word_count

        lines.append("")

    session.close()

    lines.append("=" * 40)
    lines.append(f"全文共 {total_words} 字")

    return "\n".join(lines)


def get_novel_stats(novel_id: str) -> dict:
    """获取小说统计信息."""
    session = get_session()
    novel = session.query(Novel).filter_by(id=novel_id).first()
    if not novel:
        session.close()
        return {}

    chapters = list(
        session.query(Chapter)
        .filter_by(novel_id=novel_id)
        .order_by(Chapter.number)
        .all()
    )

    chapter_stats = []
    total_words = 0
    for ch in chapters:
        scenes = list(
            session.query(Scene)
            .filter_by(chapter_id=ch.id)
            .order_by(Scene.order_index)
            .all()
        )
        ch_words = sum(s.word_count for s in scenes)
        avg_risk = (sum(s.ai_risk_score for s in scenes) / len(scenes)) if scenes else 0
        total_words += ch_words

        # 获取情绪
        from novel_craft.models import Outline
        outline = session.query(Outline).filter_by(id=ch.outline_id).first() if ch.outline_id else None
        emotion = outline.emotion_target if outline else ""

        chapter_stats.append({
            "number": ch.number,
            "title": ch.title,
            "word_count": ch_words,
            "scene_count": len(scenes),
            "avg_ai_risk": avg_risk,
            "emotion": emotion,
            "status": ch.status,
        })

    session.close()

    return {
        "title": novel.title,
        "genre": novel.genre,
        "target_words": novel.target_words,
        "total_words": total_words,
        "total_chapters": len(chapters),
        "progress": total_words / novel.target_words if novel.target_words > 0 else 0,
        "chapters": chapter_stats,
    }
