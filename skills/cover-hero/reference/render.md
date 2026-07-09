# 渲染 + 迭代流程

> skill 包含 2 个核心脚本：`pick-template.js`（多平台模板选择）+ `render-cover.js`（HTML → PNG）。两个脚本串起来用。

---

## 一、双脚本流水线

### 完整流程

```bash
# Step 1：选平台 + 产物 → 生成 HTML 骨架
node assets/code/src/pick-template.js \
  --platform <平台> \
  --type cover|figure|frame \
  --style default|compact|bold \
  --output task/<slug>/imgs/cover-v1.html

# Step 2：编辑 HTML（改 5 区内容）

# Step 3：渲染 HTML → PNG
node assets/code/src/render-cover.js \
  task/<slug>/imgs/cover-v1.html
```

### 脚本职责

| 脚本 | 职责 |
| --- | --- |
| `pick-template.js` | 根据平台/产物/风格参数，从 `assets/code/templates/` 复制对应骨架 + 应用平台适配层 + 写 `data-width/height` |
| `render-cover.js` | 读 HTML 上的 `data-width/height` → Puppeteer 截图 → 输出 2× DPI PNG |

---

## 二、pick-template.js 用法详解

### 命令行接口

```bash
node assets/code/src/pick-template.js \
  --platform <平台> \
  --type <产物类型> \
  --style <风格档位> \
  --output <输出路径>
```

### 参数对照

| 参数 | 取值 | 默认 | 说明 |
| --- | --- | --- | --- |
| `--platform` | `wechat` / `xhs` / `douyin` / `zhihu` / `bilibili` / `weibo` / `og` / `twitter` | `wechat` | 目标发布平台 |
| `--type` | `cover` / `figure` / `frame` | `cover` | 产物类型（封面 / 配图 / 视频帧） |
| `--style` | `default` / `compact` / `bold` | `default` | 风格档位（基于 HyperFrames 内部调整） |
| `--output` | 文件路径 | 自动生成 | 输出 HTML 路径 |

### 实际调用示例

```bash
# 公众号封面（2.35:1 标准）
node assets/code/src/pick-template.js --platform wechat --type cover --output task/foo/cover-v1.html

# 小红书笔记封面（3:4 高反差）
node assets/code/src/pick-template.js --platform xhs --type cover --output task/foo/xhs-cover-v1.html

# 抖音视频帧（9:16 戏剧）
node assets/code/src/pick-template.js --platform douyin --type frame --output task/foo/dy-frame-v1.html

# 抖音横屏视频帧（16:9）
node assets/code/src/pick-template.js --platform douyin --type frame --style bold --output task/foo/dy-frame-wide-v1.html

# OG Card 链接预览（1.91:1）
node assets/code/src/pick-template.js --platform og --type cover --output task/foo/og-cover-v1.html
```

---

## 三、render-cover.js 用法详解

### 命令行接口

```bash
node assets/code/src/render-cover.js <path-to-html>
```

### 渲染脚本特性

- 自动读 HTML 里 `.cover` / `.canvas` 上的 `data-width / data-height`，按尺寸渲染
- 2× DPI 输出（deviceScaleFactor: 2）
- 优先走 `node_modules/puppeteer-core`，找不到再扫 `~/.npm/_npx/` 缓存兜底
- 支持任意层级子目录的相对/绝对路径

### 实际调用示例

```bash
# 单张
node assets/code/src/render-cover.js task/foo/imgs/cover-v1.html

# 批量：在新文章 imgs/ 目录里跑
cd task/foo/imgs/
for f in *.html; do
  node ../../../assets/code/src/render-cover.js "$f"
done

# 绝对路径也行
node assets/code/src/render-cover.js /Users/.../fig-03-section8-decision-tree.html
```

### 依赖

```bash
# 项目级
npm install puppeteer-core

# 或全局
npm install -g puppeteer-core
```

---

## 四、标准工作流（5 步）

### 0. 创建 imgs 目录

```bash
mkdir -p task/<slug>/imgs/
```

### 1. 选平台 + 生成骨架

```bash
node assets/code/src/pick-template.js \
  --platform <平台> \
  --type cover \
  --output task/<slug>/imgs/cover-v1.html
```

**这一步会自动**：
- 复制对应模板（6 套之一）
- 应用平台适配层（标准 / 高反差 / 戏剧）
- 写入 `data-width` / `data-height`（按平台规格）

### 2. 编辑 5 区内容

打开生成的 HTML，按 [reference/visual-system.md §"封面 5 区结构"](visual-system.md) 改：

1. 顶栏：kicker + 期号
2. 视觉锤区：大字 + 副标
3. 信息区：主标 + 卡片
4. 角标：旋转 5deg
5. 脚注：账号名 + 期号

### 3. 渲染

```bash
node assets/code/src/render-cover.js task/<slug>/imgs/cover-v1.html
# 产物：imgs/cover-v1.png（按 data-width × 2 输出）
```

### 4. 验证

```bash
ls task/<slug>/imgs/
# 应该看到：cover-v1.png + fig-01-...png + ...
```

### 5. 交付

- 公众号 / 知乎 / B站 / 微博：上传到对应平台后台
- 小红书 / 抖音：发布时直接上传

---

## 五、迭代节奏

每次走这个循环，每轮只改一件事，避免来回反复：

1. 编辑 HTML（一处）
2. `node render-cover.js cover-vN.html`
3. 用户看 PNG → 反馈
4. 只调一处（字号 / 间距 / 配色 / 文案 / 图标），开下一轮 vN+1

**禁止动作**：

- ❌ 一次同时改字号 + 间距 + 文案（出问题定位不到）
- ❌ 用渐变、阴影模糊、玻璃拟态
- ❌ 跳过读文章直接选模板（先读 → 选模板 → 改文案）
- ❌ 改平台规格尺寸（必须保持当前平台的 `data-width/height`）
- ❌ **引入非 HyperFrames 风格**（换字体 / 改圆点纹理 / 去偏移黑阴影）

---

## 六、最快路径

**复用历史范例**：

```bash
# 1. 从历史范例复制 HTML（含已调好的 5 区）
cp assets/examples/ai-photo-father/cover-v1.html \
   task/<new-slug>/imgs/cover-v1.html

# 2. 改文字（保留视觉结构）

# 3. 如果新平台跟历史范例平台不同，用 pick-template.js 改尺寸
node assets/code/src/pick-template.js \
  --platform <新平台> \
  --type cover \
  --output task/<new-slug>/imgs/cover-v1.html
# 然后手动把改好的 5 区内容复制过去
```

整套视觉语言不要换（HyperFrames 风格标志 + 平台适配层）。