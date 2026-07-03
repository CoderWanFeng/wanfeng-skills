# 渲染 + 迭代流程

> skill 只做渲染。本文档按"在 `公众号/` 工程根下"为路径基准写的，使用时按你的实际工程根调整。

---

## 一、渲染命令（HTML → PNG）

### 渲染脚本

`assets/code/src/render-cover.js`（通用，**支持任意层级子目录**）：

```bash
# 相对路径（相对 公众号/ 根）
node code/src/render-cover.js task/<slug>/cover-v1.html

# 也支持绝对路径
node code/src/render-cover.js /Users/.../task/<slug>/fig-03-section8-decision-tree.html

# 批量：渲染某一篇文章的所有产物
cd task/<slug>/imgs/
for f in cover-*.html fig-*.html; do
  node ../../../code/src/render-cover.js "task/<slug>/imgs/$f"
done
```

脚本会自动读 HTML 里 `.cover` / `.canvas` 上的 `data-width / data-height`，输出 2× 高清 PNG。

### 依赖

需要 `puppeteer-core`：

```bash
# 项目级
npm install puppeteer-core

# 或全局
npm install -g puppeteer-core
```

脚本会优先走 `node_modules` 解析，找不到再扫 `~/.npm/_npx/` 缓存兜底。

---

## 二、标准渲染流程

### 0. 创建 imgs 目录

```bash
mkdir -p task/<slug>/imgs/
```

### 1. 复制封面骨架（HyperFrames 风格）

```bash
cp assets/code/templates/cover-template.html \
   task/<slug>/imgs/cover-v1.html
```

编辑 `cover-v1.html` 改主标 / 卡片内容 / 视觉锤。**不要改 data-width/height**（必须保持 2.35:1 900×383）。

### 2. 渲染封面

```bash
node code/src/render-cover.js \
   task/<slug>/imgs/cover-v1.html
# 产物：imgs/cover-v1.png (1800×766，2× DPI)
```

### 3. 复制配图骨架（按"按文章类型挑模板"表选对应模板）

```bash
cp assets/code/templates/fig-template-N.html \
   task/<slug>/imgs/fig-01-sectionX-keyword.html
```

### 4. 批量渲染

```bash
cd task/<slug>/imgs/
for f in cover-*.html fig-*.html; do
  node ../../../code/src/render-cover.js "$f"
done
```

或单张：
```bash
node code/src/render-cover.js task/<slug>/imgs/cover-v1.html
```

### 5. 验证 imgs/ 目录

```bash
ls task/<slug>/imgs/
# 应该看到：cover-v1.png + fig-01-...png + fig-02-...png + ...
```

---

## 三、迭代节奏

每次走这个循环，每轮只改一件事，避免来回反复：

1. 写 `cover-vN.html`
2. `node render-cover.js cover-vN.html`
3. 用户看 PNG → 反馈
4. 只调一处（字号 / 间距 / 配色 / 文案 / 图标），开下一轮 vN+1

**禁止动作**：

- ❌ 一次同时改字号 + 间距 + 文案（出问题定位不到）
- ❌ 把所有插件/项目都塞进封面（最多 5 个，多了挤）
- ❌ 用渐变、阴影模糊、玻璃拟态（这套风格只用纯色 + 偏移黑阴影）
- ❌ 跳过读文章直接选模板（先读 → 选模板 → 改文案）
- ❌ 改封面比例（必须保持 2.35:1 900×383）

---

## 四、最快路径

**复制一份历史范例（如 `task/ai-photo-father/imgs/cover-v1.html`）作为新文章的起点，改文字即可。**

整套视觉语言不要换（顶栏 / 点阵底 / 偏移黑阴影 / 6 色调色板）。