# NovelCraft

**AI 辅助小说写作工具，内置降 AI 率引擎。**

专为中文网文/小说创作设计，解决 AI 写作的三大痛点：

- **AI 检测率高** — 内置 Anti-Slop 引擎，332 词条黑名单 + 多维统计分析 + 定向改写，降低朱雀 AI 检测率
- **情节容易跑偏** — 分层大纲 + 检查点约束，强制 AI 遵循叙事规划
- **跨章记忆丢失** — Story Bible（角色口癖/世界观/伏笔）+ 滑动窗口摘要，保持长篇一致性

## 快速开始

### 1. 安装

```bash
git clone https://github.com/your-username/novel-craft.git
cd novel-craft
pip install -e .
```

### 2. 配置 LLM

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，填入你的 LLM API 信息：

```yaml
llm:
  default_provider: "claude"
  providers:
    claude:
      base_url: "https://api.anthropic.com"  # 或你的代理地址
      api_key: "sk-your-key-here"
      model: "claude-sonnet-4-20250514"
      max_tokens: 8192
```

支持任何兼容 OpenAI Chat Completions API 的服务：Claude、OpenAI、DeepSeek、Ollama、自建代理等。

### 3. 启动

```bash
streamlit run src/novel_craft/ui/app.py
```

打开浏览器访问 `http://localhost:8501`

## 功能模块

| 模块 | 说明 |
|------|------|
| 📚 **项目管理** | 多项目支持，每个项目 = 一部小说 |
| 📖 **Story Bible** | 角色档案（含口癖/方言系统）、世界观设定（硬规则标记）、伏笔管理 |
| 🗂️ **分层大纲** | 章→场景树形结构，检查点约束确保 AI 不跑偏 |
| ✍️ **写作台** | AI 场景生成，自动注入大纲+角色+记忆+anti-slop 规则 |
| 🔍 **AI 检测** | 逐段分析 AI 痕迹，可视化风险热力图，一键改写高风险段 |
| 🔎 **一致性检查** | LLM 驱动的角色行为/世界观/时间线矛盾检测 |
| 📊 **仪表盘** | 写作进度、情绪节奏图、AI 风险分布 |
| 📥 **导出** | 合并章节导出为 TXT 文件（DOCX 开发中） |
| ⚙️ **设置** | LLM Provider 管理、连接测试、模块信息 |

## Anti-Slop 引擎

核心差异化功能，三阶段降 AI 率：

1. **Prompt 预防** — 生成时注入 332 词条黑名单 + 句式约束 + 角色口癖
2. **本地统计分析** — 毫秒级计算 TTR/句长变异/结构模式/句式重复（零 API 消耗）
3. **定向改写** — 仅对高风险段落调用 LLM 改写，改写后重新评分

评分指标对标朱雀 AI 检测核心维度：

| 指标 | 权重 | 说明 |
|------|------|------|
| 黑名单命中密度 | 30% | AI 高频词在段落中的密度 |
| 词汇多样性 (TTR) | 25% | 低 TTR = 用词重复 = AI 特征 |
| 句长变异系数 | 20% | 低变异 = 句式节奏均匀 = AI 特征 |
| 段落结构模式 | 15% | 命中"三段并列"等模板 = AI 特征 |
| 句式重复度 | 10% | 相邻句子结构雷同 |

## 插件化架构

所有功能模块实现统一的 `Module` 接口，通过配置启用/禁用：

```yaml
# config.yaml
modules:
  enabled:
    - anti_slop      # 降 AI 率（核心）
    - project        # 项目管理
    - bible          # Story Bible
    - outline        # 大纲系统
    - generation     # 生成引擎
    - consistency    # 一致性检查
    - dashboard      # 仪表盘
    - export         # 导出
    - settings       # 设置
```

### 添加新模块

1. 在 `src/novel_craft/modules/` 下创建目录
2. 实现 `Module` 子类和 `create_module()` 工厂函数
3. 在 `config.yaml` 的 `modules.enabled` 中添加模块名
4. 重启应用，新模块自动加载

## 多 LLM Provider 支持

填入 URL + API Key + 模型名即可接入任意 LLM：

```yaml
llm:
  providers:
    claude:
      base_url: "https://api.anthropic.com"
      api_key: "sk-xxx"
      model: "claude-sonnet-4-20250514"
    deepseek:
      base_url: "https://api.deepseek.com/v1"
      api_key: "sk-xxx"
      model: "deepseek-chat"
    ollama:
      base_url: "http://localhost:11434/v1"
      api_key: "ollama"
      model: "qwen2.5:14b"

  # 不同任务可用不同模型
  routing:
    generation: "claude"      # 正文生成用强模型
    summary: "deepseek"       # 摘要用便宜模型
    consistency_check: "deepseek"
```

## 技术栈

- **后端**: Python 3.11 + FastAPI
- **前端**: Streamlit
- **数据库**: SQLite (SQLAlchemy ORM)
- **LLM**: OpenAI 兼容接口 (openai SDK)
- **分词**: jieba
- **模板**: Jinja2

## License

MIT
