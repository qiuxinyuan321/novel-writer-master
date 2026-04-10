"""设置 Streamlit UI - LLM Provider 配置 + 系统信息."""

from __future__ import annotations

import asyncio

import streamlit as st

from novel_craft.config import get_config
from novel_craft.core.module import registry
from novel_craft.llm.router import get_router


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


def render_settings_page() -> None:
    st.header("⚙️ 设置")

    tab_llm, tab_modules, tab_antislop, tab_about = st.tabs(
        ["🤖 LLM 配置", "🧩 模块管理", "🔍 Anti-Slop 配置", "ℹ️ 关于"]
    )

    with tab_llm:
        _render_llm_settings()
    with tab_modules:
        _render_module_info()
    with tab_antislop:
        _render_antislop_settings()
    with tab_about:
        _render_about()


def _render_llm_settings() -> None:
    """LLM Provider 配置."""
    config = get_config()
    router = get_router()

    st.subheader("当前配置")
    st.info(f"默认 Provider: **{config.llm.default_provider}**")

    # Provider 列表
    for name, provider_cfg in config.llm.providers.items():
        if not provider_cfg.base_url:
            continue
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                available = router.has_provider(name)
                status = "🟢" if available else "🔴"
                st.markdown(f"### {status} {name}")
            with col2:
                st.text(f"模型: {provider_cfg.model}")
                st.caption(f"URL: {provider_cfg.base_url}")
                st.caption(f"Max tokens: {provider_cfg.max_tokens}")
            with col3:
                if st.button("测试连接", key=f"test_{name}"):
                    if available:
                        client = router.get_client()
                        # 寻找匹配的 client
                        for pname in router.available_providers:
                            if pname == name:
                                from novel_craft.llm.client import LLMClient
                                test_client = LLMClient(provider_cfg, provider_name=name)
                                loop = _get_event_loop()
                                with st.spinner("测试中..."):
                                    ok, msg = loop.run_until_complete(test_client.test_connection())
                                if ok:
                                    st.success(msg)
                                else:
                                    st.error(msg)
                                break

    # 模型路由
    st.subheader("模型路由")
    st.caption("不同任务使用不同 Provider（在 config.yaml 中配置）")

    routing = config.llm.routing
    if routing:
        for task, provider in routing.items():
            st.text(f"  {task} → {provider}")
    else:
        st.text("  所有任务使用默认 Provider")

    st.divider()
    st.markdown("""
    **配置方法:** 编辑项目根目录的 `config.yaml`

    ```yaml
    llm:
      default_provider: "claude"
      providers:
        claude:
          base_url: "https://api.anthropic.com"
          api_key: "sk-xxx"
          model: "claude-sonnet-4-20250514"
          max_tokens: 8192
    ```

    支持任何兼容 OpenAI Chat Completions API 的服务。
    """)


def _render_module_info() -> None:
    """已加载模块信息."""
    modules = registry.list_modules()

    st.subheader(f"已加载 {len(modules)} 个模块")

    for m in modules:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{m.name}** v{m.version}")
                if m.description:
                    st.caption(m.description)
                if m.dependencies:
                    st.caption(f"依赖: {', '.join(m.dependencies)}")
            with col2:
                pages = m.get_pages()
                if pages:
                    st.text(f"📄 {len(pages)} 个页面")

    st.divider()
    st.markdown("""
    **添加新模块:** 在 `modules/` 下创建目录，实现 `Module` 接口，
    然后在 `config.yaml` 的 `modules.enabled` 中添加模块名。
    """)


def _render_antislop_settings() -> None:
    """Anti-Slop 配置."""
    config = get_config()

    st.subheader("评分指标权重")
    for key, weight in config.anti_slop.weights.items():
        labels = {
            "blacklist_density": "黑名单命中密度",
            "ttr": "词汇多样性 (TTR)",
            "sentence_variance": "句长变异系数",
            "structure_pattern": "结构模式匹配",
            "repetition": "句式重复度",
        }
        st.text(f"  {labels.get(key, key)}: {weight:.0%}")

    st.subheader("风险阈值")
    thresholds = config.anti_slop.thresholds
    st.text(f"  低风险: < {thresholds.get('low', 0.3):.0%}")
    st.text(f"  中风险: {thresholds.get('low', 0.3):.0%} - {thresholds.get('high', 0.6):.0%}")
    st.text(f"  高风险: > {thresholds.get('high', 0.6):.0%}")

    st.text(f"  改写最大轮次: {config.anti_slop.max_rewrite_rounds}")

    st.divider()
    st.caption("在 config.yaml 的 anti_slop 部分调整以上参数")


def _render_about() -> None:
    """关于页面."""
    from novel_craft import __version__
    st.subheader("NovelCraft")
    st.text(f"版本: {__version__}")
    st.markdown("""
    AI 辅助小说写作工具，内置降 AI 率引擎。

    **核心特性:**
    - 🔍 Anti-Slop 引擎: 检测并降低 AI 生成痕迹
    - 📖 Story Bible: 角色口癖/世界观/伏笔管理
    - 🗂️ 分层大纲: 检查点约束确保不跑偏
    - 🤖 多 LLM 支持: Claude/OpenAI/DeepSeek/Ollama

    **开源地址:** GitHub (Coming Soon)
    """)
