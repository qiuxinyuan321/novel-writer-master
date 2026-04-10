"""小说项目 + 章节 + 场景 ORM 模型."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from novel_writer.db import Base


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


class Novel(Base):
    """一部小说 = 一个项目."""

    __tablename__ = "novels"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    genre: Mapped[str] = mapped_column(String(50), default="")  # 玄幻/都市/科幻...
    target_words: Mapped[int] = mapped_column(Integer, default=100000)
    style_reference: Mapped[str] = mapped_column(String(200), default="")  # 参考作家/风格
    synopsis: Mapped[str] = mapped_column(Text, default="")  # 全书简介
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/writing/completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    characters: Mapped[list[Character]] = relationship(back_populates="novel", cascade="all, delete-orphan")
    outlines: Mapped[list[Outline]] = relationship(back_populates="novel", cascade="all, delete-orphan")
    chapters: Mapped[list[Chapter]] = relationship(back_populates="novel", cascade="all, delete-orphan")


class Character(Base):
    """角色档案."""

    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    novel_id: Mapped[str] = mapped_column(ForeignKey("novels.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    aliases: Mapped[dict] = mapped_column(JSON, default=list)  # ["小明", "阿明"]
    role: Mapped[str] = mapped_column(String(20), default="supporting")  # protagonist/antagonist/supporting/minor
    profile: Mapped[dict] = mapped_column(JSON, default=dict)  # {age, gender, appearance, personality, background}
    speech_style: Mapped[dict] = mapped_column(JSON, default=dict)  # 口癖系统
    # speech_style 结构: {
    #   "patterns": ["常用句式"],
    #   "vocab_level": "文雅/粗犷/中性",
    #   "dialect": "普通话/四川话/...",
    #   "catchphrases": ["口头禅"],
    #   "forbidden_words": ["此角色不会说的词"],
    #   "tone": "正式/随意/傲慢/温柔/..."
    # }
    arc_stages: Mapped[dict] = mapped_column(JSON, default=list)  # 角色弧线阶段
    current_state: Mapped[dict] = mapped_column(JSON, default=dict)  # {location, mood, knowledge_scope}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    novel: Mapped[Novel] = relationship(back_populates="characters")


class Outline(Base):
    """分层大纲节点（全书→卷→章→场景）."""

    __tablename__ = "outlines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    novel_id: Mapped[str] = mapped_column(ForeignKey("novels.id"), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("outlines.id"), nullable=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # synopsis/volume/chapter/scene
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(200), default="")
    narrative_goal: Mapped[str] = mapped_column(Text, default="")  # 叙事目标
    emotion_target: Mapped[str] = mapped_column(String(50), default="")  # 目标情绪
    checkpoints: Mapped[dict] = mapped_column(JSON, default=list)  # [{description, is_mandatory, verified}]
    content_preview: Mapped[str] = mapped_column(Text, default="")  # 大纲正文
    status: Mapped[str] = mapped_column(String(20), default="draft")

    novel: Mapped[Novel] = relationship(back_populates="outlines")
    children: Mapped[list[Outline]] = relationship(back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped[Outline | None] = relationship(back_populates="children", remote_side=[id])


class Chapter(Base):
    """章节."""

    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    novel_id: Mapped[str] = mapped_column(ForeignKey("novels.id"), nullable=False)
    outline_id: Mapped[str | None] = mapped_column(ForeignKey("outlines.id"), nullable=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default="outline_only")  # outline_only/draft/revised/finalized
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    novel: Mapped[Novel] = relationship(back_populates="chapters")
    scenes: Mapped[list[Scene]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
    summary: Mapped[ChapterSummary | None] = relationship(back_populates="chapter", uselist=False, cascade="all, delete-orphan")


class Scene(Base):
    """场景（正文最小单元）."""

    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    outline_id: Mapped[str | None] = mapped_column(ForeignKey("outlines.id"), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    pov_character_id: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 视角角色
    characters_present: Mapped[dict] = mapped_column(JSON, default=list)  # [character_id, ...]
    emotion_actual: Mapped[str] = mapped_column(String(50), default="")
    ai_risk_score: Mapped[float] = mapped_column(default=0.0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    chapter: Mapped[Chapter] = relationship(back_populates="scenes")


class ChapterSummary(Base):
    """章节摘要（跨章记忆用）."""

    __tablename__ = "chapter_summaries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id"), nullable=False, unique=True)
    summary_level: Mapped[str] = mapped_column(String(20), default="detailed")  # detailed/compressed/one_line
    content: Mapped[str] = mapped_column(Text, default="")
    key_events: Mapped[dict] = mapped_column(JSON, default=list)
    key_characters: Mapped[dict] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    chapter: Mapped[Chapter] = relationship(back_populates="summary")


class WorldSetting(Base):
    """世界观设定."""

    __tablename__ = "world_settings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    novel_id: Mapped[str] = mapped_column(ForeignKey("novels.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # geography/politics/magic_system/...
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    is_hard_rule: Mapped[bool] = mapped_column(default=False)  # 不可违反的硬规则


class Foreshadowing(Base):
    """伏笔条目."""

    __tablename__ = "foreshadowings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    novel_id: Mapped[str] = mapped_column(ForeignKey("novels.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    plant_chapter: Mapped[int] = mapped_column(Integer, default=0)
    target_chapter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planted")  # planted/partially_resolved/resolved/expired
    resolution_text: Mapped[str] = mapped_column(Text, default="")
