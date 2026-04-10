"""大纲 Service - 分层大纲 CRUD + 检查点管理."""

from __future__ import annotations

from novel_craft.db import get_session
from novel_craft.models import Chapter, Outline


def list_outlines(novel_id: str, parent_id: str | None = None) -> list[Outline]:
    """列出指定层级的大纲节点."""
    session = get_session()
    q = session.query(Outline).filter_by(novel_id=novel_id, parent_id=parent_id)
    result = list(q.order_by(Outline.order_index).all())
    session.close()
    return result


def get_outline(outline_id: str) -> Outline | None:
    session = get_session()
    result = session.query(Outline).filter_by(id=outline_id).first()
    session.close()
    return result


def create_outline(novel_id: str, level: str, title: str,
                   parent_id: str | None = None,
                   narrative_goal: str = "",
                   emotion_target: str = "",
                   checkpoints: list[dict] | None = None,
                   content_preview: str = "",
                   order_index: int = 0) -> Outline:
    """创建大纲节点."""
    session = get_session()
    outline = Outline(
        novel_id=novel_id,
        parent_id=parent_id,
        level=level,
        title=title,
        order_index=order_index,
        narrative_goal=narrative_goal,
        emotion_target=emotion_target,
        checkpoints=checkpoints or [],
        content_preview=content_preview,
    )
    session.add(outline)
    session.commit()
    session.refresh(outline)

    # 如果是章级大纲，自动创建对应的 Chapter
    if level == "chapter":
        existing = session.query(Chapter).filter_by(outline_id=outline.id).first()
        if not existing:
            chapter_num = order_index + 1
            chapter = Chapter(
                novel_id=novel_id,
                outline_id=outline.id,
                number=chapter_num,
                title=title,
            )
            session.add(chapter)
            session.commit()

    session.close()
    return outline


def update_outline(outline_id: str, **kwargs) -> Outline | None:
    session = get_session()
    outline = session.query(Outline).filter_by(id=outline_id).first()
    if not outline:
        session.close()
        return None
    for key, value in kwargs.items():
        if hasattr(outline, key):
            setattr(outline, key, value)
    session.commit()
    session.refresh(outline)
    session.close()
    return outline


def delete_outline(outline_id: str) -> bool:
    session = get_session()
    outline = session.query(Outline).filter_by(id=outline_id).first()
    if not outline:
        session.close()
        return False
    session.delete(outline)
    session.commit()
    session.close()
    return True


def get_outline_tree(novel_id: str) -> list[dict]:
    """获取完整大纲树结构（递归）."""
    session = get_session()
    all_outlines = list(
        session.query(Outline)
        .filter_by(novel_id=novel_id)
        .order_by(Outline.order_index)
        .all()
    )
    session.close()

    # 构建树
    by_parent: dict[str | None, list[Outline]] = {}
    for o in all_outlines:
        by_parent.setdefault(o.parent_id, []).append(o)

    def build_tree(parent_id: str | None) -> list[dict]:
        children = by_parent.get(parent_id, [])
        return [
            {
                "id": o.id,
                "level": o.level,
                "title": o.title,
                "narrative_goal": o.narrative_goal,
                "emotion_target": o.emotion_target,
                "checkpoints": o.checkpoints or [],
                "status": o.status,
                "children": build_tree(o.id),
            }
            for o in children
        ]

    return build_tree(None)
