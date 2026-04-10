"""仪表盘 Streamlit UI - 进度 + 情绪节奏图 + AI 风险分布."""

from __future__ import annotations

import streamlit as st

from novel_craft.modules.export.service import get_novel_stats

# 情绪→数值映射（用于折线图）
EMOTION_VALUES = {
    "紧张": 7, "高潮": 9, "热血": 8, "恐怖": 6,
    "悬疑": 5, "平淡": 3, "舒缓": 2, "温馨": 4,
    "喜悦": 6, "搞笑": 5, "悲伤": 4,
}


def render_dashboard_page() -> None:
    novel_id = st.session_state.get("current_novel_id")
    if not novel_id:
        st.warning("请先在「项目管理」中打开一个小说项目")
        return

    stats = get_novel_stats(novel_id)
    if not stats:
        st.warning("项目不存在")
        return

    st.header(f"📊 仪表盘 - 《{stats['title']}》")

    # 总览指标
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总字数", f"{stats['total_words']:,}")
    col2.metric("目标字数", f"{stats['target_words']:,}")
    col3.metric("完成进度", f"{stats['progress']:.0%}")
    col4.metric("已有章节", stats["total_chapters"])

    # 进度条
    st.progress(min(1.0, stats["progress"]))

    if not stats["chapters"]:
        st.info("还没有章节数据")
        return

    st.divider()

    # 三列图表
    col_left, col_right = st.columns(2)

    with col_left:
        _render_word_count_chart(stats)

    with col_right:
        _render_emotion_chart(stats)

    st.divider()
    _render_risk_chart(stats)

    # 章节明细表
    st.divider()
    _render_chapter_table(stats)


def _render_word_count_chart(stats: dict) -> None:
    """各章字数柱状图."""
    st.subheader("📏 各章字数")
    import pandas as pd

    chapters = stats["chapters"]
    df = pd.DataFrame({
        "章节": [f"第{ch['number']}章" for ch in chapters],
        "字数": [ch["word_count"] for ch in chapters],
    })
    st.bar_chart(df.set_index("章节"))


def _render_emotion_chart(stats: dict) -> None:
    """情绪节奏折线图."""
    st.subheader("🎭 情绪节奏图")
    import pandas as pd

    chapters = stats["chapters"]
    emotions = [ch.get("emotion", "") for ch in chapters]

    if not any(emotions):
        st.caption("暂无情绪数据（在大纲中设定目标情绪）")
        return

    df = pd.DataFrame({
        "章节": [f"第{ch['number']}章" for ch in chapters],
        "情绪强度": [EMOTION_VALUES.get(ch.get("emotion", ""), 3) for ch in chapters],
    })
    st.line_chart(df.set_index("章节"))

    # 情绪标签
    emotion_tags = " → ".join(
        f"`{ch.get('emotion', '未设定')}`" for ch in chapters
    )
    st.caption(f"节奏: {emotion_tags}")


def _render_risk_chart(stats: dict) -> None:
    """AI 风险分布."""
    st.subheader("🛡️ AI 风险分布")
    import pandas as pd

    chapters = stats["chapters"]
    chapters_with_content = [ch for ch in chapters if ch["word_count"] > 0]

    if not chapters_with_content:
        st.caption("暂无数据")
        return

    df = pd.DataFrame({
        "章节": [f"第{ch['number']}章" for ch in chapters_with_content],
        "AI风险": [ch["avg_ai_risk"] for ch in chapters_with_content],
    })
    st.bar_chart(df.set_index("章节"))

    # 统计
    risks = [ch["avg_ai_risk"] for ch in chapters_with_content]
    avg_risk = sum(risks) / len(risks) if risks else 0
    level = "🟢 低" if avg_risk < 0.3 else ("🟡 中" if avg_risk < 0.6 else "🔴 高")
    st.caption(f"平均 AI 风险: {avg_risk:.0%} ({level})")


def _render_chapter_table(stats: dict) -> None:
    """章节明细表格."""
    st.subheader("📋 章节明细")
    import pandas as pd

    chapters = stats["chapters"]
    df = pd.DataFrame([
        {
            "章节": f"第{ch['number']}章",
            "标题": ch["title"],
            "字数": ch["word_count"],
            "场景数": ch["scene_count"],
            "AI风险": f"{ch['avg_ai_risk']:.0%}",
            "情绪": ch.get("emotion", "-"),
            "状态": ch["status"],
        }
        for ch in chapters
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
