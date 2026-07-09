# HyperFrames 视觉风格系统

> 账号所有封面与配图共用的视觉 DNA。**多平台统一底色**（公众号 / 小红书 / 抖音 / 知乎 / B站 / 微博 / OG / Twitter）。**不要换**。

## 1. 视觉 DNA 速查表（账号锁定）

| 元素 | 规格 |
| --- | --- |
| 主底色 | 米白 `#f3efe6` |
| 圆点纹理 | `#d4d0c8` 1px 圆点，间距 18px（`background-size: 18px 18px`） |
| 顶栏 | 黑色 `#0b0d12`，高度 36px，padding 0 28px |
| 主标色 | 黑色 `#0b0d12` |
| 主强调色 | 橙色 `#ff5b1f`（安全橙） |
| 次强调色 | 绿色 `#6cd76b`（选中绿） |
| 辅助色 | 黄色 `#ffd23f`（柠檬黄）/ 蓝色 `#0a3bd9`（IKB） |
| 卡片边 | 黑色 `#0b0d12`，2.5px |
| 卡片偏移阴影 | `box-shadow: 4px 4px 0 #0b0d12`（**HyperFrames 风格标志**，禁止模糊阴影） |
| 字体 | `PingFang SC` / `Helvetica Neue` Bold 700-900 |
| 字号上限 | 视觉锤 160px / 主标 42px / 卡片标题 15px / 标签 11-13px |

## 2. 封面 5 区结构（必须按顺序）

```
顶栏（黑色横条 36px）
├── kicker（左）：主题标签
├── ep（右）：期号标签（橙色）
├──────────────────────────────┤
│                              │
│ 视觉锤（左 1/3）      信息区（右 2/3）
│ - 160px 大字         - 主标 42px
│ - 橙色副标            - 卡片区 3 张
│                              │
│ 角标（旋转 5deg，橙色）        │
├──────────────────────────────┤
脚注：账号名 + 期号
```

## 3. 标志性 CSS 片段

```css
/* 卡片 - HyperFrames 风格的标志 */
.card {
  background: #fff;
  border: 2.5px solid #0b0d12;
  box-shadow: 4px 4px 0 #0b0d12;  /* 偏移硬阴影，不要模糊 */
}

/* 高亮卡片 */
.highlight-card { background: #6cd76b; }

/* 角标 */
.badge {
  background: #ff5b1f;
  color: #fff;
  transform: rotate(5deg);
  box-shadow: 3px 3px 0 #0b0d12;
}

/* 顶栏 */
.top-bar {
  height: 36px;
  background: #0b0d12;
  color: #fff;
  padding: 0 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 圆点纹理底 */
body {
  background: var(--paper);
  background-image: radial-gradient(circle, #d4d0c8 1px, transparent 1px);
  background-size: 18px 18px;
}
```

## 4. 不可改动（账号硬性规范）

- ❌ 不要换主底色（米白 `#f3efe6`）
- ❌ 不要换强调色（橙色 `#ff5b1f` / 绿色 `#6cd76b`）
- ❌ 不要去掉顶栏黑色横条（36px）
- ❌ 不要去掉圆点纹理背景
- ❌ 不要去掉卡片偏移黑阴影 `box-shadow: 4px 4px 0 #0b0d12`
- ❌ 不要在封面放超过 5 个主要元素（视觉锤 / 主标 / 卡片 / 角标 / 脚注）
- ❌ 不要用 emoji 当主视觉锤（用大字号汉字）
- ❌ 不要用渐变、阴影模糊、玻璃拟态（风格不兼容）
- ❌ 不要在静态产物里用视频帧的红黑 swiss-grid 风格（两类产物风格不同源）
- ❌ 不要换比例（封面比例由 `pick-template.js --platform` 决定，**手动改尺寸无效**）
- ✅ **允许**叠加平台适配层（小红书高反差 / 抖音戏剧），但**仅限 pick-template.js 自动注入**，不要手动改 CSS 引入非 HyperFrames 风格

## 5. 与视频帧的关系

| 维度 | 公众号封面/配图（静态） | 视频帧（动态） |
| --- | --- | --- |
| 背景 | 米白 `#f3efe6` + 圆点纹理 | 白 `#fff` + 网格线 |
| 主色 | 黑 `#0b0d12` | 黑 `#0a0a0a` |
| 强调色 | 橙 `#ff5b1f` / 绿 `#6cd76b` | 红 `#E30613` |
| 字体 | PingFang SC / Helvetica | Helvetica Neue / JetBrains Mono |
| 渲染 | 路径 A（手写 HTML + Puppeteer） | HyperFrames（GSAP + composition.template.html） |

冷暖差异是**有意为之**：静态产物（暖）负责"吸引点击"，动态产物（冷）负责"克制呈现"。但字体 / 黑色 / 元素结构三者一致，跨产物系列感不丢。

## 6. 关键边界（重要）

> "用 HyperFrames 生成封面" = **采用 HyperFrames 视觉风格**，**不是用 HyperFrames 工具渲染**。
>
> HyperFrames 是**视频渲染工具**（GSAP + composition.template.html），不直接渲染静态封面。
> 封面和配图采用 HyperFrames 风格，但**实现路径仍为路径 A**（手写 HTML + Puppeteer）。