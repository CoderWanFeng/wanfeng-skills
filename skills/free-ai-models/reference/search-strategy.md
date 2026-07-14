# 检索策略

> **目的**：当用户问的问题**不在本地 `reference/*.md` 范围**时，AI 如何快速找到答案。

---

## 核心原则

1. **先本地后联网**：本地 80% 的问题能答
2. **官方源优先**：联网只查官方
3. **关键词路由**：用户输入含特定关键词 → 锁定类别 + 推荐模型
4. **场景路由**：用户说用途（写代码 / 翻译 / 写作）→ 推荐最匹配

---

## 关键词路由表

> 用户输入含这些关键词 → 跳过"问类别"步骤，直接给答案。

### 路由到「类别 ①：直接免费用」

| 关键词 | 触发 | 答什么 |
|---|---|---|
| `网站` `网页版` `app` `在线用` | ✅ | 直接免费用的网站清单 |
| `不用注册` `免登录` `匿名` | ✅ | LMArena / Hugging Face Chat |
| `手机上` `App` `iOS` `Android` | ✅ | 移动端 App 清单 |
| `网页` | ✅ | 全部网页版 |

### 路由到「类别 ②：软件里免费切换」

| 关键词 | 触发 | 软件 |
|---|---|---|
| `Cursor` | ✅ | Cursor 专属清单 |
| `Cline` `Roo Code` | ✅ | Cline + 第三方 API |
| `Continue` | ✅ | Continue + 第三方 API |
| `Trae` | ✅ | Trae 专属清单 |
| `Windsurf` `Codeium` | ✅ | Windsurf 专属清单 |
| `Cherry Studio` `ChatBox` | ✅ | 国产 Chat 客户端 |
| `VS Code` `JetBrains` `IDE` | ✅ | 编程 IDE 插件 |
| `LibreChat` `NextChat` `LobeChat` | ✅ | 开源 Chat 客户端 |
| `插件` `扩展` | ✅ | 浏览器/IDE 插件 |

### 路由到「类别 ③：平台免费额度」

| 关键词 | 触发 | 答什么 |
|---|---|---|
| `API` `token` `key` `调用` | ✅ | 平台免费 API 额度 |
| `额度` `配额` `限制` | ✅ | 平台免费 API 额度 |
| `免费用` `免费调用` `免费 token` | ✅ | 平台免费 API 额度 |
| `百万` `千万` | ✅ | token 额度单位 |

### 路由到「本地模型」

| 关键词 | 触发 | 答什么 |
|---|---|---|
| `本地` `离线` `本机` `自己电脑` `自己跑` | ✅ | Ollama / LM Studio / Jan |
| `显存` `GPU` | ✅ | 本地模型硬件要求 |
| `不联网` | ✅ | 本地模型 |
| `跑得动` | ✅ | 按显存推荐模型 |

### 路由到「软件内置 vs 自备 API」分流

| 关键词 | 触发 | 含义 |
|---|---|---|
| `内置` `自带` `官方` | ✅ | 软件内置免费模型 |
| `自备` `自己申请` `我自己去申请` | ✅ | 走第三方 API |

---

## 场景路由表

> 用户说"我要做 XX" → 推荐最匹配的 2-3 个。

| 场景 | 推荐（按优先级） |
|---|---|
| **写代码** | 1. Cursor 内置（Claude 4 / GPT-4o mini）<br>2. Cline + DeepSeek / OpenRouter Free<br>3. Trae（国内友好） |
| **写文章** | 1. Claude.ai 免费版<br>2. Kimi 智能助手（国内无限）<br>3. 通义千问 Qwen3 |
| **翻译** | 1. 沉浸式翻译 + GPT-4o mini<br>2. Gemini App<br>3. Kimi |
| **中文写作** | 1. Kimi / 智谱清言<br>2. 通义千问 Qwen3<br>3. 文心一言 |
| **代码补全** | 1. Cursor / Trae 内置<br>2. Continue + DeepSeek<br>3. JetBrains Mellum |
| **长上下文（> 100k）** | 1. Kimi 网页版<br>2. Gemini 1.5 Pro（API 免费 50 次/日）<br>3. Moonshot v1 128k（API 15 元额度） |
| **图像理解** | 1. Gemini App（国内受限）<br>2. 通义千问 VL（API 限时免费）<br>3. Qwen-VL（本地） |
| **语音转文字** | 1. Groq Whisper（API 免费 7200 秒/日）<br>2. 飞书妙记（国内） |
| **Embedding（向量化）** | 1. Mistral Embed（完全免费）<br>2. SiliconFlow BGE（永久免费）<br>3. Gemini Embedding（API 免费） |
| **Agent / Function Call** | 1. DeepSeek-V3（API 极便宜）<br>2. GLM-4-Flash（API 每日 200 万 token 免费）<br>3. Qwen3（API 限时免费） |

---

## 模型路由（按模型名问）

> 用户说「XXX 免费吗」→ 直接路由到那个模型的免费信息。

### 主流海外模型

| 模型 | 哪类免费 | 答什么 |
|---|---|---|
| **GPT-4o / GPT-4o mini** | ① + ③ | ChatGPT 免费版（限量）+ OpenAI API（新用户 $5） |
| **Claude Sonnet 4 / Opus 4** | ① + ② | Claude.ai 免费版（限量）+ Cursor 内置（500 次/月） |
| **Gemini 2.0 Flash** | ① + ③ | Gemini App + Google AI Studio（60 RPM） |
| **Gemini 1.5 Pro** | ③ | Google AI Studio（2 RPM / 50 RPD） |
| **Llama 3.3 70B** | ② + ③ | Groq（30 RPM）+ OpenRouter Free + Ollama |
| **Mistral Large / Small** | ① + ③ | Mistral Chat + Mistral Console |
| **Mixtral 8x7B** | ③ | Groq + OpenRouter Free |
| **Whisper（语音）** | ③ | Groq 7200 秒/日 |

### 主流国内模型

| 模型 | 哪类免费 | 答什么 |
|---|---|---|
| **Qwen3 / Qwen-Plus** | ① + ③ | 通义千问网站 + 阿里云百炼（新用户 100 万） |
| **DeepSeek-V3 / R1** | ① + ③ | DeepSeek Chat（无限）+ DeepSeek API（送 200 万） |
| **GLM-4-Flash** | ① + ③ | 智谱清言 + 智谱 API（200 万/日永久免费） |
| **Doubao 1.5 Pro** | ① + ③ | 豆包网站 + 火山引擎（新用户 50 万） |
| **Hunyuan Turbo** | ③ | 腾讯云（新用户 100 万） |
| **Kimi / Moonshot v1** | ① + ③ | Kimi 网页（无限）+ Moonshot API（15 元） |
| **ERNIE 4.0** | ① + ③ | 文心一言（50 次/日）+ 百度智能云（部分免费） |
| **Spark 4.0** | ① + ③ | 讯飞星火（200 万永久免费） |
| **Moonshot v1 128k** | ① + ③ | Kimi 网页（无限）+ Moonshot API（15 元） |
| **Qwen-VL / Qwen2-VL** | ① + ③ | 通义千问网站 + 阿里云百炼 |

---

## 检索优先级

> 当用户问的问题不只属于一个类别，按这个优先级给答案：

1. **具体模型名**（如"GPT-4o 免费吗"）→ 直接答那个模型
2. **软件名**（如"Cursor"）→ 类别 ②
3. **场景**（如"写代码"）→ 类别 ② + ③ 混合
4. **泛问**（如"免费大模型"）→ 三大类都列

---

## WebFetch 检索的备用源（按可信度）

> 本地无 + 需要 WebFetch 时，按这个顺序：

| 优先级 | 类型 | 例 |
|---|---|---|
| 🥇 1 | 平台官方 Pricing | platform.deepseek.com/api-docs/pricing |
| 🥇 1 | 平台官方控制台文档 | bigmodel.cn/dev/howuse/ |
| 🥈 2 | 平台官方 Blog | blog.google/products/gemini/ |
| 🥈 2 | 软件官方 Pricing | cursor.com/pricing |
| 🥉 3 | 软件官方 changelog | cline/changelog |
| 🥉 3 | 软件官方 README（GitHub） | github.com/cline/cline |
| ⚠️ 4 | 官方公众号文章 | （用 WebSearch 反查 URL） |
| ❌ | 非官方汇总站 | 不用 |
| ❌ | 论坛 / 知乎 | 不用 |

---

## 兜底话术（找不到答案时）

| 情况 | 答什么 |
|---|---|
| 本地无 + WebFetch 失败 | "我没找到这个模型的免费信息。你给的线索是 {用户原话}，我去查了下 {URL}，没看到明确说法。要不你打开 {URL} 确认下？或者换个相近的模型（比如 XX）？" |
| 已知但官方没说"免费" | "官方没明确说免费，但 {可能免费的部分}。建议你直接打开 {URL} 验证下，我不确定。" |
| 模型太小众 | "这个模型我没听过。可能是新的或小众的。你给个链接我看看？" |
| 用户问的是"未来会免费吗" | "这个预测不了。我只能告诉你'截至 YYYY-MM-DD' 它的状态是 {是/否免费}。" |

---

## 关键词 → 答案 速查（最常用的 20 个问题）

| 用户问 | 答什么 |
|---|---|
| "现在哪个 GPT 是免费的？" | ChatGPT 免费版（GPT-4o mini 无限 + GPT-4o 限量） |
| "免费用 Claude" | Claude.ai 免费版（Sonnet 4 限量）+ Cursor 内置（500 次/月） |
| "免费 Gemini API" | Google AI Studio 60 RPM 永久免费 |
| "国内能用的免费 GPT" | 走 OpenRouter Free 或 微软 Copilot（用 Bing 账号） |
| "Cursor 里哪个免费" | Cursor 自研模型 + Gemini 2.0 Flash（无限） |
| "Cline 接哪个 API" | DeepSeek + OpenRouter Free + Gemini |
| "DeepSeek 真的免费吗" | Yes，网页版无限，API 注册送 200 万 token（一次性） |
| "Qwen3 免费吗" | Yes，网页版 + 阿里云百炼新用户 100 万 |
| "智谱 GLM-4-Flash 免费吗" | Yes，每日 200 万 token，**永久免费** |
| "哪个有 200 万 token 免费" | 智谱 GLM-4-Flash / SiliconFlow / Gemini 2.0 Flash |
| "永久免费的 API" | 智谱 / 讯飞 / SiliconFlow / Mistral Embed |
| "国内能开的免费 API" | DeepSeek / 智谱 / 阿里云百炼 / 火山 / 腾讯 / 讯飞 / Moonshot |
| "本地跑大模型" | Ollama / LM Studio + Qwen3-7B / Llama-3.3-8B |
| "8G 显存能跑什么" | Qwen3-14B / DeepSeek-R1-Distill-14B（4-bit） |
| "免费 Embedding" | Mistral Embed / SiliconFlow BGE / Gemini Embedding |
| "免费 Whisper" | Groq 7200 秒/日 |
| "学生免费" | Cursor Student Pack（.edu 邮箱）+ GitHub Student Pack |
| "教育邮箱免费" | JetBrains AI / Cursor Pro / GitHub Copilot |
| "1 元体验" | 阿里云百炼「新人首单 0 元」+ 火山引擎「邀请新人」 |
| "对比 Claude 和 DeepSeek" | 见下方"对比模板" |

---

## 对比模板（用户问"哪个好"时用）

> 当用户问"X 和 Y 哪个好"或"推荐一个"，用以下模板：

```markdown
| 维度 | {模型A} | {模型B} |
|---|---|---|
| 中文能力 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 代码能力 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 速度 | 快 | 中 |
| 免费额度 | 200 万/日 | 100 万/月 |
| 国内可用 | ✅ | ✅ |
| 注册门槛 | 手机号 | 支付宝 |
| 上下文长度 | 8K | 128K |
| 适用场景 | 日常对话、写作 | 长文档分析、代码生成 |

⭐ **推荐**：{按用户的隐含需求推 1 个}
```

**推荐规则**：

| 用户隐含需求 | 推荐 |
|---|---|
| 国内能用 | DeepSeek / 智谱 / 硅基 |
| 中文好 | 智谱 GLM-4-Flash / Qwen3 / 文心 |
| 代码 | DeepSeek-V3 / Qwen3-Coder / Claude 4 |
| 长上下文 | Kimi / Moonshot v1 128k / Gemini 1.5 Pro |
| 速度 | Gemini 2.0 Flash / Groq / SiliconFlow |
| 永久免费 | 智谱 GLM-4-Flash / 讯飞 Spark Lite / SiliconFlow |
| 学生 | Cursor Student Pack + Claude.ai |

---

## 相关文档

- [SKILL.md](../SKILL.md) — 主入口
- [data-update.md](data-update.md) — 数据更新机制
- [direct-free.md](direct-free.md) — 直接免费用清单
- [in-software.md](in-software.md) — 软件内置清单
- [platform-quota.md](platform-quota.md) — 平台额度清单
