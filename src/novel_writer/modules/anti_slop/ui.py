"""Anti-Slop 检测面板 - Streamlit UI.

核心交互流程：粘贴文本 → 分析 → 可视化风险热力图 → 一键改写高风险段落。
"""

from __future__ import annotations

import asyncio

import streamlit as st

from novel_writer.modules.anti_slop.dictionary import get_dictionary
from novel_writer.modules.anti_slop.scorer import DocumentScore, score_document


def _get_event_loop():
    """获取或创建事件循环."""
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


def _risk_color(level: str) -> str:
    """风险等级对应的颜色."""
    return {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(level, "⚪")


def _risk_label(level: str) -> str:
    return {"low": "低风险", "medium": "中风险", "high": "高风险"}.get(level, "未知")


def render_detection_page() -> None:
    """渲染 AI 检测面板页面."""
    st.header("🔍 AI 检测分析")
    st.caption("粘贴文本 → 逐段分析 AI 痕迹 → 定向改写高风险段落")

    # 词库信息
    dictionary = get_dictionary()
    with st.expander(f"📚 词库信息 ({dictionary.total} 词条)", expanded=False):
        col1, col2, col3 = st.columns(3)
        banned = dictionary.by_severity("ban")
        warned = dictionary.by_severity("warn")
        limited = dictionary.by_severity("limit")
        col1.metric("禁用词", len(banned))
        col2.metric("警告词", len(warned))
        col3.metric("限制词", len(limited))

    # 文本输入
    text = st.text_area(
        "输入待检测的文本",
        height=300,
        placeholder="在此粘贴小说正文...\n\n支持多段落，系统会逐段分析 AI 痕迹。",
        key="detection_input",
    )

    col_analyze, col_rewrite = st.columns([1, 1])

    with col_analyze:
        analyze_btn = st.button("🔬 分析 AI 痕迹", type="primary", use_container_width=True)

    with col_rewrite:
        rewrite_btn = st.button(
            "✏️ 改写高风险段落",
            use_container_width=True,
            disabled="doc_score" not in st.session_state,
        )

    # 分析逻辑
    if analyze_btn and text.strip():
        with st.spinner("正在分析..."):
            doc_score = score_document(text.strip())
            st.session_state.doc_score = doc_score

    # 改写逻辑
    if rewrite_btn and "doc_score" in st.session_state:
        _handle_rewrite()
        return

    # 显示结果
    if "doc_score" in st.session_state:
        _render_results(st.session_state.doc_score)


def _render_results(doc_score: DocumentScore) -> None:
    """渲染分析结果."""
    st.divider()

    # 总览
    st.subheader("📊 总览")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "整体 AI 风险",
        f"{doc_score.overall_score:.0%}",
        help="0% = 纯人写，100% = 纯 AI",
    )
    col2.metric("🔴 高风险段", doc_score.high_risk_count)
    col3.metric("🟡 中风险段", doc_score.medium_risk_count)
    col4.metric("🟢 低风险段", doc_score.low_risk_count)

    # 整体评级
    level_emoji = _risk_color(doc_score.overall_level)
    level_text = _risk_label(doc_score.overall_level)
    st.info(f"{level_emoji} 整体评级: **{level_text}** ({doc_score.overall_score:.1%})")

    # 风险分布条
    if doc_score.segments:
        st.subheader("🌡️ 段落风险热力图")
        cols = st.columns(len(doc_score.segments))
        for i, (col, seg) in enumerate(zip(cols, doc_score.segments)):
            with col:
                color = _risk_color(seg.risk_level)
                st.markdown(
                    f"<div style='text-align:center'>{color}<br>"
                    f"<small>P{i+1}</small><br>"
                    f"<small>{seg.risk_score:.0%}</small></div>",
                    unsafe_allow_html=True,
                )

    # 逐段详情
    st.subheader("📝 逐段分析")
    for seg in doc_score.segments:
        emoji = _risk_color(seg.risk_level)
        label = _risk_label(seg.risk_level)
        with st.expander(
            f"{emoji} 段落 {seg.index + 1} - {label} ({seg.risk_score:.0%}) "
            f"| {seg.metrics.char_count}字",
            expanded=seg.risk_level == "high",
        ):
            # 原文
            st.text_area(
                "原文",
                seg.text,
                height=100,
                disabled=True,
                key=f"seg_text_{seg.index}",
            )

            # 指标明细
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("词汇多样性", f"{seg.metrics.ttr:.2f}", help="TTR，越高越好")
            c2.metric("句长变异", f"{seg.metrics.sentence_len_cv:.2f}", help="变异系数，越高越好")
            c3.metric("黑名单密度", f"{seg.metrics.blacklist_density:.3f}", help="越低越好")
            c4.metric("结构模式", len(seg.metrics.structure_patterns), help="命中AI模板数")
            c5.metric("句式重复", f"{seg.metrics.repetition_score:.2f}", help="越低越好")

            # 风险因素
            if seg.risk_factors:
                st.warning("**风险因素:**")
                for factor in seg.risk_factors:
                    st.markdown(f"- {factor}")

            # 命中的黑名单词
            if seg.metrics.blacklist_hits:
                hits = sorted(seg.metrics.blacklist_hits.items(), key=lambda x: -x[1])
                hit_tags = " ".join(f"`{w}` ×{c}" for w, c in hits[:15])
                st.caption(f"命中词: {hit_tags}")


def _handle_rewrite() -> None:
    """处理改写请求."""
    doc_score: DocumentScore = st.session_state.doc_score

    high_risk = [s for s in doc_score.segments if s.risk_level in ("high", "medium")]
    if not high_risk:
        st.success("没有需要改写的段落！所有段落均为低风险。")
        return

    st.info(f"正在改写 {len(high_risk)} 个中/高风险段落...")

    from novel_writer.modules.anti_slop.rewriter import rewrite_segment

    loop = _get_event_loop()

    results = []
    progress = st.progress(0)
    for i, seg in enumerate(high_risk):
        with st.spinner(f"改写段落 {seg.index + 1}..."):
            try:
                result = loop.run_until_complete(rewrite_segment(seg))
                results.append((seg.index, result))
            except Exception as e:
                st.error(f"段落 {seg.index + 1} 改写失败: {e}")
                results.append((seg.index, None))
        progress.progress((i + 1) / len(high_risk))

    # 显示改写结果
    st.divider()
    st.subheader("✏️ 改写结果")

    full_text_parts = []
    seg_map = {seg.index: seg for seg in doc_score.segments}

    for seg in doc_score.segments:
        # 查找是否有改写结果
        rewrite_result = None
        for idx, r in results:
            if idx == seg.index and r is not None:
                rewrite_result = r
                break

        if rewrite_result and rewrite_result.improved:
            with st.expander(
                f"✅ 段落 {seg.index + 1}: "
                f"{rewrite_result.original_score:.0%} → {rewrite_result.new_score:.0%}",
                expanded=True,
            ):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption("原文")
                    st.text_area(
                        "原文", rewrite_result.original, height=120,
                        disabled=True, key=f"rw_orig_{seg.index}"
                    )
                with col_b:
                    st.caption("改写后")
                    st.text_area(
                        "改写后", rewrite_result.rewritten, height=120,
                        disabled=True, key=f"rw_new_{seg.index}"
                    )
            full_text_parts.append(rewrite_result.rewritten)
        else:
            full_text_parts.append(seg.text)

    # 合并完整文本
    st.divider()
    st.subheader("📄 完整改写文本")
    final_text = "\n\n".join(full_text_parts)
    st.text_area("改写后全文（可复制）", final_text, height=300, key="final_output")

    # 重新评分
    new_doc_score = score_document(final_text)
    improvement = doc_score.overall_score - new_doc_score.overall_score

    col1, col2, col3 = st.columns(3)
    col1.metric("改写前", f"{doc_score.overall_score:.0%}")
    col2.metric("改写后", f"{new_doc_score.overall_score:.0%}")
    col3.metric("改善", f"{improvement:.0%}", delta=f"-{improvement:.0%}")
