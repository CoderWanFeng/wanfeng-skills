# 类别 ③：各大模型平台的免费 API 额度

> **数据基准日**：2026-07-16（含 2026-07-16 新增 OpenCode Zen / NVIDIA NIM / Codex 学术 / Codex 开源 4 类）
> **覆盖范围**：各家模型 API 的免费 tier（按次 / 按 token / 按月）
> **筛选标准**：官方文档明确标注"free tier"、注册即可用
> **更新机制**：本地 30 天内的数据有效，否则 WebFetch 重新抓取

---

## 🌟 特殊白嫖渠道（身份/资格型免费）

> 这些不属于"注册即用"的普通平台免费层，而是**需要某种身份**（研究者、开源维护者、特定生态用户）才能拿到的免费配额。适合有对应身份的用户。

### OpenCode Zen（编程代理精选模型网关）

- **官网**：[opencode.ai/zen](https://opencode.ai/zen)
- **数据日期**：2026-07-16（官方页直抓）
- **免费模型列表**（共 8 个，**限免**，数据可能用于改进）：

| 模型 | 简介 |
|---|---|
| **DeepSeek V4 Flash Free** | DeepSeek 极速版，编程向 |
| **MiMo-V2.5 Free** | 小米 MiMo 开源 |
| **Laguna S 2.1 Free** | — |
| **Ling-3.0-tiny Free** | 蚂蚁集团 Ling 系列小模型 |
| **LongCat-2.0 Free** | 美团 LongCat |
| **North Mini Code Free** | 代码向小模型 |
| **Nemotron 3 Ultra Free** | NVIDIA 旗舰（详见下方"NVIDIA NIM"） |
| **Big Pickle** | 匿名隐身模型 |

- **白嫖步骤**：
  1. 打开 [opencode.ai/zen](https://opencode.ai/zen) → 点击「开始使用 Zen」
  2. 登录（邮箱 / GitHub OAuth）→ 充值 $20（**必须**，免费模型也要先充值）
  3. 复制 API key → 在 OpenCode CLI 跑 `/connect` 选 OpenCode Zen → 粘贴
  4. 跑 `/models` 看可用模型列表 → 选带 `Free` 后缀的即可
- **限制**：
  - ⚠️ 8 个 Free 模型**仅限免**（"正在利用这段时间收集反馈并改进模型"）
  - ⚠️ 数据可能**用于改进模型**（非零留存）
  - ⚠️ 即使是免费模型，也需要先**充值 $20**（即用即付，余额低于 $5 时自动再充 $20，可关闭）
- **国内能用**：⚠️ 需海外网络（"所有 Zen 模型均托管在美国"）
- **视频教程**：[BV1TmK36aEBh「白嫖 opencode api 的免费模型」](https://www.bilibili.com/video/BV1TmK36aEBh/)

### NVIDIA NIM / build.nvidia.com（免费试用 API）

- **官网**：[build.nvidia.com](https://build.nvidia.com/explore/discover)
- **数据日期**：2026-07-04（官方页直抓）
- **Free Endpoint 模型**：

| 模型 | 上下文 | 备注 |
|---|---|---|
| ⭐ **Nemotron-3-Ultra-550B-A55B** | 1M | 561B 参数，MoE 架构，agent 推理 / 编程 / 工具调用 |
| **GLM-5.2**（智谱） | — | OpenCode 也引用此端点 |
| **DeepSeek-V4-Pro** | 1M | MoE 架构，编程向 |
| **Thinkingmachines Inkling** | — | 多模态（文本+图像）推理模型 |
| （更多） | — | 官方页 [build.nvidia.com/models](https://build.nvidia.com/models) 筛选 "Free Endpoint" |

- **白嫖步骤**：
  1. 打开 [build.nvidia.com](https://build.nvidia.com) → 注册 NVIDIA 账号（Google / GitHub / 邮箱）
  2. 进入任一标 "Free Endpoint" 的模型 → 点 "Get API Key"
  3. 生成 Personal API Key → 按官方 OpenAI 兼容调用：
     ```python
     from openai import OpenAI
     client = OpenAI(
         base_url="https://integrate.api.nvidia.com/v1",
         api_key="$NVIDIA_API_KEY"
     )
     client.chat.completions.create(
         model="nvidia/nemotron-3-ultra-550b-a55b",
         messages=[{"role":"user","content":""}],
         stream=True
     )
     ```
- **限制**：
  - ⚠️ "仅供试用 — 请勿提交个人或机密数据"（官方原话）
  - ⚠️ "出于安全目的以及为改进 NVIDIA 产品和服务，系统会记录你的使用情况"
  - ⚠️ 免费层按调用次数计费（具体 RPM/RPD 见各模型页）
- **国内能用**：⚠️ 需海外网络（integrate.api.nvidia.com 在美）
- **视频教程**：[BV17tuu6EEec「天塌了，61个大模型，免费用」](https://www.bilibili.com/video/BV17tuu6EEec/)

### OpenAI Codex 两种官方免费（限定身份）

#### A. 学术科研 1 年免费 — ChatGPT for Academic Researchers

- **官方页**：[help.openai.com/articles/20001406](https://help.openai.com/en/articles/20001406-chatgpt-for-academic-researchers)
- **数据日期**：2026-07-29（OpenAI 官方启动日）
- **免费内容**：
  - **12 个月** ChatGPT 工作区（≈ $200/月 ChatGPT Pro 价值）
  - GPT-5.6 **Sol Pro / Terra / Luna** 全家桶
  - **Codex** 全功能（含 ChatGPT Work 任务）
  - **75+ 生命科学 / 学术 Skills**（遗传、基因组、单细胞、蛋白建模、文献检索等）
  - 扩容 Deep Research
  - 可邀请 **4 名同机构协作者**
- **资格**（**全部满足**）：
  - ✅ 高校**研究教职**或**博士后**
  - ✅ 机构有高研究活跃度、能授学位
  - ✅ 近 3 年在 arXiv / bioRxiv / ChemRxiv 发过论文（**你是作者**）
  - ✅ 学科限 7 个：**生物 / 化学材料 / 计算机 / 地球行星 / 工程 / 数学 / 物理**
  - ✅ 通过 SheerID 验证机构邮箱
  - ✅ 提交一篇论文 + 简短研究用途说明
- **限制**：
  - ❌ **不含 OpenAI API credits**（只覆盖 ChatGPT 产品访问）
  - ❌ **不给模型权重**（只有使用权）
  - ⚠️ 数据不用于训练（默认）
  - ⚠️ 限额约等于 ChatGPT Pro（用超要自费买 credits）
- **规模**：今夏首批 10,000 人，2027 年扩展到 100,000 人
- **国内能用**：⚠️ 国家必须在支持名单上（具体见 [官方页](https://help.openai.com/en/articles/20001406)）
- **视频教程**：[BV19PG36pEpN「CodeX免费用1年，申请指南」](https://www.bilibili.com/video/BV19PG36pEpN/)

#### B. 开源项目维护者 6 个月免费 — Codex for Open Source

- **官方页**：[openai.com/form/codex-for-oss/](https://openai.com/form/codex-for-oss/)
- **数据日期**：2026-03-07（OpenAI 启动日）
- **免费内容**：
  - **6 个月** ChatGPT Pro（≈ $1,200 总价值）
  - Codex 全功能（CLI / 桌面 / Web / IDE 插件）
  - **API credits**（从 $1M 「Codex Open Source Fund」拨款，**单项目最高 $25,000**）
  - **Codex Security**（条件性访问，case-by-case 审核）
- **资格**（**主要门槛**）：
  - ✅ 是某个**广泛使用的公共开源项目**的**核心维护者**
  - ✅ 在 GitHub 有**活跃贡献记录**
  - ✅ 项目满足：实质性使用量 / 广泛采用度 / 对生态有明确重要性（三选一）
  - ✅ 有 **write access**（申请 Codex Security 才需要）
  - ❌ **无硬性 Star 数 / NPM 下载量门槛**（小但重要的项目也能申）
- **申请方式**：
  1. 打开 [openai.com/form/codex-for-oss/](https://openai.com/form/codex-for-oss/)
  2. 填 GitHub 仓库地址 + 项目说明 + 为什么 Codex 能帮到你
  3. 提交后滚动审核
- **限制**：
  - ❌ **不覆盖 OpenAI API credits**（ChatGPT Pro 自带的 credits 用完不补）
  - ⚠️ API credits 只给"在 PR 审查 / 维护自动化 / 发布工作流"上用 Codex 的项目
- **国内能用**：✅ 全球维护者都可申请（无国家限制）
- **视频教程**：[BV1jPNs6LELP「免费用6个月的CodeX Pro」](https://www.bilibili.com/video/BV1jPNs6LELP/)

### 对比速查：3 类身份型免费

| 渠道 | 资格 | 持续时间 | 总价值 | 主要限制 |
|---|---|---|---|---|
| **OpenCode Zen Free** | 注册账号 + 充值 $20 | 限免期（可能随时结束） | 按用量计 | 仅 8 个 Free 模型可用 |
| **NVIDIA NIM Free** | NVIDIA 账号 | 持续 | 按用量计 | 数据被收集用于改进 |
| **Codex 学术 1 年** | 高校科研 + arXiv 论文 + 7 学科 | **12 个月** | ≈ $2,400 | 不含 API / 不给权重 |
| **Codex 开源 6 个月** | 开源项目核心维护者 | **6 个月** | ≈ $1,200 + API credits | 仅维护者本人 |

---

## 🌐 海外平台

### Google AI Studio（Gemini）

- **官网**：[aistudio.google.com](https://aistudio.google.com)
- **免费模型与额度**（截至 2026-07-12）：

| 模型 | RPM | RPD | TPM | 备注 |
|---|---|---|---|---|
| Gemini 2.0 Flash | 60 | 1,500 | — | 主力推荐 |
| Gemini 2.0 Flash-Lite | 60 | 1,500 | — | 更便宜（虽然免费也够用） |
| Gemini 1.5 Pro | 2 | 50 | 32,000,000 | 量少 |
| Gemini 1.5 Flash | 15 | 1,500 | 1,000,000 | 仍可用 |
| Gemini Embedding | — | — | — | 完全免费 |

- **注册**：Google 账号
- **国内开通**：⚠️ 需海外网络 + Google 账号
- **API 文档**：[ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits)

### OpenAI Platform

- **官网**：[platform.openai.com](https://platform.openai.com)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| GPT-4o mini | 200 次/日 + 20,000 token/分钟 | 注册送 $5（3 个月有效） |
| GPT-4o | ❌ | 最低 $5 充值 |
| o1 / o3 系列 | ❌ | 不在免费层 |

- **注册**：海外手机号 / Google 账号
- **国内开通**：⚠️ 需海外手机号 + 海外卡
- **特别注意**：注册账号默认有 $5 免费额度（3 个月内用完），不是无限免费

### Anthropic（Claude）

- **官网**：[console.anthropic.com](https://console.anthropic.com)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| Claude Sonnet 4 | 注册送 $5（部分账户） | 限量、不保证 |
| Claude Opus 4 | ❌ | 无免费层 |
| Claude 3.5 Haiku | ❌ | 无免费层 |

- **注册**：Google 账号 / 邮箱
- **国内开通**：⚠️ 需海外网络 + 海外手机号
- **注意**：Anthropic 的"免费"主要通过 Claude.ai 网站，不在 API 层

### Mistral AI

- **官网**：[console.mistral.ai](https://console.mistral.ai)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| Mistral Small | 实验性免费层 | 限速 |
| Mistral Embed | 完全免费 | 文档向量化 |
| Codestral | ❌ | 已停止免费层 |

- **注册**：邮箱
- **国内开通**：✅（注册可用，调 API 需海外网络）

### Groq

- **官网**：[console.groq.com](https://console.groq.com)
- **免费模型与额度**（超快推理）：

| 模型 | RPM | RPD | TPM |
|---|---|---|---|
| Llama 3.3 70B | 30 | 14,400 | — |
| Llama 3.1 8B Instant | 30 | 14,400 | — |
| Mixtral 8x7B | 30 | 14,400 | — |
| Whisper（语音） | — | — | 7,200 秒/日 |

- **注册**：邮箱
- **国内开通**：✅（注册可用，调 API 需海外网络）

### Cohere

- **官网**：[dashboard.cohere.com](https://dashboard.cohere.com)
- **免费模型**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| Command R+ | 1,000 次/月 | 注册即送 |
| Embed | 5,000 次/月 | 文档向量化 |

- **注册**：邮箱
- **国内开通**：⚠️ 部分受限

### Together AI

- **官网**：[api.together.xyz](https://api.together.xyz)
- **免费模型**：

| 模型 | 免费额度 |
|---|---|
| 多种开源模型 | 注册送 $5（用于推理） |

### Fireworks AI

- **官网**：[fireworks.ai](https://fireworks.ai)
- **免费模型**：

| 模型 | 免费额度 |
|---|---|
| 多开源模型 | 注册送 $1 + 每日限量 |

### OpenRouter

- **官网**：[openrouter.ai](https://openrouter.ai)
- **完全免费的模型**（带 `:free` 后缀）：

| 模型 | 限速 |
|---|---|
| meta-llama/llama-3.3-70b-instruct:free | 20 次/分钟 |
| deepseek/deepseek-chat:free | 20 次/分钟 |
| qwen/qwen-2.5-72b-instruct:free | 20 次/分钟 |
| google/gemini-2.0-flash-exp:free | 20 次/分钟 |
| mistralai/mistral-7b-instruct:free | 20 次/分钟 |

- **注册**：邮箱 / Google
- **国内开通**：⚠️ 部分受限

### Hugging Face Inference API

- **官网**：[huggingface.co/docs/api-inference](https://huggingface.co/docs/api-inference)
- **免费模型**：多种开源模型
- **额度**：注册账号送 $0.10/月（Pro $9/月 更多）

### Replicate

- **官网**：[replicate.com](https://replicate.com)
- **免费模型**：多种开源模型（图像/视频/语言）
- **额度**：注册送额度（按模型不同）

---

## 🇨🇳 国内平台

### DeepSeek（深度求索）

- **官网**：[platform.deepseek.com](https://platform.deepseek.com)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| DeepSeek-V3 | 注册送 200 万 token（一次性） | 之后按量计费（极便宜） |
| DeepSeek-R1 | 同上 | 推理模型 |
| DeepSeek-V2.5 | 限时免费 | 旧模型 |

- **注册**：手机号 / 邮箱
- **国内开通**：✅ 全程国内网络
- **API 价格（超便宜）**：V3 1 元 / 百万 input token，2 元 / 百万 output

### 智谱 AI（BigModel）

- **官网**：[bigmodel.cn](https://bigmodel.cn)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| GLM-4-Flash | 每日 200 万 token | 永久免费 |
| GLM-4-FlashX | 每日 200 万 token | 更快版 |
| GLM-Z1-Flash | 每日 200 万 token | 推理模型 |
| Embedding-2 | 每日 200 万 token | 向量化 |

- **注册**：手机号
- **国内开通**：✅
- **API 文档**：[bigmodel.cn/dev/howuse/glm-4](https://bigmodel.cn/dev/howuse/glm-4)

### 阿里云百炼（通义千问）

- **官网**：[bailian.console.aliyun.com](https://bailian.console.aliyun.com)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| Qwen-Plus | 新用户 100 万 token（3 个月内有效） | 注册即送 |
| Qwen-Turbo | 同上 | 更快 |
| Qwen-Long | 同上 | 长上下文 |
| Qwen3 系列 | 限时免费 | 主力推荐 |
| 通义千问 VL | 限时免费 | 多模态 |

- **注册**：支付宝 / 阿里云账号
- **国内开通**：✅
- **活动**：每月有"新人首单 0 元"

### 字节跳动火山引擎（豆包）

- **官网**：[console.volcengine.com/ark](https://console.volcengine.com/ark)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| Doubao-lite-32k | 新用户 50 万 token | 限时 |
| Doubao-pro-32k | 新用户 50 万 token | 限时 |
| Doubao-embedding | 限时免费 | 向量化 |

- **注册**：手机号 / 飞书
- **国内开通**：✅
- **活动**：经常有"邀请新人"活动

### 腾讯云（混元大模型）

- **官网**：[console.cloud.tencent.com/hunyuan](https://console.cloud.tencent.com/hunyuan)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| Hunyuan Turbo | 新用户 100 万 token | 限时 |
| Hunyuan T1 | 新用户 100 万 token | 推理 |
| Hunyuan Embedding | 限时免费 | 向量化 |

- **注册**：QQ / 微信
- **国内开通**：✅

### 百度智能云（文心）

- **官网**：[cloud.baidu.com/product/wenxinworkshop](https://cloud.baidu.com/product/wenxinworkshop)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| ERNIE Speed | 新用户免费 | 轻量 |
| ERNIE Lite | 新用户免费 | 轻量 |
| ERNIE 4.0 | ❌ | 需付费 |
| ERNIE 3.5 | 限时免费 | 主力 |

- **注册**：百度账号
- **国内开通**：✅
- **认证**：需要实名认证才能开 API

### 讯飞星火（Spark）

- **官网**：[console.xfyun.cn](https://console.xfyun.cn)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| Spark Lite | 新用户 200 万 token | 永久 |
| Spark Pro | 新用户 100 万 token | 限时 |
| Spark Max | 新用户 50 万 token | 限时 |
| Spark Ultra | ❌ | 顶级 |

- **注册**：手机号
- **国内开通**：✅

### 月之暗面（Kimi / Moonshot）

- **官网**：[platform.moonshot.cn](https://platform.moonshot.cn)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| Moonshot v1 8k | 新用户 15 元 | 长上下文 |
| Moonshot v1 32k | 新用户 15 元 | 长上下文 |
| Moonshot v1 128k | 新用户 15 元 | 超长上下文 |

- **注册**：手机号
- **国内开通**：✅
- **注意**：Kimi 网页版是免费无限，API 才按量

### SiliconFlow（硅基流动）

- **官网**：[siliconflow.cn](https://siliconflow.cn)
- **免费模型与额度**：

| 模型 | 免费额度 | 备注 |
|---|---|---|
| Qwen2.5-7B/14B/32B/72B | 永久免费 | 限速 |
| DeepSeek-V2.5 | 永久免费 | 限速 |
| Llama-3.3-70B | 永久免费 | 限速 |
| GLM-4-9B | 永久免费 | 限速 |
| BGE Embedding | 永久免费 | 向量化 |

- **注册**：手机号
- **国内开通**：✅
- **特点**：国内最丰富的"永久免费"开源模型 API

### 360 智脑

- **官网**：[ai.360.com](https://ai.360.com)
- **免费模型**：360GPT-S2（限时免费）
- **国内开通**：✅

### 商汤日日新

- **官网**：[platform.sensenova.cn](https://platform.sensenova.cn)
- **免费模型**：SenseChat-Lite（限时免费）
- **国内开通**：✅

### MiniMax

- **官网**：[api.MiniMax.chat](https://api.MiniMax.chat)
- **免费模型**：abab-6.5s（注册送额度）
- **国内开通**：✅

---

## 📊 国内平台对比速查

| 平台 | 主力免费模型 | 永久免费 | 每日/每月免费 | 注册门槛 |
|---|---|---|---|---|
| **DeepSeek** | V3 / R1 | ❌ | 注册送 200 万 token | 手机号 |
| **智谱 AI** | GLM-4-Flash | ✅ 200 万/日 | ✅ | 手机号 |
| **阿里云百炼** | Qwen3 | ❌ | 新用户 100 万 | 支付宝 |
| **火山引擎** | Doubao-lite | ❌ | 新用户 50 万 | 手机号 |
| **腾讯云** | Hunyuan Turbo | ❌ | 新用户 100 万 | QQ/微信 |
| **百度智能云** | ERNIE Speed | ❌ | 限时 | 百度账号 + 实名 |
| **讯飞星火** | Spark Lite | ✅ 200 万 | ✅ | 手机号 |
| **Moonshot** | v1 系列 | ❌ | 新用户 15 元 | 手机号 |
| **SiliconFlow** | Qwen2.5 全系 | ✅ | ✅ | 手机号 |
| **360 智脑** | 360GPT | ❌ | 限时 | 手机号 |

---

## 💡 「完全永久免费」终极清单

> 这些是**官方明确标注"永久免费"**的（不是"限时""新用户"）：

| 平台 | 模型 | 额度 | 国内 |
|---|---|---|---|
| **智谱 AI** | GLM-4-Flash / GLM-4-FlashX / GLM-Z1-Flash | 200 万 token/日 | ✅ |
| **讯飞星火** | Spark Lite | 200 万 token | ✅ |
| **SiliconFlow** | Qwen2.5 / DeepSeek / GLM-4 全系 | 限速永久免费 | ✅ |
| **Gemini** | 2.0 Flash | 60 RPM | ⚠️ |
| **Hugging Face** | 多种开源 | $0.10/月 | ⚠️ |
| **Mistral** | Embed | 完全免费 | ⚠️ |
| **Ollama** | 本地 | 无限 | ✅ |

---

## 🔄 已知变化（高时效性）

| 时间 | 事件 |
|---|---|
| 2026-06 | 智谱 GLM-4-Flash 永久免费额度从 100 万/日升到 200 万/日 |
| 2026-05 | 阿里云百炼 Qwen3 上线，新用户 100 万 token |
| 2026-04 | OpenRouter 推出"Free"模型专区 |
| 2026-03 | Google AI Studio Gemini 2.0 Flash 免费 RPM 从 15 提到 60 |
| 2026-02 | SiliconFlow 全面升级限速策略，多模型"永久免费" |
| 2026-01 | DeepSeek V3 API 价格降至 1 元/百万 input |
| 2026-07-29 | OpenAI 启动 **ChatGPT for Academic Researchers**（学术科研 1 年免费 Codex + GPT-5.6 Sol Pro） |
| 2026-07-16 | OpenCode Zen 上线 **8 个限免模型**（DeepSeek V4 Flash Free / MiMo / Ling / LongCat / Nemotron 3 Ultra / Big Pickle 等） |
| 2026-07-04 | NVIDIA build.nvidia.com 上线 **Nemotron-3-Ultra Free Endpoint** + 多模型免费试用 |
| 2026-03-07 | OpenAI 启动 **Codex for Open Source**（开源维护者 6 个月 ChatGPT Pro + API credits 池 $1M） |

---

## ⚠️ 重要提醒

1. **"新用户免费"≠"永久免费"**：用完额度后要付费
2. **"限时免费"≠"永久免费"**：到期可能转付费
3. **手机号注册**几乎都支持国内手机号
4. **实名认证**：百度智能云/部分平台需要实名才能开 API
5. **海外卡 vs 支付宝/微信**：海外平台大多要海外卡，国内平台支持支付宝/微信
6. **并发限制**：所有平台都有 RPM（每分钟请求数）限制，超出会 429
7. **API 兼容**：智谱/DeepSeek/Qwen 等都兼容 OpenAI API 格式，可以无缝接 Cursor/Cline

---

## 📚 数据来源

- 各平台官方 Pricing 页面
- 各平台官方控制台文档
- 官方公众号 / changelog
- 维护者手动验证（每月 1 号）

## 🔗 相关阅读

- [direct-free.md](direct-free.md) — 直接免费用的网站/App
- [in-software.md](in-software.md) — 软件里能免费选的模型
- [data-update.md](data-update.md) — 数据更新机制
