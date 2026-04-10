"""一致性检查 Streamlit UI."""

from __future__ import annotations

import asyncio

import streamlit as st

from novel_craft.db import get_session
from novel_craft.models import Chapter


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


def render_consistency_page() -> None:
    novel_id = st.session_state.get("current_novel_id")
    if not novel_id:
        st.warning("请先在「项目管理」中打开一个小说项目")
        return

    st.header("🔎 一致性检查")
    st.caption("LLM 驱动的角色行为/世界观/时间线矛盾检测")

    session = get_session()
    chapters = list(
        session.query(Chapter)
        .filter_by(novel_id=novel_id)
        .order_by(Chapter.number)
        .all()
    )
    session.close()

    if not chapters:
        st.info("还没有章节")
        return

    chapters_with_content = [ch for ch in chapters if ch.word_count > 0]
    if not chapters_with_content:
        st.info("还没有已生成正文的章节")
        return

    ch_options = {ch.id: f"第{ch.number}章: {ch.title} ({ch.word_count}字)" for ch in chapters_with_content}
    selected_id = st.selectbox("选择章节", list(ch_options.keys()),
                                format_func=lambda x: ch_options[x])

    if st.button("🔎 开始检查", type="primary", use_container_width=True):
        from novel_craft.modules.consistency.service import check_chapter_consistency
        loop = _get_event_loop()
        with st.spinner("正在分析一致性... 请稍候"):
            try:
                report = loop.run_until_complete(check_chapter_consistency(selected_id))

                if report.is_clean:
                    st.success("✅ 未发现一致性问题！")
                else:
                    st.warning("发现以下问题：")

                st.markdown(report.raw_response)

            except Exception as e:
                st.error(f"检查失败: {e}")
