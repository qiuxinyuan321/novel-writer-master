"""导出 Streamlit UI."""

from __future__ import annotations

import streamlit as st

from novel_craft.modules.export.service import export_novel_txt


def render_export_page() -> None:
    novel_id = st.session_state.get("current_novel_id")
    if not novel_id:
        st.warning("请先在「项目管理」中打开一个小说项目")
        return

    title = st.session_state.get("current_novel_title", "小说")
    st.header(f"📥 导出 - {title}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 导出为 TXT", type="primary", use_container_width=True):
            try:
                text = export_novel_txt(novel_id)
                st.session_state.export_text = text
                st.success(f"导出成功！共 {len(text)} 字符")
            except Exception as e:
                st.error(f"导出失败: {e}")

    with col2:
        st.button("📝 导出为 DOCX (需安装 python-docx)", disabled=True, use_container_width=True)

    if "export_text" in st.session_state:
        st.divider()
        text = st.session_state.export_text

        # 下载按钮
        st.download_button(
            label="⬇️ 下载 TXT 文件",
            data=text.encode("utf-8"),
            file_name=f"{title}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        # 预览
        with st.expander("预览", expanded=True):
            st.text_area("全文预览", text, height=400, disabled=True)
