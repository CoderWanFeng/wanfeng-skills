# 封装进度记录

## 元信息

- **Skill 名**：`article-cover-illustration`
- **首次封装**：2026-06-30
- **二次优化**：2026-06-30（用更权威的源替换）
- **源材料**：`/Users/wanfeng/晚枫工作室/内容更新/个人网站/python4office.cn/hexo/hexo/source/_posts/workflow/公众号/`
  - 主 SOP：`guide/公众号封面&配图的创作指南.md`
  - 代码 + 模板：`code/src/` + `code/templates/`
- **目标位置**：`/Users/wanfeng/code/wanfeng-skills/skills/article-cover-illustration/`

## 用户决策（已确认）

| 问题 | 决策 |
| --- | --- |
| Skill 范围 | 公众号专用 |
| 目录名 | `article-cover-illustration` |
| SOP 拆分方式 | 拆分成 `reference/*.md`（节省 token） |
| 代码位置 | 复制到新 skill 内（自包含） |
| 历史任务 | 不入 skill（节省体积） |
| deploy/ | 不入 skill（保持上次决策） |

## 进度

### 第一次封装（2026-06-30 早）

| 步骤 | 状态 | 备注 |
| --- | --- | --- |
| 1. 创建目录结构 | ✅ 完成 | |
| 2. 复制代码 | ✅ 完成 | 7 个文件（render-cover.js + 6 模板） |
| 3. 拆分 SOP | ✅ 完成 | 4 个 reference 文件 |
| 4. 写 SKILL.md | ✅ 完成 | |
| 5. 写 README.md | ✅ 完成 | |
| 6. 写 progress.md | ✅ 完成 | |
| 7. 验证 | ✅ 完成 | |

### 二次优化（2026-06-30 晚 — 切换到更权威的源）

| 步骤 | 状态 | 备注 |
| --- | --- | --- |
| 1. 探索新源 | ✅ 完成 | 找到完整目录：`guide/` + `code/{src,templates,deploy}` + `task/` × 11 + `ads/` × 2 |
| 2. 决定覆盖范围 | ✅ 完成 | 用户决策：只优化封面&配图、不纳入 task 历史范例、不要 deploy/ |
| 3. 对比代码/模板 | ✅ 完成 | 与新源 `diff -q` 比对，render-cover.js + 6 模板**完全一致**，无需替换 |
| 4. 重写 4 个 reference | ✅ 完成 | 去掉"任意文章"措辞 + 去掉 1.91:1 / OG Card 等多比例，聚焦公众号唯一比例 |
| 5. 重写 SKILL.md | ✅ 完成 | frontmatter 改为"公众号专用"；适用平台改为"只公众号" |
| 6. 重写 README.md | ✅ 完成 | 适用范围明确"只公众号" |
| 7. 重写 progress.md | ✅ 完成 | 本文件（记录两次封装的全过程） |
| 8. 验证 | ✅ 完成 | 无残留"任意文章" / 多比例 |

## 关键变化对比（v1 → v2）

| 项 | v1（旧 todo/公众号/ 源） | v2（新 晚枫工作室/ 源） |
| --- | --- | --- |
| 适用范围 | 公众号/博客/技术文档/知乎/Newsletter/视频脚本 | **只公众号** |
| 画布比例 | 多比例（2.35:1 + 16:9 + 1.91:1） | **唯一**：2.35:1 + 16:9 |
| frontmatter description | "任意文章" | "公众号文章" |
| 触发关键词 | 公众号/博客 hero 等 | 公众号封面/配图/做头图等 |
| 代码/模板 | render-cover.js + 6 模板 | **完全一致**（diff 0 行差异） |
| Markdown 文章来源 | 任意平台通用 | 公众号内容创作指南产出 |
| 适用平台章节 | 6 行平台表 | "只公众号"一行 |

## 最终文件清单

```
article-cover-illustration/
├── SKILL.md                            7.0K    入口 + 决策树
├── README.md                           2.8K    仓库说明
├── progress.md                         本文件   封装进度
├── reference/
│   ├── visual-system.md                4.3K    HyperFrames 视觉 DNA
│   ├── hard-rules.md                   4.9K    封面三大硬性要求
│   ├── naming.md                       4.7K    命名 + 画布 + 模板
│   └── render.md                       3.7K    渲染 + 迭代
├── assets/
│   ├── code/
│   │   ├── src/
│   │   │   └── render-cover.js         ← Puppeteer 渲染器
│   │   └── templates/
│   │       ├── cover-template.html     ← 主封面模板
│   │       ├── fig-template-1-card-row.html
│   │       ├── fig-template-2-matrix.html
│   │       ├── fig-template-3-decision-tree.html
│   │       ├── fig-template-4-pipeline.html
│   │       └── fig-template-5-summary.html
│   └── examples/                       （空，预留历史范例位置）
```

## 关键设计决策

### 1. 为什么拆 4 个 reference？

原 SOP 接近 600 行，作为 token 优化：

- **`visual-system.md`**：纯视觉 DNA（配色 / 字体 / 5 区结构 / CSS 片段）— 改配色/字体时查阅
- **`hard-rules.md`**：强制要求（名人/Logo / 文字易懂 / 图标可识别 / 自检清单）— 自检时查阅
- **`naming.md`**：文件命名 + 画布规格 + 模板选择 — 不知道用哪个模板时查阅
- **`render.md`**：渲染命令 + 迭代节奏 — 渲染/迭代时查阅

SKILL.md 只承载决策树 + 流程概览，详细规则下沉到 reference/。

### 2. 为什么 `assets/examples/` 是空的？

按用户决策"全不入 skill（推荐 · 节省体积）"，所有历史 task/ 任务（含 `ai-photo-father` 等）都不复制。
templates/ 里已有空白骨架可用，无需历史范例也能上手。

### 3. SKILL.md frontmatter 的设计

```yaml
---
name: article-cover-illustration
description: 为公众号文章生成 HyperFrames 视觉风格的封面 + 正文配图。封装 HTML 手写 + Puppeteer 渲染流水线；6 套空白模板、严格的命名规范、不可改动的视觉 DNA、唯一比例（2.35:1 封面 + 16:9 配图）。当用户提到"公众号封面"、"公众号配图"、"做头图"、"做信息图"、"配张图"且文章主题明确时立即触发。
---
```

- `description` 包含**触发关键词**（"公众号封面"、"公众号配图"、"做头图"、"做信息图"），便于 Agent 自动触发
- `description` 明确**风格锁定**（HyperFrames 视觉风格）+ **比例锁定**（唯一）+ **不使用场景**（AI 生图风格不兼容）
- 用 `name` + `description` 双字段，符合当前 skill 元数据规范

## 后续可选优化（未做，避免过度封装）

- [x] ✅ **增加 `assets/examples/`**：放入 2 个最佳历史范例（`ai-photo-father` 教程型 + `netflix-headroom-save-token` 对比型），每个含 README + cover-v1.html/.png + 1 张 fig-v1.html/.png（2026-06-30 完成）
- [x] ✅ **增加"按文章类型自动选模板"的辅助脚本（CLI）**：`assets/code/src/pick-template.js`（~80 行 Node.js），支持 5 类 type + 中文别名 + 自动读 frontmatter（2026-06-30 完成）
- [ ] 增加 CI：渲染产物自动检查（字号上限 / 元素数量 / 颜色合规）

如未来要做，按需提取单条做即可，不要一次性把上面 3 项都补齐。

## 第三次封装（2026-06-30 — Option C：examples + 自动选模板）

| 步骤 | 状态 | 备注 |
|---|---|---|
| 1. 复制 2 个历史范例（HTML + PNG）| ✅ 完成 | ai-photo-father + netflix-headroom-save-token |
| 2. 写 2 个 example README | ✅ 完成 | 每个含复用指南 + 设计要点 + 与其他范例对比 |
| 3. 写 pick-template.js CLI | ✅ 完成 | ~80 行 Node.js，4 种调用方式 |
| 4. 更新 SKILL.md | ✅ 完成 | 新增 `assets/examples/` 节点 + Step 2 引用 pick-template.js |
| 5. 更新 README.md | ✅ 完成 | 新增"2 套历史范例" + "自动选模板 CLI"小节 |
| 6. 更新 reference/naming.md | ✅ 完成 | "按文章类型挑模板"指向 pick-template.js |
| 7. 更新 progress.md | ✅ 完成 | 本节 |
| 8. 验证 | ✅ 完成 | 2 个 PNG 渲染 + 4 种 pick-template.js 调用测试通过 |