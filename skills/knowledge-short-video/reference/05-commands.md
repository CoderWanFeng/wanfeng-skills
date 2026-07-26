# 五、关键命令速查

> 7 条命令覆盖整个流水线。命令顺序对应 [Step 1-7](../reference/04-production.md)。

## 5.0 任务目录初始化（Step 0 必走）

```bash
# 创建带时间戳的任务目录
TS=$(date +%Y%m%d_%H%M%S)
TASK="${TS}_<任务名>"
mkdir -p "$TASK"/{01-Script,02-VisualSpec,03-Cover,04-Composition,05-Audio/segments,06-Render,07-Publish}
cp 口播稿/skills/knowledge-short-video/assets/task-config.sample.json "$TASK/task-config.json"
echo "✅ 任务目录已创建: $TASK"
```

## 5.1 TTS 合成（每段独立 wav）

**默认（系统默认 TTS）**：

```bash
OUT_DIR=<task>/05-Audio/segments \
  python3 tools/tts/default-tts.py
```

**自定义（按 Step 0 选定）**：

```bash
# 按 task-config.json 自动适配
OUT_DIR=<task>/05-Audio/segments \
  CONFIG=<task>/05-Audio/tts-config.json \
  python3 tools/tts/custom-tts.py
```

## 5.2 拼 wav + 出 timeline.json

```bash
# 拼接 segments/ 下所有 wav，段间插 0.15s 静音
python3 tools/audio/concat-with-silence.py \
  --input <task>/05-Audio/segments \
  --output <task>/05-Audio/narration.wav \
  --gap 0.15

# 生成 timeline.json
python3 tools/audio/build-timeline.py \
  --segments <task>/01-Script/segments.txt \
  --audio <task>/05-Audio/narration.wav \
  --output <task>/05-Audio/timeline.json
```

## 5.3 初始化 swiss-grid 项目（参考用）

```bash
npx hyperframes init my-video --example swiss-grid
```

## 5.4 Chrome headless 截 cover（swiss-grid）

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --no-sandbox --window-size=1080,1440 \
  --force-device-scale-factor=1 \
  --screenshot=<task>/03-Cover/cover-v1.png \
  "file://<task>/03-Cover/cover-v1.html"
```

> ⚠️ **验证完 cover.png 正确后，必须删掉 cover-v*.html / cover-v*.png 中间产物**（保留选定版 cover.png）。
> 见 [§0.0.1 中间产物清理](../reference/04-production.md#001-中间产物清理必读)。

## 5.5 注入时间戳到 composition

```bash
python3 tools/video/resync.py \
  --template <task>/04-Composition/composition.template.html \
  --timeline <task>/05-Audio/timeline.json \
  --out <task>/04-Composition/composition.html
```

## 5.6 渲染 MP4（CDP 单 Chrome 长连接 · 推荐）

```bash
python3 <task>/06-Render/render.py
# 内部用 Chrome DevTools Protocol 复用单 Chrome 实例
# 速度：~30 帧/秒（vs 单次启动 3.3s/帧 → 118x 加速）
```

## 5.7 拼发布包 3 文件（Step 7）

```bash
PUB=<task>/07-Publish
mkdir -p "$PUB"

# 复制封面（从选定版本，删掉未选定的 v1/v2/v3）
cp <task>/03-Cover/cover.png          "$PUB/cover.png"

# 复制视频（删掉 06-Render/frames/ 渲染中间产物）
cp <task>/06-Render/video_full.mp4    "$PUB/video_full.mp4"

# publish.md 手工写（5 分钟）
```

## 5.8 测 narration.wav 时长（Step 6 硬性前置）

```bash
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 <task>/05-Audio/narration.wav
# → 91.21s
```

> 这个数字必须填到 composition 的 `data-duration`。

## 5.9 改完 HTML 必跑（lint + validate）

```bash
# 验证 composition.html 的 4 条硬约束：
# 1. 每个 clip 有 data-start + data-duration + data-track-index + class="clip"
# 2. timeline paused + 注册到 window.__timelines[composition-id]
# 3. 视频 muted + 单独 <audio>
# 4. 不用 Date.now() / Math.random() / fetch
python3 tools/lint/composition-check.py <task>/04-Composition/composition.html
```

## 5.10 中间产物清理（每个 Step 完成后必跑）

```bash
# Step 1：删早期草稿
rm -f <task>/01-Script/script-v0.md <task>/01-Script/script-v1.md

# Step 3：删未选定的封面变体
rm -f <task>/03-Cover/cover-v[12].html <task>/03-Cover/cover-v[12].png

# Step 4：删验证截图
rm -f <task>/04-Composition/composition_preview_t*.png

# Step 5：删每段独立 wav（保留拼接后的 narration.wav）
rm -rf <task>/05-Audio/segments/

# Step 6：删渲染中间帧（保留 video_full.mp4）
rm -rf <task>/06-Render/frames/

# Step 7：发布包内禁止任何中间产物（见 §7.5 不放进发布包的文件）
find <task>/07-Publish/ -type f ! \( -name 'cover.png' -o -name 'video_full.mp4' -o -name 'publish.md' \) -delete
```

> ⚠️ **本节命令是硬性约定**——任务做完后发布包目录里只允许 3 个文件（`cover.png` + `video_full.mp4` + `publish.md`）。其他都算脏数据。