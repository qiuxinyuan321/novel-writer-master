"""项目管理 Service - CRUD 操作."""

from __future__ import annotations

from novel_craft.db import get_session
from novel_craft.models import Novel


def list_novels() -> list[Novel]:
    """列出所有小说项目."""
    session = get_session()
    result = list(session.query(Novel).order_by(Novel.updated_at.desc()).all())
    session.close()
    return result


def get_novel(novel_id: str) -> Novel | None:
    """获取单个小说项目."""
    session = get_session()
    result = session.query(Novel).filter_by(id=novel_id).first()
    session.close()
    return result


def create_novel(title: str, genre: str = "", target_words: int = 100000,
                 style_reference: str = "", synopsis: str = "") -> Novel:
    """创建新小说项目."""
    session = get_session()
    novel = Novel(
        title=title,
        genre=genre,
        target_words=target_words,
        style_reference=style_reference,
        synopsis=synopsis,
    )
    session.add(novel)
    session.commit()
    session.refresh(novel)
    session.close()
    return novel


def update_novel(novel_id: str, **kwargs) -> Novel | None:
    """更新小说项目."""
    session = get_session()
    novel = session.query(Novel).filter_by(id=novel_id).first()
    if not novel:
        session.close()
        return None
    for key, value in kwargs.items():
        if hasattr(novel, key):
            setattr(novel, key, value)
    session.commit()
    session.refresh(novel)
    session.close()
    return novel


def delete_novel(novel_id: str) -> bool:
    """删除小说项目."""
    session = get_session()
    novel = session.query(Novel).filter_by(id=novel_id).first()
    if not novel:
        session.close()
        return False
    session.delete(novel)
    session.commit()
    session.close()
    return True
