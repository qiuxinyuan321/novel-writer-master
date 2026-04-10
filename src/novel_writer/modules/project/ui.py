"""项目管理 Streamlit UI."""

from __future__ import annotations

import streamlit as st

from novel_writer.modules.project.service import (
    create_novel,
    delete_novel,
    list_novels,
)

GENRES = ["玄幻", "仙侠", "都市", "科幻", "言情", "悬疑", "历史", "军事", "游戏", "其他"]


def render_projects_page() -> None:
    st.header("📚 项目管理")

    # 创建新项目
    with st.expander("➕ 创建新项目", expanded=not bool(st.session_state.get("novels"))):
        with st.form("create_novel"):
            title = st.text_input("书名", placeholder="请输入小说名称")
            col1, col2 = st.columns(2)
            with col1:
                genre = st.selectbox("类型", GENRES)
            with col2:
                target_words = st.number_input("目标字数", min_value=10000, max_value=5000000,
                                                value=100000, step=10000)
            style_ref = st.text_input("风格参考", placeholder="如：鲁迅、金庸、刘慈欣...")
            synopsis = st.text_area("简介/梗概", height=100, placeholder="一句话概括你的故事...")
            submitted = st.form_submit_button("创建项目", type="primary")

            if submitted and title.strip():
                novel = create_novel(
                    title=title.strip(),
                    genre=genre,
                    target_words=target_words,
                    style_reference=style_ref.strip(),
                    synopsis=synopsis.strip(),
                )
                st.success(f"已创建项目: {novel.title}")
                st.rerun()

    st.divider()

    # 项目列表
    novels = list_novels()
    if not novels:
        st.info("还没有项目，点击上方创建你的第一部小说！")
        return

    st.subheader(f"我的小说 ({len(novels)})")

    for novel in novels:
        with st.container(border=True):
            col_info, col_action = st.columns([4, 1])
            with col_info:
                st.markdown(f"### {novel.title}")
                tags = []
                if novel.genre:
                    tags.append(f"`{novel.genre}`")
                tags.append(f"目标 {novel.target_words // 10000} 万字")
                tags.append(f"状态: {novel.status}")
                if novel.style_reference:
                    tags.append(f"风格: {novel.style_reference}")
                st.caption(" · ".join(tags))
                if novel.synopsis:
                    st.text(novel.synopsis[:100] + ("..." if len(novel.synopsis) > 100 else ""))

            with col_action:
                if st.button("打开", key=f"open_{novel.id}", use_container_width=True):
                    st.session_state.current_novel_id = novel.id
                    st.session_state.current_novel_title = novel.title
                    st.toast(f"已打开: {novel.title}")
                if st.button("删除", key=f"del_{novel.id}", type="secondary", use_container_width=True):
                    delete_novel(novel.id)
                    st.rerun()

    # 当前选中项目提示
    if "current_novel_id" in st.session_state:
        st.sidebar.success(f"当前项目: {st.session_state.get('current_novel_title', '')}")
