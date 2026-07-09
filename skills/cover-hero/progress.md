# 封装进度记录

## 元信息

- **Skill 名**：`cover-hero`（中文别名：封面侠）
- **首次封装**：2026-06-30
- **第二次优化（聚焦公众号）**：2026-06-30
- **第三次扩展（多平台）**：2026-07-01（用户需求：支持 8 个平台分发 + 风格档位）
- **源材料**：`/Users/wanfeng/晚枫工作室/内容更新/个人网站/python4office.cn/hexo/hexo/source/_posts/workflow/公众号/`
  - 主 SOP：`guide/公众号封面&配图的创作指南.md`
  - 代码 + 模板：`code/src/` + `code/templates/`
  - 历史范例：`task/{ai-photo-father, netflix-headroom-save-token}/`
- **目标位置**：`/Users/wanfeng/code/wanfeng-skills/skills/cover-hero/`

## 用户决策（已确认）

| 问题 | 决策 |
| --- | --- |
| 目录名 | `cover-hero`（中文别名：封面侠）|
| SOP 拆分方式 | 拆分成 `reference/*.md`（节省 token） |
| 代码位置 | 复制到新 skill 内（自包含） |
| deploy/ | 不入 skill |
| 历史范例 | 不入 skill（v1）/ 选 2 个放入 examples/（v3：ai-photo-father + netflix-headroom） |
| v3 平台覆盖 | 公众号 + 小红书 + 抖音 + 知乎 + B站 + 微博 + OG Card + Twitter Card（共 8 个） |
| v3 交互顺序 | 文案先行 → 平台选择（用户决策） |
| v3 风格策略 | HyperFrames 统一覆盖 + 平台适配层（小红书高反差 / 抖音戏剧） |
| v3 风格档位 | default / compact / bold（全部基于 HyperFrames，不引入新风格） |
| v3 可调维度 | 调色板 / 比例 / 装饰强度 / 主标文字数（多选） |

## 进度

### v1 · 首次封装（2026-06-30 早）

只支持公众号，6 套空白模板。

### v2 · 二次优化（2026-06-30 晚）

切换到更权威的源（晚枫工作室），强化"只公众号"边界，去掉多比例。

### v3 · 三次扩展（2026-07-01）

**重大变化**：
- 平台扩展：公众号 → 8 个平台（公众号 / 小红书 / 抖音 / 知乎 / B站 / 微博 / OG / Twitter）
- 新增交互流：6 步对话（文案先行 → 平台 → 风格 → 产物 → 渲染）
- 新增平台适配层：小红书高反差 / 抖音戏剧 / 其他标准
- 新增 pick-template.js：CLI 多平台模板选择器
- 新增 reference/platforms.md：8 个平台规格 + 适配层 CSS
- 新增历史范例：ai-photo-father + netflix-headroom（reference 范例）

| 步骤 | 状态 | 备注 |
| --- | --- | --- |
| 1. 设计 8 平台规格表 | ✅ 完成 | platforms.md |
| 2. 设计 6 步交互流 | ✅ 完成 | SKILL.md |
| 3. 重写 SKILL.md | ✅ 完成 | frontmatter 改为多平台，6 步交互流 |
| 4. 重写 reference/naming.md | ✅ 完成 | 加多平台文件命名规则 |
| 5. 新增 reference/platforms.md | ✅ 完成 | 8 平台 × 适配层 CSS |
| 6. 重写 reference/visual-system.md | ✅ 完成 | 加平台适配层允许规则 |
| 7. 重写 reference/render.md | ✅ 完成 | 双脚本流水线（pick + render） |
| 8. 重写 reference/hard-rules.md | ✅ 完成 | 加平台主标字数限制表 |
| 9. 重写 assets/code/src/pick-template.js | ✅ 完成 | 完整重写：8 平台 + 3 档位 + 适配层 |
| 10. 重写 README.md | ✅ 完成 | 6 步交互流速查 + 平台支持 |
| 11. 重写 progress.md | ✅ 完成 | 本文件（v1 → v2 → v3） |
| 12. 最终验证 | ✅ 完成 | 见下方 |

## 关键变化对比（v1 → v2 → v3）

| 项 | v1（首次） | v2（聚焦公众号） | v3（多平台扩展） |
| --- | --- | --- | --- |
| 平台 | 公众号（默认） | **只公众号** | **8 个平台**（公众号/小红书/抖音/知乎/B站/微博/OG/Twitter） |
| 比例 | 唯一：2.35:1 + 16:9 | 唯一：2.35:1 + 16:9 | **按平台自适应**（12 种比例） |
| 交互 | 无流程（直接复制模板） | 无流程 | **6 步对话**（文案先行 → 平台 → 风格 → 产物 → 渲染） |
| 风格档位 | 无 | 无 | default / compact / bold（基于 HyperFrames） |
| 平台适配层 | 无 | 无 | 小红书高反差 / 抖音戏剧（自动注入） |
| 脚本 | 仅 render-cover.js | 仅 render-cover.js | **pick-template.js + render-cover.js** |
| 历史范例 | 不入 skill | 不入 skill | 入 2 个（ai-photo-father + netflix-headroom） |
| reference 文件数 | 4 | 4 | **5**（新增 platforms.md） |
| 触发关键词 | 公众号封面/配图 | 公众号封面/配图 | **多平台** + 小红书/抖音/视频帧 |

## 最终文件清单（v3）

```
cover-hero/
├── SKILL.md                            8.0K    入口 + 6 步交互流
├── README.md                           4.5K    仓库说明 + 平台支持
├── progress.md                         本文件   封装进度（v1→v2→v3）
├── reference/
│   ├── visual-system.md                4.5K    HyperFrames 视觉 DNA
│   ├── hard-rules.md                   5.0K    三大硬性 + 平台字数限制
│   ├── platforms.md                    6.5K    8 平台规格 + 适配层 CSS
│   ├── naming.md                       5.0K    命名 + 模板选择
│   └── render.md                       4.5K    双脚本流水线
├── assets/
│   ├── code/
│   │   ├── src/
│   │   │   ├── render-cover.js         ← Puppeteer 渲染器（HTML → PNG）
│   │   │   └── pick-template.js        ← 多平台模板选择器（CLI）
│   │   └── templates/                  ← 6 套空白 HTML 模板
│   │       ├── cover-template.html
│   │       ├── fig-template-1-card-row.html
│   │       ├── fig-template-2-matrix.html
│   │       ├── fig-template-3-decision-tree.html
│   │       ├── fig-template-4-pipeline.html
│   │       └── fig-template-5-summary.html
│   └── examples/                       ← 历史范例
│       ├── ai-photo-father/
│       │   ├── cover-v1.html / .png
│       │   ├── fig-01-section1-5-tips.html / .png
│       │   └── README.md
│       └── netflix-headroom-save-token/
│           ├── cover-v1.html / .png
│           ├── fig-01-section3-comparison.html / .png
│           └── README.md
```

## 关键设计决策

### 1. 为什么 6 步对话流？

用户体验考虑：
- **文案先行**（Step 1）让用户在最低门槛下开始，无需面对"先选哪个平台"的选择困难
- **视觉锤提炼**（Step 2）Agent 自动完成，用户无需懂设计
- **平台选择**（Step 3）多选（≤3 个平台推荐），避免一次性出 10+ 张图
- **风格档位**（Step 4）3 选 1，简单且不引入新风格
- **产物类型**（Step 5）默认 + 调整，无需用户懂技术细节
- **渲染**（Step 6）双脚本流水线，命令可复制粘贴

### 2. 为什么用 pick-template.js 而不是手写 HTML 模板？

**好处**：
- 用户只关心"哪个平台 + 哪个产物"，不需要懂 data-width/height
- 自动应用平台适配层（小红书高反差 / 抖音戏剧），避免手写 CSS 错误
- 自动写入 `data-width` / `data-height`，保证 render-cover.js 正确读取

**坏处**：
- 多了一层抽象，用户改起来要先看 CLI

**结论**：利大于弊。新用户上手更快，老用户也能 `cp` 模板手改。

### 3. 为什么不允许"非 HyperFrames 风格"？

- **品牌一致性**：账号视觉跨平台统一，避免割裂感
- **质量保证**：HyperFrames 已经验证 11+ 个 task 的视觉效果
- **避免倒退**：放开风格 = 让用户做出模糊阴影、渐变、玻璃拟态，回到糟糕的设计

具体约束：换字体 / 改圆点纹理 / 去偏移黑阴影 → 全部 ❌ 拒绝。

### 4. 为什么 3 个风格档位（default/compact/bold）而不是更多？

- **3 档覆盖 90% 场景**：默认 + 信息密集 + 强吸睛
- **再多用户记不住**：5 档以上变成"我到底选哪个"
- **变体用适配层**：平台差异（小红书高反差 / 抖音戏剧）走平台维度，不走风格维度

## 后续可选优化（v3 列的清单 · 已在 v4 全部完成）

- [x] ✅ **pick-template.js 加 `--article` 自动从 frontmatter 读 type + platform**（v4 2026-07 完成）
- [x] ✅ **pick-template.js 加交互模式（`-i` 跑入问答）**（v4 完成）
- [x] ✅ **增加 CI：渲染产物自动检查（主标字数 / 安全区 / 文件大小 / 尺寸）**（v4 quality-check.js 完成）
- [x] ✅ **增加 assets/examples/ 的范例 README**（v4 加 v3 平台信息章节）
- [ ] 增加 templates/xhs-cover.html / douyin-frame.html 等**专用模板**（当前共用 cover-template + 适配层）— **保留待用**（v4 适配层已覆盖 80% 场景，专用模板是 nice-to-have）

---

## v4 · 多平台增强（2026-07）

| 步骤 | 状态 | 备注 |
|---|---|---|
| 1. A1 修 `--article` | ✅ 完成 | 从 frontmatter 读 type / platform / hammer / mention / label |
| 2. A2 交互模式 `-i` | ✅ 完成 | 4 步问答 + 可选自定义尺寸 |
| 3. C1 多平台一键 | ✅ 完成 | `--platform wechat,xhs,douyin` 逗号分隔 |
| 4. C1 自定义尺寸 | ✅ 完成 | `--width/--height` / `--ratio + base-width/height` / `--label` |
| 5. C2 渲染后自检 | ✅ 完成 | 4 项检查：尺寸 / 主标字数 / 文件大小 / 安全区 |
| 6. C3 CSS 独立化 | ✅ 完成 | adaptations/{standard,high-contrast,theatrical}.css |
| 7. B2 examples README 更新 | ✅ 完成 | 2 个 README 加 v4 多平台建议章节 |
| 8. D 文档同步 | ✅ 完成 | SKILL.md / README.md / progress.md 全部更新 |

## 关键变化对比（v3 → v4）

| 项 | v3 | v4 |
|---|---|---|
| `pick-template.js` 调用方式 | 仅 `--platform` 单一预设 | 新增 `--article` / `--interactive` / `--width/--height` / `--ratio` / `--multi-platform` |
| 平台支持 | 8 个预设平台（写死 width/height）| 8 个预设 + **任意自定义尺寸** |
| 适配层 | inline 字符串注入到 HTML | **独立 CSS 文件**（adaptations/*.css）|
| 自检 | 人工对照 platforms.md | **自动 4 项自检**（render-cover.js 渲染完直接打印报告）|
| 用户体验 | 必传 `--platform wechat` 等 | 新用户**只需 `--article <md>`**，skill 自动推断 |
| 交互模式 | 无 | **`-i` 进入问答**，适合命令行不熟的用户 |
| 渲染路径 | `render-cover.js` 单文件 | `render-cover.js` + `quality-check.js` 两个职责清晰 |

## 最终文件清单（v4）

```
cover-hero/
├── SKILL.md                            入口（v4 更新交互流 + 5 步）
├── README.md                           仓库说明（v4 加自定义尺寸 + --article 用法）
├── progress.md                         本文件（v1→v2→v3→v4 完整记录）
├── reference/ (5 文件)
│   ├── visual-system.md                HyperFrames 视觉 DNA
│   ├── hard-rules.md                   三大硬性 + 平台字数限制
│   ├── platforms.md                    8 平台规格 + 适配层 CSS
│   ├── naming.md                       命名 + 模板选择
│   └── render.md                       双脚本流水线 + 自检
├── assets/
│   ├── code/
│   │   ├── src/
│   │   │   ├── render-cover.js         ← Puppeteer 渲染器（v4 调 quality-check）
│   │   │   ├── quality-check.js        ← NEW · 渲染后自检 4 项
│   │   │   └── pick-template.js        ← 多平台模板选择器（v4 加 --article / --interactive / 自定义尺寸 / CSS 独立化）
│   │   ├── adaptations/                ← NEW · 平台适配层 CSS
│   │   │   ├── standard.css            公众号 / 知乎 / B站 / 微博 / OG / Twitter
│   │   │   ├── high-contrast.css       小红书
│   │   │   └── theatrical.css          抖音
│   │   └── templates/                  6 套空白 HTML 模板（与之前一致）
│   └── examples/                       历史范例
│       ├── ai-photo-father/            ← v4 README 加"3 平台建议"
│       └── netflix-headroom-save-token/ ← v4 README 加"4 平台建议"
```

## 关键设计决策

### 1. 为什么 pick-template.js 加 `--article`？

用户的实际工作流：**有 MD 文章 + 想出多平台图**。
之前必须：手动查 platform 列表 → 写 `platform: wechat,xhs,douyin` → 跑 3 次。
现在：MD frontmatter 加 `platform: wechat xhs douyin` → 跑 1 次 `--article <md>` → 3 张图自动出。
**减少 67% 命令 + 0 重复输 platform 列表**。

### 2. 为什么适配层要独立 CSS 文件？

之前 inline 字符串注入到 HTML 头部，**用户改 CSS 会被下次 pick-template.js 覆盖**。
独立 CSS 文件后：
- 用户改 `assets/code/adaptations/xhs.css` → 永久生效
- pick-template.js 改 HTML 结构 / 适配层都不互相影响
- 多个 HTML 共享同一个 CSS 引用（CDN 模式）

### 3. 为什么 render-cover.js 加自检？

v3 之前用户**完全靠人工对照** platforms.md 检查主标字数、安全区、文件大小。
v4 之后**渲染完自动 4 项检查**，不通过会显示 ⚠ 但**不阻塞**（用户可继续发布）。

## 后续可选优化（v4 之后的新清单）

- [ ] 增加 templates/xhs-cover.html / douyin-frame.html 等**专用模板**（nice-to-have，适配层已覆盖 80%）
- [ ] pick-template.js 加 `--all-platforms` 一键 8 平台
- [ ] pick-template.js 加 `--html-head` 注入自定义 head（meta og:image 等）
- [ ] quality-check.js 加视觉对比检查（截封面 PNG 跟 examples 对比，找模板漂移）
- [ ] quality-check.js 接入 GitHub Actions CI（PR 时自动跑）

如未来要做，按需提取单条做即可，不要一次性把上面 5 项都补齐。