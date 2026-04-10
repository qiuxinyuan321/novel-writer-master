"""数据库引擎 - SQLAlchemy + SQLite."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from novel_craft.config import get_config


class Base(DeclarativeBase):
    """ORM 基类."""

    pass


_engine = None
_session_factory = None


def get_engine():
    """获取数据库引擎（延迟初始化）."""
    global _engine
    if _engine is None:
        config = get_config()
        db_path = Path(config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(_engine)
    return _engine


def get_session_factory():
    """获取 Session 工厂."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())
    return _session_factory


def get_session() -> Session:
    """获取一个新的数据库会话."""
    return get_session_factory()()


def init_db() -> None:
    """初始化数据库（创建所有表）."""
    engine = get_engine()
    Base.metadata.create_all(engine)
