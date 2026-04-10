<div align="center">

<!-- 古风标题区 -->

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          ████  █  █  ████  █  █  █████  █                    ║
║          █   █ █  █  █   █ █  █  █      █                    ║
║          █   █ █  █  █   █ █  █  ████   █                    ║
║          █   █ █  █  █   █ █  █  █      █                    ║
║          ████  ████  ████  ████  █████  █████                ║
║                                                              ║
║                 ╭─────────────────────╮                      ║
║                 │   笔 · 墨 · 丹 · 青  │                      ║
║                 ╰─────────────────────╯                      ║
║                                                              ║
║          ─── AI 辅助小说写作 · 内置降 AI 率引擎 ───           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

<br>

**「工欲善其事，必先利其器。笔墨纸砚之外，今有 NovelCraft。」**

<br>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-DAA520?style=for-the-badge)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-8B4513?style=for-the-badge)](https://github.com/qiuxinyuan321/novel-craft/pulls)

</div>

---

<div align="center">

### 『 三 大 痛 点 · 一 器 破 之 』

</div>

<table>
<tr>
<td width="33%" align="center">

### 🏮 降 AI 率

**「文以载道，笔墨当随人心。」**

332 词条黑名单 · 多维统计分析 · 定向改写

**对标朱雀 AI 检测**，让 AI 之文，
化为人笔之迹。

</td>
<td width="33%" align="center">

### 🏯 主线不偏

**「纲举目张，大纲既定，万事可期。」**

分层大纲 · 检查点约束 · 叙事里程碑

以**大纲为纲**，以**检查点为目**，
AI 虽千变万化，不出方寸之间。

</td>
<td width="33%" align="center">

### 🏛️ 跨章记忆

**「前事不忘，后事之师。」**

角色口癖 · 世界观硬规则 · 伏笔追踪

**Story Bible** 为小说之唯一真相，
百章千回，人物如一。

</td>
</tr>
</table>

---

## ⚡ 快速开始

```bash
# 一、克隆仓库
git clone https://github.com/qiuxinyuan321/novel-craft.git
cd novel-craft

# 二、安装依赖
pip install -e .

# 三、配置 LLM（填入你的 API Key）
cp config.example.yaml config.yaml

# 四、启动
streamlit run src/novel_craft/ui/app.py
```

打开浏览器访问 `http://localhost:8501`，开始创作。

<details>
<summary><b>📋 config.yaml 配置示例（点击展开）</b></summary>

```yaml
llm:
  default_provider: "claude"
  providers:
    # Anthropic Claude（推荐）
    claude:
      base_url: "https://api.anthropic.com"
      api_key: "sk-your-key-here"
      model: "claude-sonnet-4-20250514"
      max_tokens: 8192

    # DeepSeek（便宜，适合摘要任务）
    deepseek:
      base_url: "https://api.deepseek.com/v1"
      api_key: "sk-your-key"
      model: "deepseek-chat"
      max_tokens: 8192

    # Ollama 本地模型（免费）
    ollama:
      base_url: "http://localhost:11434/v1"
      api_key: "ollama"
      model: "qwen2.5:14b"

  # 不同任务使用不同模型（省钱策略）
  routing:
    generation: "claude"         # 正文生成用强模型
    rewrite: "claude"            # 改写用强模型
    summary: "deepseek"          # 摘要用便宜模型
    consistency_check: "deepseek" # 一致性检查用便宜模型
```

**支持任何兼容 OpenAI Chat Completions API 的服务。**

</details>

---

## 🏮 九 大 功 能 模 块

<div align="center">

```
                    ┌─────────────┐
                    │  📚 项目管理  │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────┴──────┐┌─────┴──────┐┌──────┴──────┐
     │ 📖 角色世界观 ││ 🗂️ 分层大纲 ││ ✍️ AI 写作台 │
     │  Story Bible ││  检查点约束  ││  场景生成    │
     └──────┬──────┘└─────┬──────┘└──────┬──────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────┴──────┐┌─────┴──────┐┌──────┴──────┐
     │ 🔍 AI 检测   ││ 🔎 一致性   ││ 📊 仪表盘   │
     │  降AI率引擎  ││  矛盾检测   ││  情绪节奏图  │
     └─────────────┘└────────────┘└─────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
         ┌──────┴──────┐       ┌──────┴──────┐
         │ 📥 导出      │       │ ⚙️ 设置      │
         │  TXT/DOCX   │       │  LLM 配置   │
         └─────────────┘       └─────────────┘
```

</div>

| 模块 | 功能 | 亮点 |
|:---:|------|------|
| 📚 **项目管理** | 创建/管理多部小说 | 一个项目 = 一部小说，独立数据隔离 |
| 📖 **Story Bible** | 角色档案 · 世界观 · 伏笔 | **口癖系统**：方言/口头禅/禁用词，每角色独立语言风格 |
| 🗂️ **分层大纲** | 章 → 场景树形结构 | **检查点约束**：定义必达叙事里程碑，AI 不可跑偏 |
| ✍️ **写作台** | AI 场景生成 | 自动注入大纲 + 角色口癖 + 前文摘要 + anti-slop 规则 |
| 🔍 **AI 检测** | 逐段分析 AI 痕迹 | **风险热力图** + **一键改写**高风险段落 |
| 🔎 **一致性检查** | 矛盾检测 | LLM 驱动：角色行为/世界观/时间线/称谓/伏笔 |
| 📊 **仪表盘** | 进度 · 统计 · 可视化 | **情绪节奏折线图** + AI 风险分布图 |
| 📥 **导出** | 合并为完整文件 | TXT 一键下载（DOCX 开发中） |
| ⚙️ **设置** | LLM 配置管理 | 图形化 Provider 管理 + 一键连接测试 |

---

## 🔍 Anti-Slop 引擎 —— 核心差异化

> **「大巧若拙，大辩若讷。」** —— 让 AI 之文，不着 AI 之痕。

现有的 AI 小说工具几乎没有内置降 AI 率能力。NovelCraft 的 Anti-Slop 引擎是核心差异化，专为通过**朱雀 AI 检测**设计。

### 三阶段工作流

```
┌─────────────────────────────────────────────────────────┐
│  阶段 A: Prompt 预防                                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 332 词条黑名单（随机抽取 50 个注入）              │    │
│  │ + 句式多样化约束 + 角色口癖强制 + 段落节奏控制    │    │
│  └─────────────────────────────────────────────────┘    │
│                         ↓                                │
│  阶段 B: 本地统计分析（毫秒级·零 API 消耗）              │
│  ┌─────────────────────────────────────────────────┐    │
│  │ TTR 词汇多样性 │ 句长变异系数 │ 结构模式匹配     │    │
│  │ 黑名单命中密度 │ 相邻句式重复 │ → 逐段风险评分   │    │
│  └─────────────────────────────────────────────────┘    │
│                         ↓                                │
│  阶段 C: 定向改写（仅高风险段落）                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 针对具体风险点改写 → 重新评分 → 最多循环 2 轮    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 评分指标

| 指标 | 权重 | 原理 |
|------|:----:|------|
| 黑名单命中密度 | **30%** | 「然而」「不禁」「内心深处」…… AI 高频词越多越可疑 |
| 词汇多样性 (TTR) | **25%** | 用词重复 = AI 特征，人类写作 TTR 通常 0.4-0.7 |
| 句长变异系数 | **20%** | 句式节奏均匀 = AI 特征，人类写作长短交替 |
| 段落结构模式 | **15%** | 命中「首先/其次/最后」三段式等模板 |
| 句式重复度 | **10%** | 相邻句子结构雷同 |

---

## 🧩 插件化架构

> **「海纳百川，有容乃大。」**

所有功能模块实现统一的 `Module` 接口。新增功能 **不改已有代码**：

```python
# 三步添加新模块：

# 1. 创建 modules/your_module/__init__.py
class YourModule(Module):
    name = "your_module"
    version = "1.0.0"

    def get_pages(self):
        return [PageDef(title="新功能", icon="🆕", render=your_page)]

def create_module():
    return YourModule()

# 2. 在 config.yaml 中启用
# modules:
#   enabled:
#     - your_module

# 3. 重启应用 —— 新页面自动出现在导航中
```

### 多 LLM Provider 即插即用

```yaml
# 填 3 个字段即可接入任意 LLM：
providers:
  any_name:
    base_url: "https://your-api.com/v1"  # ← URL
    api_key: "sk-xxx"                     # ← Key
    model: "your-model"                   # ← 模型名
```

支持 **Claude / OpenAI / DeepSeek / Ollama / 任何兼容服务**，还可按任务路由到不同模型。

---

## 📐 技术栈

<div align="center">

| 层 | 技术 | 用途 |
|:---:|:---:|------|
| 🎨 前端 | **Streamlit** | Python 全栈，零 Node 依赖 |
| ⚙️ 后端 | **FastAPI** | API 层 + 业务逻辑 |
| 💾 数据库 | **SQLite** | 零部署，单文件存储 |
| 🤖 LLM | **OpenAI SDK** | 统一接口，多 Provider |
| 📝 分词 | **jieba** | 中文文本分析 |
| 📄 模板 | **Jinja2** | Prompt 模板引擎 |

</div>

---

## 🗺️ 路线图

- [x] Anti-Slop 降 AI 率引擎（332 词条黑名单 + 多维评分 + 定向改写）
- [x] 项目管理 + Story Bible（角色口癖/世界观/伏笔）
- [x] 分层大纲 + 检查点约束
- [x] AI 场景生成引擎（大纲 + 记忆 + anti-slop → 正文）
- [x] 一致性检查（LLM 驱动矛盾检测）
- [x] 仪表盘 + 情绪节奏图
- [x] 导出功能 + 设置页面
- [ ] ChromaDB 向量语义检索（长篇跨章记忆增强）
- [ ] DOCX/EPUB 导出
- [ ] 角色关系图谱可视化
- [ ] 多视角场景生成
- [ ] Docker 一键部署

---

## 🤝 参与贡献

欢迎 PR！添加新模块只需实现 `Module` 接口，无需修改已有代码。

```bash
# 开发环境
pip install -e ".[dev]"
pytest
```

---

<div align="center">

```
╭──────────────────────────────────────╮
│                                      │
│    「 文 章 千 古 事 ，               │
│      得 失 寸 心 知 。 」             │
│                                      │
│              —— 杜甫《偶题》          │
│                                      │
╰──────────────────────────────────────╯
```

**MIT License** · Made with ❤️ for Chinese novel writers

</div>
