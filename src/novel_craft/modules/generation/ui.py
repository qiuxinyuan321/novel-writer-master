"""写作台 Streamlit UI - 场景生成 + 编辑 + 管理."""

from __future__ import annotations

import asyncio

import streamlit as st

from novel_craft.db import get_session
from novel_craft.models import Chapter, Scene
from novel_craft.modules.anti_slop.scorer import score_document
from novel_craft.modules.bible.service import list_characters
from novel_craft.modules.outline.service import list_outlines


def _get_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def _get_novel_id() -> str | None:
    return st.session_state.get("current_novel_id")


def render_write_page() -> None:
    novel_id = _get_novel_id()
    if not novel_id:
        st.warning("请先在「项目管理」中打开一个小说项目")
        return

    st.header(f"✍️ 写作台 - {st.session_state.get('current_novel_title', '')}")

    tab_gen, tab_chapters = st.tabs(["🎬 生成场景", "📄 章节管理"])

    with tab_gen:
        _render_generate(novel_id)
    with tab_chapters:
        _render_chapters(novel_id)


def _render_generate(novel_id: str) -> None:
    """场景生成面板."""
    st.subheader("生成新场景")

    # 选择章节
    with get_session() as session:
        chapters = list(
            session.query(Chapter)
            .filter_by(novel_id=novel_id)
            .order_by(Chapter.number)
            .all()
        )

    if not chapters:
        st.info("还没有章节。请先在「大纲」中添加章级大纲，系统会自动创建章节。")
        return

    chapter_options = {ch.id: f"第{ch.number}章: {ch.title} ({ch.word_count}字)" for ch in chapters}
    selected_chapter_id = st.selectbox(
        "选择章节",
        list(chapter_options.keys()),
        format_func=lambda x: chapter_options[x],
    )

    # 选择场景大纲（可选）
    scene_outlines = list_outlines(novel_id, parent_id=None)
    # 过滤出属于该章节的场景大纲
    chapter_obj = next((ch for ch in chapters if ch.id == selected_chapter_id), None)
    outline_id = None
    if chapter_obj and chapter_obj.outline_id:
        scene_outlines = list_outlines(novel_id, parent_id=chapter_obj.outline_id)
        if scene_outlines:
            outline_options = {"": "不使用场景大纲"}
            outline_options.update({o.id: f"🎬 {o.title}" for o in scene_outlines})
            outline_id = st.selectbox(
                "场景大纲（可选）",
                list(outline_options.keys()),
                format_func=lambda x: outline_options[x],
            )
            if outline_id == "":
                outline_id = None

    # 选择出场角色
    all_chars = list_characters(novel_id)
    if all_chars:
        char_options = {c.id: f"{c.name} ({c.role})" for c in all_chars}
        selected_chars = st.multiselect(
            "出场角色",
            list(char_options.keys()),
            format_func=lambda x: char_options[x],
            default=[c.id for c in all_chars if c.role in ("protagonist", "antagonist")],
        )
    else:
        selected_chars = []

    # 目标字数
    target_words = st.slider("目标字数", 500, 5000, 1500, 100)

    # 生成按钮
    if st.button("🚀 生成场景", type="primary", use_container_width=True):
        from novel_craft.modules.generation.service import generate_scene

        loop = _get_event_loop()
        with st.spinner("正在生成中... 请稍候"):
            try:
                scene = loop.run_until_complete(
                    generate_scene(
                        novel_id=novel_id,
                        chapter_id=selected_chapter_id,
                        outline_id=outline_id or None,
                        character_ids=selected_chars or None,
                        target_words=target_words,
                    )
                )
                st.session_state.last_generated_scene = scene
                st.success(f"生成完成！{scene.word_count} 字，AI风险: {scene.ai_risk_score:.0%}")
            except Exception as e:
                st.error(f"生成失败: {e}")
                return

    # 显示生成结果
    if "last_generated_scene" in st.session_state:
        scene = st.session_state.last_generated_scene
        st.divider()
        st.subheader("生成结果")

        # AI 风险
        risk_color = "🔴" if scene.ai_risk_score > 0.6 else ("🟡" if scene.ai_risk_score > 0.3 else "🟢")
        st.info(f"{risk_color} AI 风险评分: {scene.ai_risk_score:.0%}")

        # 正文
        st.text_area("正文（可编辑后复制）", scene.content, height=400, key="gen_result")

        # 快速检测
        if st.button("🔬 详细分析 AI 痕迹"):
            doc_score = score_document(scene.content)
            for seg in doc_score.segments:
                if seg.risk_factors:
                    with st.expander(f"段落 {seg.index+1}: {seg.risk_score:.0%}"):
                        for f in seg.risk_factors:
                            st.markdown(f"- {f}")


def _render_chapters(novel_id: str) -> None:
    """章节管理和浏览."""
    with get_session() as session:
        chapters = list(
            session.query(Chapter)
            .filter_by(novel_id=novel_id)
            .order_by(Chapter.number)
            .all()
        )

    if not chapters:
        st.info("还没有章节")
        return

    st.subheader(f"共 {len(chapters)} 章")

    for ch in chapters:
        with st.expander(f"第{ch.number}章: {ch.title} ({ch.word_count}字) [{ch.status}]"):
            # 获取场景
            with get_session() as session:
                scenes = list(
                    session.query(Scene)
                    .filter_by(chapter_id=ch.id)
                    .order_by(Scene.order_index)
                    .all()
                )

            if not scenes:
                st.caption("暂无正文")
                continue

            for i, scene in enumerate(scenes):
                risk_icon = "🔴" if scene.ai_risk_score > 0.6 else ("🟡" if scene.ai_risk_score > 0.3 else "🟢")
                st.markdown(f"**场景 {i+1}** {risk_icon} {scene.word_count}字 | AI风险 {scene.ai_risk_score:.0%}")
                st.text_area(
                    f"内容",
                    scene.content,
                    height=200,
                    key=f"scene_{scene.id}",
                    disabled=True,
                )

            # 摘要
            with get_session() as session:
                ch_obj = session.query(Chapter).filter_by(id=ch.id).first()
                if ch_obj and ch_obj.summary:
                    st.markdown("**📝 章节摘要:**")
                    st.caption(ch_obj.summary.content[:300])
                else:
                    if st.button(f"生成摘要", key=f"summary_{ch.id}"):
                        from novel_craft.modules.generation.service import generate_chapter_summary
                        loop = _get_event_loop()
                        with st.spinner("生成摘要中..."):
                            try:
                                loop.run_until_complete(generate_chapter_summary(ch.id))
                                st.success("摘要已生成")
                                st.rerun()
                            except Exception as e:
                                st.error(f"失败: {e}")
