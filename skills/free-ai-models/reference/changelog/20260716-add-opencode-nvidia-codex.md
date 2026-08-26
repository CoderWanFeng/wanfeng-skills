# Changelog · 2026-07-16

## 更新内容

用户反馈（4 条 B 站视频）需新增 3 类「身份/资格型免费大模型」，全部经 WebFetch 官方源核实后写入。

### 新增 1：OpenCode Zen（编程代理精选模型网关）
- **官方源**：[opencode.ai/zen](https://opencode.ai/zen)、[opencode.ai/docs/zh-cn/zen/](https://opencode.ai/docs/zh-cn/zen/)
- **新增条目**：8 个 Free 模型（DeepSeek V4 Flash Free / MiMo-V2.5 Free / Laguna S 2.1 Free / Ling-3.0-tiny Free / LongCat-2.0 Free / North Mini Code Free / Nemotron 3 Ultra Free / Big Pickle）
- **限制**：⚠️ 需先充值 $20 / 数据可能被收集用于改进 / 仅限免
- **写入文件**：`platform-quota.md`（特殊白嫖渠道章节）+ `in-software.md`（软件条目 + 速查表）+ `search-strategy.md`（路由 + 速查）

### 新增 2：NVIDIA build.nvidia.com Free Endpoint
- **官方源**：[build.nvidia.com/explore/discover](https://build.nvidia.com/explore/discover)、[build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b](https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b)
- **新增条目**：Nemotron-3-Ultra-550B-A55B（1M 上下文 / 561B MoE）+ GLM-5.2 + DeepSeek-V4-Pro + Thinkingmachines Inkling
- **限制**：⚠️ "仅供试用 / 请勿提交个人或机密数据" / 数据被收集用于改进
- **写入文件**：`platform-quota.md`

### 新增 3：OpenAI Codex 两种官方免费
- **官方源**：
  - 学术：[help.openai.com/articles/20001406](https://help.openai.com/en/articles/20001406-chatgpt-for-academic-researchers)
  - 开源：[openai.com/form/codex-for-oss/](https://openai.com/form/codex-for-oss/)
- **新增条目**：
  - A. **学术科研 1 年**：GPT-5.6 Sol Pro + Codex 全功能 + 75+ 学术 Skills（限 faculty / postdoc + arXiv 论文 + 7 学科）
  - B. **开源 6 个月**：ChatGPT Pro + Codex + API credits（限开源核心维护者，可能获 $25K credits）
- **写入文件**：`platform-quota.md`

### 已知变化表追加
- 2026-07-29 OpenAI 学术科研 1 年免费
- 2026-07-16 OpenCode Zen 8 个 Free 模型
- 2026-07-04 NVIDIA build.nvidia.com Free Endpoint
- 2026-03-07 OpenAI Codex for Open Source

## 数据来源

| 类型 | URL |
|---|---|
| OpenCode Zen 主页 | https://opencode.ai/zen |
| OpenCode Zen 文档 | https://opencode.ai/docs/zh-cn/zen/ |
| NVIDIA 模型发现页 | https://build.nvidia.com/explore/discover |
| NVIDIA Nemotron 详情 | https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b |
| Codex 学术官方 | https://help.openai.com/en/articles/20001406-chatgpt-for-academic-researchers |
| Codex 开源官方 | https://openai.com/form/codex-for-oss/ |
| Codex 开源条款 | https://developers.openai.com/codex/codex-for-oss-terms |
| 视频（教程） | BV1skuA6CEDL / BV17tuu6EEec / BV19PG36pEpN / BV1jPNs6LELP / BV1TmK36aEBh |

## 维护者注意

- ⚠️ OpenCode Zen 的 8 个 Free 模型是**限免**，可能随时结束，每月 1 号必须重抓
- ⚠️ NVIDIA Free Endpoint 政策可能调整，每月 1 号重抓 build.nvidia.com/explore/discover
- ⚠️ Codex 学术计划**首批 1 万人**已发出，剩余名额有限
- ⚠️ Codex 开源计划**$1M API credits 池**已发放部分，建议持续关注