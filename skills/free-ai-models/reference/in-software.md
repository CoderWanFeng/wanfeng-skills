# 类别 ②：软件里能免费切换的大模型

> **数据基准日**：2026-07-12
> **覆盖范围**：主流 AI 软件（IDE / Chat 客户端 / 浏览器插件）里**官方明确支持 + 用户可白嫖**的模型
> **筛选标准**：软件内置可选 + 模型提供方有免费额度 + 不需要用户自掏腰包
> **更新机制**：本地 30 天内的数据有效，否则 WebFetch 重新抓取

---

## 🛠️ AI 编程软件

### Cursor

- **官方页面**：[cursor.com](https://cursor.com)
- **免费模型列表**（截至 2026-07-12）：
  - ✅ Claude Sonnet 4（500 次/月，Pro 会员无限）
  - ✅ GPT-4o mini（无限）
  - ✅ GPT-4o（限量，需 Pro）
  - ✅ Gemini 2.0 Flash（无限）
  - ✅ Cursor 自研小模型（无限，速度快）
- **白嫖方式**：
  - 注册账号 → 免费版（500 次慢速 + 2000 次快速）
  - Pro 会员 $20/月（14 天试用）
  - 学生 Pro 1 年免费（需 .edu 邮箱）
- **国内能用**：✅ 但部分模型要魔法

### Cline / Roo Code（VS Code 插件）

- **官方页面**：[github.com/cline/cline](https://github.com/cline/cline)
- **免费模型接入方式**（用户自备 API key，走第三方免费平台）：
  - ✅ **DeepSeek**（推荐，国内最快，注册送 200 万 token）
  - ✅ **Google AI Studio**（Gemini 2.0 Flash，15 RPM 免费）
  - ✅ **智谱 AI**（GLM-4-Flash，每日 200 万 token）
  - ✅ **通义千问 / 阿里云百炼**（Qwen 系列，新用户 100 万 token）
  - ✅ **OpenRouter**（标"free"的模型无限）
  - ✅ **SiliconFlow**（硅基流动，国产模型免费层）
- **完全免费方案**：用 OpenRouter 的 `meta-llama/llama-3.3-70b-instruct:free` 或 `deepseek/deepseek-chat:free`
- **国内能用**：✅ 全程国内网络可跑

### Continue（VS Code / JetBrains 插件）

- **官方页面**：[continue.dev](https://continue.dev)
- **免费方案**：同上（Cline 的所有免费 API 都适用）
- **额外**：可接 Ollama 本地模型（完全免费，但要本机跑得动）

### JetBrains AI Assistant

- **官方页面**：[jetbrains.com/ai](https://www.jetbrains.com/ai/)
- **免费模型**：
  - ✅ JetBrains AI Pro 试用 7 天
  - ✅ Mellum 模型（代码补全，基础免费）
- **白嫖方式**：试用 / 学生免费（需 .edu 邮箱）/ 开源项目维护者申请

### Trae（字节跳动）

- **官方页面**：[trae.ai](https://trae.ai)
- **免费模型**：
  - ✅ Claude Sonnet 4（限量免费）
  - ✅ GPT-4o / GPT-4o mini
  - ✅ DeepSeek-V3 / R1
  - ✅ Doubao
- **国内能用**：✅ 国内版直接用

### Windsurf

- **官方页面**：[codeium.com/windsurf](https://codeium.com/windsurf)
- **免费模型**：
  - ✅ Cascade Base（自研，基础对话无限）
  - ✅ GPT-4o mini
  - ✅ Claude 3.5 Sonnet（限量）
- **白嫖方式**：免费版 + 注册

---

## 💬 Chat 客户端

### Cherry Studio

- **官方页面**：[cherry-ai.com](https://cherry-ai.com)
- **免费模型接入**：
  - ✅ 内置聚合 20+ 家国内平台（DeepSeek / 智谱 / 通义 / 硅基 / 字节豆包等）
  - ✅ 所有"新用户免费" / "每日免费"的模型都能一键切换
  - ✅ 支持自定义 OpenAI 兼容端点
- **完全白嫖清单**：
  - 智谱 GLM-4-Flash（每日 200 万 token）
  - DeepSeek-V3（注册送 200 万 token）
  - 通义 Qwen-Plus（每日 2000 次）
  - SiliconFlow（多模型免费层）
- **国内能用**：✅ 全程国内网络

### ChatBox

- **官方页面**：[chatboxai.app](https://chatboxai.app)
- **免费模型接入**：与 Cherry Studio 类似
- **白嫖清单**：同上
- **国内能用**：✅

### LibreChat

- **官方页面**：[librechat.ai](https://librechat.ai)
- **完全开源 + 自部署**：免费层取决于你接的 API
- **白嫖方式**：自部署 + 接入 OpenRouter Free / DeepSeek / Gemini

### NextChat / ChatGPT-Next-Web

- **官方页面**：[github.com/ChatGPTNextWeb/ChatGPT-Next-Web](https://github.com/ChatGPTNextWeb/ChatGPT-Next-Web)
- **白嫖方式**：自部署 + 接任意 OpenAI 兼容 API
- **国内能用**：✅（自部署在国内服务器）

### LobeChat

- **官方页面**：[lobechat.com](https://lobechat.com)
- **白嫖方式**：在线版可用 + 接免费 API
- **国内能用**：✅

---

## 🌐 浏览器插件

### Monica（Chrome / Edge）

- **免费模型**：GPT-4o mini / Claude 3.5 / Gemini 2.0 Flash（每日约 30 次）
- **国内能用**：✅（有国内版）

### 沉浸式翻译

- **免费模型**：GPT-4o mini（每日 1000 次）/ 多种开源模型
- **白嫖方式**：免费版 + 注册

### Sider

- **免费模型**：GPT-4o / Claude 3.5（每日约 30 次）
- **国内能用**：⚠️ 部分受限

### Merlin

- **免费模型**：GPT-4o / Claude 3.5（每日约 100 次）
- **国内能用**：⚠️ 部分受限

### 豆包浏览器插件

- **免费模型**：Doubao 1.5 Pro（每日限次）
- **国内能用**：✅

---

## 📊 软件免费程度速查表

| 软件 | 完全免费模型 | 试用 / 限量 | 需自备 API | 国内友好 |
|---|---|---|---|---|
| **Cursor** | Cursor 自研 / Gemini Flash | Claude/GPT-4o 限量 | ❌ | ✅ |
| **Cline** | OpenRouter Free / DeepSeek | — | ✅（推荐） | ✅ |
| **Roo Code** | OpenRouter Free / DeepSeek | — | ✅（推荐） | ✅ |
| **Continue** | OpenRouter Free / DeepSeek | — | ✅（推荐） | ✅ |
| **Trae** | Claude / GPT-4o / DeepSeek | 限量 | ❌ | ✅ |
| **Cherry Studio** | 智谱 / DeepSeek / 通义 | — | ✅ | ✅ |
| **ChatBox** | 智谱 / DeepSeek / 通义 | — | ✅ | ✅ |
| **LibreChat** | 自部署 + 接 API | — | ✅ | ✅ |
| **JetBrains AI** | Mellum | Pro 7 天试用 | ❌ | ⚠️ |
| **Windsurf** | Cascade Base / GPT-4o mini | Claude 限量 | ❌ | ⚠️ |
| **Monica** | GPT-4o mini / Gemini Flash | 每日 30 次 | ❌ | ✅ |
| **沉浸式翻译** | GPT-4o mini / 多开源 | 每日 1000 次 | ❌ | ✅ |

---

## 💡 终极白嫖方案：本地模型

> **完全免费 + 完全离线 + 不限量**——前提是你电脑跑得动。

| 工具 | 模型 | 显存要求 | 速度 |
|---|---|---|---|
| **Ollama** | Llama 3.3 / Qwen3 / DeepSeek-R1-Distill | 8GB+ | 中 |
| **LM Studio** | 同上 | 8GB+ | 中 |
| **Jan** | 同上 | 8GB+ | 中 |
| **GPT4All** | 小模型 | 4GB+ | 快 |

**推荐配置**（2026 年主流）：
- 16GB 显存 → Qwen3-32B / Llama-3.3-70B（4-bit）
- 8GB 显存 → Qwen3-14B / DeepSeek-R1-Distill-14B
- 4GB 显存 → Qwen3-7B / Llama-3.2-8B

**国内能用**：✅（完全离线）

---

## 📚 数据来源

- 各软件官方 Pricing 页面
- 官方 GitHub README
- 官方 changelog
- 维护者手动验证（每月 1 号）

## 🔗 相关阅读

- [platform-quota.md](platform-quota.md) — 各大平台免费 API 额度
- [direct-free.md](direct-free.md) — 直接免费用的网站/App
- [data-update.md](data-update.md) — 数据更新机制
