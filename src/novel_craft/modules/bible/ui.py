"""Story Bible Streamlit UI - 角色/世界观/伏笔管理."""

from __future__ import annotations

import streamlit as st

from novel_craft.modules.bible.service import (
    create_character,
    create_foreshadowing,
    create_world_setting,
    delete_character,
    delete_world_setting,
    list_characters,
    list_foreshadowings,
    list_world_settings,
    update_character,
    update_foreshadowing,
)

ROLES = {"protagonist": "主角", "antagonist": "反派", "supporting": "配角", "minor": "龙套"}
TONES = ["中性", "正式", "随意", "傲慢", "温柔", "粗犷", "阴沉", "活泼", "冷漠"]
WORLD_CATEGORIES = ["地理", "政治", "魔法体系", "科技", "社会", "历史", "文化", "经济", "其他"]


def _get_novel_id() -> str | None:
    return st.session_state.get("current_novel_id")


def render_bible_page() -> None:
    novel_id = _get_novel_id()
    if not novel_id:
        st.warning("请先在「项目管理」中打开一个小说项目")
        return

    st.header(f"📖 Story Bible - {st.session_state.get('current_novel_title', '')}")

    tab_char, tab_world, tab_foreshadow = st.tabs(["👤 角色", "🌍 世界观", "🔮 伏笔"])

    with tab_char:
        _render_characters(novel_id)
    with tab_world:
        _render_world_settings(novel_id)
    with tab_foreshadow:
        _render_foreshadowings(novel_id)


def _render_characters(novel_id: str) -> None:
    """角色管理."""
    # 创建角色
    with st.expander("➕ 添加角色"):
        with st.form("add_char"):
            name = st.text_input("姓名")
            col1, col2 = st.columns(2)
            with col1:
                role = st.selectbox("角色定位", list(ROLES.keys()),
                                    format_func=lambda x: ROLES[x])
            with col2:
                tone = st.selectbox("语气基调", TONES)

            col3, col4 = st.columns(2)
            with col3:
                age = st.text_input("年龄", placeholder="如：25岁")
                personality = st.text_input("性格", placeholder="如：沉稳内敛、外冷内热")
            with col4:
                gender = st.text_input("性别")
                dialect = st.text_input("方言", value="普通话")

            appearance = st.text_area("外貌描写", height=60, placeholder="简要外貌特征...")
            background = st.text_area("背景故事", height=60, placeholder="人物背景...")
            catchphrases = st.text_input("口头禅（逗号分隔）", placeholder="如：有意思, 不过如此")
            forbidden = st.text_input("禁用词（此角色不会说的词，逗号分隔）")

            if st.form_submit_button("添加", type="primary") and name.strip():
                profile = {
                    "age": age, "gender": gender,
                    "appearance": appearance, "personality": personality,
                    "background": background,
                }
                speech = {
                    "patterns": [],
                    "vocab_level": "中性",
                    "dialect": dialect or "普通话",
                    "catchphrases": [c.strip() for c in catchphrases.split(",") if c.strip()],
                    "forbidden_words": [w.strip() for w in forbidden.split(",") if w.strip()],
                    "tone": tone,
                }
                create_character(novel_id, name.strip(), role, profile, speech)
                st.success(f"已添加角色: {name}")
                st.rerun()

    # 角色列表
    chars = list_characters(novel_id)
    if not chars:
        st.info("还没有角色，点击上方添加")
        return

    for char in chars:
        role_label = ROLES.get(char.role, char.role)
        with st.expander(f"**{char.name}** ({role_label})", expanded=False):
            # 基础信息
            profile = char.profile or {}
            cols = st.columns(4)
            cols[0].text(f"年龄: {profile.get('age', '-')}")
            cols[1].text(f"性别: {profile.get('gender', '-')}")
            cols[2].text(f"性格: {profile.get('personality', '-')}")

            speech = char.speech_style or {}
            cols[3].text(f"语气: {speech.get('tone', '-')}")

            if profile.get("appearance"):
                st.caption(f"外貌: {profile['appearance']}")
            if profile.get("background"):
                st.caption(f"背景: {profile['background']}")

            # 口癖系统
            st.markdown("**口癖系统:**")
            cp = speech.get("catchphrases", [])
            if cp:
                st.text(f"  口头禅: {', '.join(cp)}")
            fw = speech.get("forbidden_words", [])
            if fw:
                st.text(f"  禁用词: {', '.join(fw)}")
            st.text(f"  方言: {speech.get('dialect', '普通话')}")

            if st.button("删除", key=f"del_char_{char.id}"):
                delete_character(char.id)
                st.rerun()


def _render_world_settings(novel_id: str) -> None:
    """世界观设定."""
    with st.expander("➕ 添加设定"):
        with st.form("add_world"):
            category = st.selectbox("分类", WORLD_CATEGORIES)
            key = st.text_input("设定项", placeholder="如：修炼体系")
            content = st.text_area("内容", height=100)
            is_hard = st.checkbox("硬规则（不可违反）")

            if st.form_submit_button("添加", type="primary") and key.strip():
                create_world_setting(novel_id, category, key.strip(), content.strip(), is_hard)
                st.success(f"已添加: {key}")
                st.rerun()

    settings = list_world_settings(novel_id)
    if not settings:
        st.info("还没有世界观设定")
        return

    for ws in settings:
        icon = "🔒" if ws.is_hard_rule else "📝"
        with st.expander(f"{icon} [{ws.category}] {ws.key}"):
            st.text(ws.content)
            if st.button("删除", key=f"del_ws_{ws.id}"):
                delete_world_setting(ws.id)
                st.rerun()


def _render_foreshadowings(novel_id: str) -> None:
    """伏笔管理."""
    with st.expander("➕ 埋伏笔"):
        with st.form("add_fs"):
            content = st.text_area("伏笔内容", placeholder="描述这个伏笔...")
            col1, col2 = st.columns(2)
            with col1:
                plant = st.number_input("埋设章节", min_value=1, value=1)
            with col2:
                target = st.number_input("计划回收章节（0=未定）", min_value=0, value=0)

            if st.form_submit_button("埋入", type="primary") and content.strip():
                create_foreshadowing(novel_id, content.strip(), plant,
                                     target if target > 0 else None)
                st.success("伏笔已埋入")
                st.rerun()

    fss = list_foreshadowings(novel_id)
    if not fss:
        st.info("还没有伏笔")
        return

    status_icons = {"planted": "🌱", "partially_resolved": "🌿",
                    "resolved": "✅", "expired": "💀"}
    status_labels = {"planted": "已埋设", "partially_resolved": "部分回收",
                     "resolved": "已回收", "expired": "已过期"}

    for fs in fss:
        icon = status_icons.get(fs.status, "❓")
        label = status_labels.get(fs.status, fs.status)
        target_info = f" → 计划第{fs.target_chapter}章回收" if fs.target_chapter else ""
        with st.expander(f"{icon} 第{fs.plant_chapter}章{target_info} - {label}"):
            st.text(fs.content)
            if fs.status == "planted":
                if st.button("标记已回收", key=f"resolve_{fs.id}"):
                    update_foreshadowing(fs.id, status="resolved")
                    st.rerun()
