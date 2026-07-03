# netflix-headroom-save-token · 历史范例

> **任务类型**：硬核科普 / 对比（"÷ 20 大数字冲击"）
> **来源文章**：`todo/公众号/task/netflix-headroom-save-token/20260622-netflix-headroom-save-token.md`（AI 太贵？Netflix 开源 Token 压缩神器 Headroom，省 95%）
> **生成时间**：2026-06-23
> **范例渲染**：2026-06-30

## 文件清单

| 文件 | 用途 | 大小 |
|---|---|---|
| `cover-v1.html` | 封面源（2.35:1 900×383）| ~7 KB |
| `cover-v1.png` | 封面渲染产物（1800×766 @2x）| ~55 KB |
| `fig-01-section3-comparison.html` | 配图源（16:9 1200×675，5×5 对比矩阵）| ~5 KB |
| `fig-01-section3-comparison.png` | 配图渲染产物（2400×1350 @2x）| ~45 KB |

## 这个范例演示什么

### 封面（cover-v1.html）

**大数字视觉锤 + 4 卡片纵列** 的典型范式：
- 视觉锤：`÷ 20`（140px 黑字 + 橙色 ::after 偏移副本）— **反常识钩子**
- 信息区：4 卡片纵列 1 行 1 张，**第 4 张"可逆·原文随时取回"绿色高亮**（核心差异点）
- 顶部栏：`NETFLIX · TOKEN · SAVER` + `OPEN SOURCE · 2026-05`
- 角标：`−95% Token`（橙底白字，旋转 6deg）
- 副标："一次上下文压缩 / 省 95% Token 费"

### 配图（fig-01-section3-comparison.html）

**对比矩阵**（fig-template-2）的典型范式：
- 5 行 × 5 列：1 列对比项标签 + 4 列方案对比
- **Headroom 列** 黄色高亮（推荐方案）
- 每行对比一个维度：Token 降幅 / 信息丢失 / 接入成本 / 回答质量 / 适合场景
- 5 秒能看出"为什么 Headroom 比其他方案好"

## 怎么复用

```bash
# 1. 复制整个目录到你的文章 task
cp -r assets/examples/netflix-headroom-save-token/ \
      task/<你的-slug>/imgs/

# 2. 改 5 处内容
#    - 顶栏 kicker（NETFLIX → 你的公司/工具名）
#    - 视觉锤大数字（÷ 20 → 你的数字：÷ 5 / × 10 / −95%）
#    - 角标文字（−95% Token → 你的卖点）
#    - 4 卡片内容（每张改 name + role）
#    - 矩阵的 5 行 × 5 列数据

# 3. 渲染
cd assets && node code/src/render-cover.js \
  examples/netflix-headroom-save-token/cover-v1.html
```

## 设计要点（学这个范例）

1. **大数字视觉锤用反常识运算** — `÷ 20 / × 3 / -95%` 比"高效""快速"更有冲击力
2. **数字不用纯阿拉伯，用中文 + 阿拉伯混合** — "÷ 20" 比 "÷20" 视觉更稳
3. **4 张卡 ≤ 5 张时，纵列 1 列更紧凑** — 横排 4 张会显空
4. **核心差异点用绿色高亮** — 第 4 张"可逆·原文随时取回"是 Headroom 区别于其他工具的关键
5. **对比矩阵每行 1 个维度** — 不要把多个信息塞进一行，否则看不懂
6. **推荐列固定黄色，其他列白色** — 视觉重心一眼锁定

## 对比 ai-photo-father 范例

| 维度 | ai-photo-father（教程型）| netflix-headroom（对比型）|
|---|---|---|
| 视觉锤 | 大汉字（"穿越"）| 大数字（"÷ 20"）|
| 信息区 | 3 卡片纵列（流水线）| 4 卡片纵列（特性）|
| 高亮卡 | 绿色（核心步骤）| 绿色（核心差异点）|
| 配图模板 | fig-template-1（5 卡片横排）| fig-template-2（对比矩阵）|
| 适用选题 | 教程 / 步骤拆解 | 工具横评 / 对比 |

**学完这两个范例，你就覆盖了公众号 80% 的封面/配图场景。**