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
│   │   └── templates/                  ← 8 套空白 HTML 模板（v5 +2 套竖版专用）
│   │       ├── cover-template.html         横版通用（公众号 / 知乎 / B站 / 微博 / OG / Twitter）
│   │       ├── xhs-cover.html             ⭐ v5 小红书 3:4 专用
│   │       ├── douyin-cover.html          ⭐ v5 抖音 9:16 专用
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
- [x] ✅ **增加 templates/xhs-cover.html / douyin-frame.html 等专用模板**（v5 完成，layout 重新设计为竖版 flex column）

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

## 最终文件清单（v5）

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

---

## v5 · 竖版平台专用模板（2026-07）

| 步骤 | 状态 | 备注 |
|---|---|---|
| 1. 新增 `templates/xhs-cover.html`（3:4 1080×1440）| ✅ 完成 | 顶栏 44px / flex column 布局 / 卡片竖列 |
| 2. 新增 `templates/douyin-cover.html`（9:16 1080×1920）| ✅ 完成 | 顶栏 56px / flex column / 视觉锤 280px / 卡片立体阴影 |
| 3. pick-template.js 加 `PLATFORM_TO_TEMPLATE` 映射 | ✅ 完成 | xhs→xhs-cover.html, xhs-story/douyin→douyin-cover.html, 其他→cover-template.html |
| 4. 端到端验证（context-window-100m 任务）| ✅ 完成 | 3 平台自检全过 + 视觉效果完美 |
| 5. progress.md 更新（v5 段落）| ✅ 完成 | 本节 |

## 关键变化对比（v4 → v5）

| 项 | v4 | v5 |
|---|---|---|
| 竖版平台模板 | 共用 cover-template + CSS 适配层 | **专用模板**（xhs-cover.html / douyin-cover.html）|
| 竖版布局 | 横版 grid 套 3:4/9:16 崩布局（卡片撑高、顺序错乱）| **flex column 重设计**（顶栏 / hero / 卡片 三段式）|
| 视觉锤尺寸（小红书）| 130px（硬塞横版 hero）| **180px**（专门 3:4 视觉比例）|
| 视觉锤尺寸（抖音）| 110px | **280px**（戏剧感，超大吸睛）|
| 端到端测试 | 套横版崩（需要用户手动改 HTML）| **pick-template.js 一键出，0 手动修** |

## v5 测试结果（context-window-100m 任务）

```
=== v5 --article 自动生成 3 平台 ===
✓ wechat-cover-v1.html   (cover-template.html)    1800×766
✓ xhs-cover-v1.html      (xhs-cover.html)        2160×2880
✓ douyin-cover-v1.html   (douyin-cover.html)     2160×3840

=== 4 项自检结果 ===
✓ 尺寸：3 平台 PNG 输出 = data-width × 2 × data-height × 2
✓ 主标字数：wechat ≤14 / xhs ≤20 / douyin ≤8
✓ 文件大小：≤ 2MB（公众号/抖音）/ ≤ 5MB（其他）
✓ 安全区：wechat/xhs/douyin 无要求，OG/Twitter 需标 safe-area
```

## 后续可选优化（v5 之后的新清单）

## 后续可选优化（v5 之后的新清单）

- [ ] pick-template.js 加 `--all-platforms` 一键 8 平台
- [ ] pick-template.js 加 `--html-head` 注入自定义 head（meta og:image 等）
- [ ] quality-check.js 加视觉对比检查（截封面 PNG 跟 examples 对比，找模板漂移）
- [ ] quality-check.js 接入 GitHub Actions CI（PR 时自动跑）
- [ ] 给 fig-template 也加平台专用版本（fig-xhs / fig-douyin，5 个 fig 模板现在都共用 cover-template 的横版布局，竖版可能也崩）

---

## v5.1 · 任务目录约定（2026-07）

| 步骤 | 状态 | 备注 |
|---|---|---|
| 1. 实战任务跑 v5 后发现 cover 跨平台输出平铺混乱 | ✅ 完成 | 跑 `todo/wanfeng-skills-readme-cover/imgs/` |
| 2. 提"每个平台建子目录"约定 | ✅ 完成 | 平台子目录（`wechat/`, `xhs/`, `douyin/`） |
| 3. SKILL.md 加 v5.1 任务目录约定章节 | ✅ 完成 | 5 规则：平台子目录 / fig 进平台子目录 / HTML+PNG 配对 / vN 迭代 / 实战示例 |
| 4. README.md 加 v5.1 章节 | ✅ 完成 | 同步约定 |
| 5. **用户实操发现 fig 没进 wechat 子目录**（fix 文档 + 真实目录） | ✅ 完成 | fig 也放平台子目录里，因为 fig 通常是为某个平台做的 |

## 关键变化对比（v5 → v5.1）

| 项 | v5 | v5.1 |
|---|---|---|
| 任务目录结构 | 平铺（5 个文件混在一起）| 平台子目录 + fig 根目录 |
| 删除某平台 | 需手动识别 + 删（易误删）| 直接 `rm -rf wechat/` |
| 添加某平台 | 手动 mkdir + 移动文件 | `mkdir og/ && cp` |
| fig 跨平台复用 | 文件名冲突风险 | fig 独立编号 `fig-NN-v1`，多平台共用 |

## 实战对比（v5 → v5.1）

```
v5 产物（跑完 v5 + 自己组织）         v5.1 产物（按约定自动）
imgs/                                imgs/
├── wechat-cover-v1.html              ├── wechat/
├── xhs-cover-v1.html                 │   ├── cover-v1.html
├── douyin-cover-v1.html              │   ├── cover-v1.png
├── wechat-cover-v1.png               │   ├── fig-01/
├── xhs-cover-v1.png                  │   │   ├── cover-v1.html
├── douyin-cover-v1.png                │   │   └── cover-v1.png
├── fig-01-v1.html                    │   └── fig-02/
├── fig-01-v1.png                     │       ├── cover-v1.html
├── fig-02-v1.html                    │       └── cover-v1.png
└── fig-02-v1.png                     ├── xhs/
                                      │   ├── cover-v1.html
                                      │   └── cover-v1.png
                                      └── douyin/
                                          ├── cover-v1.html
                                          └── cover-v1.png
```

## v5.1 后续选项（未做）

- pick-template.js 支持 `--output-dir <dir>/<subdir>/` 自动按平台分子目录（用户连手动组织都省了）
- v5.1 没改 pick-template.js，只文档化约定（轻量 + 渐进引入）

---

## v5.2 · 全 8 平台实战 + README 文档化（2026-07）

| 步骤 | 状态 | 备注 |
|---|---|---|
| 1. 实战发现只跑了 3 平台，README 缺 5 个 | ✅ 完成 | 跑 `todo/wanfeng-skills-readme-cover/imgs/` |
| 2. SKILL.md 补 8 平台子目录约定 | ✅ 完成 | 完整目录树（8 平台 + fig-01/fig-02）|
| 3. README.md 同步 8 平台约定 | ✅ 完成 | 实战示例改为"v5.2 全 8 平台"|
| 4. progress.md 补 v5.2 段 | ✅ 完成 | 本节 |
| 5. 跑剩下 5 个平台（xhs-story / douyin-wide / zhihu / bilibili / weibo / weibo-fig / og / twitter）| ✅ 完成 | 11 平台子目录，各 cover 自检全 ✓ |

## 8 平台实战清单

| 平台 | 比例 | cover 模板 | 适配层 |
|---|---|---|---|
| wechat | 2.35:1 | cover-template | standard |
| xhs | 3:4 | xhs-cover | high-contrast |
| douyin | 9:16 | douyin-cover | theatrical |
| xhs-story | 9:16 | douyin-cover | high-contrast |
| douyin-wide | 16:9 | cover-template | theatrical |
| zhihu | 16:9 | cover-template | standard |
| bilibili | 16:10 | cover-template | standard |
| weibo | 5:4 | cover-template | standard |
| weibo-fig | 16:9 | cover-template | standard |
| og | 1.91:1 | cover-template | standard |
| twitter | 2:1 | cover-template | standard |

## 关键变化对比（v5.1 → v5.2）

| 项 | v5.1 | v5.2 |
|---|---|---|
| 平台子目录约定 | 写文档（只跑 3 平台示范）| 跑全 8+ 平台 + fig 跨平台 |
| fig 归属 | 之前说"fig 放根目录"（错）| 全部进平台子目录（wechat/fig-01/ 等）|
| README.md 平台覆盖 | 仅 3 个（公众号 / 小红书 / 抖音）| 11 个子目录（含 2 种尺寸变体）|

## v5.2 后续选项（未做）

- pick-template.js 支持 `--output-dir <dir>/<subdir>/` 自动按平台分子目录（目前要手 mv 到子目录）
- pick-template.js 加 `--all-platforms` 一键 8 平台（目前要跑 8 次）
- v5.3 候选：把 fig 跨平台渲染（同一 fig 内容按平台适配）|

## v5.3 · CLI 自动分目录 + 一键全平台（2026-07）

> 把 v5.1/v5.2 的**文档约定**落到 `pick-template.js` 代码里，两个改动全实现并测过。

| 步骤 | 状态 | 备注 |
|---|---|---|
| A. `--output` 目录时自动分平台子目录 | ✅ 完成 | 新增 `resolveOutputPath(platformKey, opts)`：`.html` 后缀=文件原样输出；目录路径 → `<dir>/<platform>/cover-v1.html` |
| B. `--all-platforms` 一键 8 平台 | ✅ 完成 | main() 加分支：必须配 `--output <dir>`，覆盖 `--platform`（警告），跑 wechat/xhs/douyin/zhihu/bilibili/weibo/og/twitter |
| C. parseArgs 加 `--all-platforms` flag | ✅ 完成 | opts.allPlatforms 默认 false |
| D. printHelp 补方式 6/7 说明 | ✅ 完成 | 新增一键全平台 + 输出路径规则 |
| E. SKILL.md 加 v5.3 段 + 方式 2.5 | ✅ 完成 | A/B 用法 + 组合 --article |
| F. README.md 版本升 v5.3 + 能力表 + CLI 示例 | ✅ 完成 | 本节 |

## 实现要点（v5.3）

- **A · 输出路径判定**：`isFilePath = /\.(html?|png|svg)$/i.test(output) && !endsWith('/')`
  - 文件路径 → 原样输出（用户显式覆盖用）
  - 目录路径 → 平台分子目录（custom 平台除外，custom 仍平铺 `<dir>/custom-WxH-cover-v1.html`）
  - fig 类型进 `<dir>/<platform>/fig-NN-cover-v1.html`（typePrefix 逻辑）
- **B · --all-platforms**：复用 `generateMulti()`，8 平台不含 custom / 尺寸变体（xhs-story / douyin-wide / weibo-fig）

## 测试结果（v5.3）

| 用例 | 命令 | 结果 |
|---|---|---|
| A 目录路径 | `--platform wechat --output /tmp/test-A/` | ✓ `/tmp/test-A/wechat/cover-v1.html` |
| A 文件路径 | `--platform wechat --output /tmp/test-A/custom-name.html` | ✓ `/tmp/test-A/custom-name.html`（原样）|
| B 一键 8 平台 | `--all-platforms --output /tmp/test-B/` | ✓ 8 子目录全生成 |
| B + article | `--article foo.md --all-platforms --output /tmp/test-B2/` | ✓ 8 子目录 + 警告覆盖 platform |

## 关键变化对比（v5.2 → v5.3）

| 项 | v5.2 | v5.3 |
|---|---|---|
| 平台分子目录 | 手动约定（要手 mv）| CLI 自动（`--output <dir>/`）|
| 全平台生成 | 跑 8 次 or `--platform a,b,c...` | `--all-platforms` 一条命令 |
| 输出路径语义 | `--output` 只当文件/平铺目录 | 目录=分子目录，`.html`=文件原样 |

## v5.4 · 内容注入链路 + 竖版布局修复（2026-07）

> 实战反馈两个问题：抖音/小红书封面 (1) 视觉锤文字重叠 (2) 上下大留白；另外制作过程没有"选择内容"的步骤（全靠手改 HTML）。

| 步骤 | 状态 | 备注 |
|---|---|---|
| 1. xhs/douyin 模板 flex 自然流 | ✅ 完成 | `.cover` flex-column；`.hero` flex:0 0 auto；`.cards` flex:1 1 auto；删绝对定位写死高度 |
| 2. pick-template.js 加 injectContent | ✅ 完成 | kicker/hammer/sub/cards 注入；hammer 整段替换 .num 根治 data-hammer 冲突 |
| 3. parseArticle 加 kicker/sub/cards 解析 | ✅ 完成 | 新增 parseCardsBlock + applyCardKV（YAML 缩进列表子集）|
| 4. main() 传新字段 + parseArgs 加 --kicker/--hammer/--sub | ✅ 完成 | 三种入口：CLI flag / frontmatter / 交互 |
| 5. interactiveMode 加内容问答 | ✅ 完成 | 输出路径后问 kicker/hammer/sub/卡片（可跳过）|
| 6. quality-check.js 加卡片数检查 | ✅ 完成 | 竖版渲染后多一项 `✓ N 张卡片（1-5）`|
| 7. 横版 cover-template .sub 注入验证 | ✅ 完成 | injectContent 同时支持 .sub 和 .h |
| 8. SKILL/README/progress 文档 | ✅ 完成 | 本节 |

## 根因分析（v5.4）

**问题 1 · 文字重叠**
- 现象：`.num` 大字上方叠加半透明的旧占位文字（红/橙）
- 根因：手改 HTML 时保留了两个 `data-hammer` 属性（`data-hammer="穿越" data-hammer="6 合一"`），`.num::after { content: attr(data-hammer) }` 取第一个值"穿越"→ 与用户填的"6 合一"叠加
- 修法：`injectContent` 用 `<div class="num" ...>[\s\S]*?</div>` 整段替换，只写一个 `data-hammer`

**问题 2 · 上下大留白**
- 现象：hero 与 cards 之间 150px+ 空白，cards 离底部也大空
- 根因：`.hero { position:absolute; height:620px }` + `.cards { position:absolute; bottom:120px; height:560px }` 都写死，中间没人管
- 修法：`.cover` 改 `display:flex; flex-direction:column`；顶栏 `flex:0 0 auto`；hero `flex:0 0 auto`（内容撑）；cards `flex:1 1 auto`（撑满剩余）

**问题 3 · 没有选择步骤**
- 现象：换内容必须手工编辑 HTML 里的 kicker/num/sub/卡片
- 根因：v4/v5 的 `--article` 解析了 hammer 却从没注入模板（`generateSingle` 没用 opts.hammer）；模板文案全硬编码
- 修法：injectContent 打通链路 + 3 种输入入口（CLI/frontmatter/交互）

## 测试结果（v5.4）

| 用例 | 命令 | 结果 |
|---|---|---|
| 模板布局（无注入）| `--platform xhs/douyin --output /tmp/p1/` → render | ✓ hero↔cards 无缝、无重叠、卡片撑满 |
| CLI 注入 | `--platform xhs --kicker/--hammer/--sub` | ✓ HTML 三段替换、data-hammer 单一 |
| frontmatter + cards | `--article test.md --platform xhs` | ✓ kicker/hammer/sub/3 卡片全注入、pick 高亮 |
| 横版 .sub 注入 | `--platform wechat --sub ...` | ✓ .sub 替换（cover-template）|
| 卡片数自检 | render 竖版 | ✓ "3 张卡片（1-5）"；横版显示"无 .cards 区块" |

## 关键变化对比（v5.3 → v5.4）

| 项 | v5.3 | v5.4 |
|---|---|---|
| 换内容 | 手工编辑 HTML | --kicker/--hammer/--sub / frontmatter cards / -i 问答 |
| 视觉锤 | 手填易留双 data-hammer 重叠 | injectContent 整段替换，单一属性 |
| 竖版布局 | 绝对定位写死高度 → 留白 | flex 自然流，hero 撑内容 + cards 撑剩余 |
| 渲染自检 | 4 项 | 5 项（+卡片数）|
| 交互模式 | 平台/类型/风格/输出/尺寸 | +内容（kicker/hammer/sub/卡片）|