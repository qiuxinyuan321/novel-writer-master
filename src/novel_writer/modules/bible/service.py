"""Story Bible Service - 角色/世界观/伏笔 CRUD."""

from __future__ import annotations

from novel_writer.db import get_session
from novel_writer.models import Character, Foreshadowing, WorldSetting


# === 角色管理 ===

def list_characters(novel_id: str) -> list[Character]:
    session = get_session()
    result = list(session.query(Character).filter_by(novel_id=novel_id).all())
    session.close()
    return result


def get_character(char_id: str) -> Character | None:
    session = get_session()
    result = session.query(Character).filter_by(id=char_id).first()
    session.close()
    return result


def create_character(novel_id: str, name: str, role: str = "supporting",
                     profile: dict | None = None, speech_style: dict | None = None) -> Character:
    session = get_session()
    char = Character(
        novel_id=novel_id,
        name=name,
        role=role,
        profile=profile or {},
        speech_style=speech_style or {
            "patterns": [],
            "vocab_level": "中性",
            "dialect": "普通话",
            "catchphrases": [],
            "forbidden_words": [],
            "tone": "中性",
        },
    )
    session.add(char)
    session.commit()
    session.refresh(char)
    session.close()
    return char


def update_character(char_id: str, **kwargs) -> Character | None:
    session = get_session()
    char = session.query(Character).filter_by(id=char_id).first()
    if not char:
        session.close()
        return None
    for key, value in kwargs.items():
        if hasattr(char, key):
            setattr(char, key, value)
    session.commit()
    session.refresh(char)
    session.close()
    return char


def delete_character(char_id: str) -> bool:
    session = get_session()
    char = session.query(Character).filter_by(id=char_id).first()
    if not char:
        session.close()
        return False
    session.delete(char)
    session.commit()
    session.close()
    return True


# === 世界观管理 ===

def list_world_settings(novel_id: str) -> list[WorldSetting]:
    session = get_session()
    result = list(session.query(WorldSetting).filter_by(novel_id=novel_id).all())
    session.close()
    return result


def create_world_setting(novel_id: str, category: str, key: str,
                         content: str, is_hard_rule: bool = False) -> WorldSetting:
    session = get_session()
    ws = WorldSetting(novel_id=novel_id, category=category, key=key,
                      content=content, is_hard_rule=is_hard_rule)
    session.add(ws)
    session.commit()
    session.refresh(ws)
    session.close()
    return ws


def delete_world_setting(ws_id: str) -> bool:
    session = get_session()
    ws = session.query(WorldSetting).filter_by(id=ws_id).first()
    if not ws:
        session.close()
        return False
    session.delete(ws)
    session.commit()
    session.close()
    return True


# === 伏笔管理 ===

def list_foreshadowings(novel_id: str) -> list[Foreshadowing]:
    session = get_session()
    result = list(session.query(Foreshadowing).filter_by(novel_id=novel_id).all())
    session.close()
    return result


def create_foreshadowing(novel_id: str, content: str, plant_chapter: int,
                         target_chapter: int | None = None) -> Foreshadowing:
    session = get_session()
    fs = Foreshadowing(novel_id=novel_id, content=content,
                       plant_chapter=plant_chapter, target_chapter=target_chapter)
    session.add(fs)
    session.commit()
    session.refresh(fs)
    session.close()
    return fs


def update_foreshadowing(fs_id: str, **kwargs) -> Foreshadowing | None:
    session = get_session()
    fs = session.query(Foreshadowing).filter_by(id=fs_id).first()
    if not fs:
        session.close()
        return None
    for key, value in kwargs.items():
        if hasattr(fs, key):
            setattr(fs, key, value)
    session.commit()
    session.refresh(fs)
    session.close()
    return fs
