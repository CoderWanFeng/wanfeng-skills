# HyperFrames 路线 + ffmpeg 兜底 · engine-hyperframes.md

> Step 5 的选项 B / C。
> **B（HyperFrames）**：HTML + GSAP 直接渲成视频，MIT 许可，渲染链路已在社区跑通，本仓库其他 skill（`cover-hero`、`knowledge-short-video`）同源，视觉令牌可复用。
> **C（ffmpeg）**：机器上只有 ffmpeg 时的最后手段，一定能出片，动效朴素一档。

---

## B1. composition 骨架（一份 HTML 搞定）

```html
<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  :root{--ink:#0a0a0a;--bg:#fff;--accent:#E30613;--sans:'PingFang SC','Helvetica Neue',sans-serif}
  html,body{margin:0;width:1080px;height:1920px;overflow:hidden}
  .stage{position:relative;width:1080px;height:1920px;overflow:hidden}
  video.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
  .clip{position:absolute;pointer-events:none}
  /* slot 定位（与 reference/overlay-layout.md §1 一致） */
  .slot-top{left:6%;right:6%;top:58px;text-align:center}
  .slot-bottom{left:6%;right:6%;bottom:76px;text-align:center}
  .slot-left{left:32px;top:460px;width:250px}
  .slot-right{right:96px;top:460px;width:250px;text-align:right}
</style></head><body>
<div class="stage" data-composition-id="thm" data-fps="30">
  <video class="bg" src="talking-head.mp4" muted playsinline></video>

  <!-- ⬇️ 每张卡 = 一个 class="clip" + data-start/data-duration（秒），由 overlay-spec.json 生成 -->
  <div class="clip slot-right" data-start="12.4" data-duration="3.0" data-card="number-roll">
    <div class="label">参数规模</div>
    <div class="val"><span data-to="120">0</span> 万</div>
  </div>
</div>
<script>
  // 单条暂停时间线，seek-safe（HyperFrames 的硬要求：不要用会自行推进的动画）
  const tl = gsap.timeline({paused:true});
  document.querySelectorAll('.clip').forEach(el => {
    const s = +el.dataset.start, d = +el.dataset.duration;
    tl.from(el, {y:24, opacity:0, duration:0.25, ease:'power3.out'}, s)
      .to(el.querySelector('[data-to]'), {textContent:+el.querySelector('[data-to]').dataset.to,
            snap:{textContent:1}, duration:Math.min(1.2,d-0.4), ease:'power3.out'}, s+0.1)
      .to(el, {opacity:0, y:-12, duration:0.18, ease:'power2.in'}, s+d-0.18);
  });
</script></body></html>
```

**要点**：

- `data-start` / `data-duration` 直接取 `animation.visible.start` / `end - start`，**不要自己四舍五入成帧**，交给渲染器；
- 时间线 `paused:true` + 由外部 seek 驱动 —— 这是 HyperFrames 能抽帧一致渲染的前提；
- 只动 `transform` / `opacity`；
- 卡片层永远在 `<video class="bg">` 之后（DOM 顺序即层级），`layer:"front"` 才需要反过来 + 抠图素材。

## B2. 从 spec 生成卡片 HTML（让 agent 做的事，不用脚本）

遍历 `overlay-spec.json` 里 `animation != null` 的段，按 `animation.type` 选 `animation-brief.md` §1–§8 的模板，填入 `text` / `keywords`，拼出上面那段 `.clip`。本 skill **不内置生成器脚本**——卡片内容差异太大，模板化反而限制了 agent 表现力。

## B3. 渲染

```bash
npx hyperframes render ./composition.html --output out/final.mp4   # 具体参数以 npx hyperframes --help 为准
```

装了 HyperFrames 相关 skill（本仓库 `cover-hero` / `knowledge-short-video` 走的同一套）时，优先复用它们的渲染链路与设计令牌，保证同账号视觉一致。

---

## C. ffmpeg 兜底路线（只有 ffmpeg 时）

```bash
# 1) 每张卡出一个 PNG（agent 写 1280x400 的小 HTML，用无头浏览器截图；没有浏览器就手写 SVG→PNG）
# 2) 按 ffmpeg-plan.json 逐条叠加。每条已带好时间窗与坐标，直接拼滤镜即可：
#    {"frame_png":"cards/card-08.png","start":17.38,"end":19.85,
#     "slot":"left","xy":[0.03,0.24],"ffmpeg_xy":"x=W*0.03:y=H*0.24","text":"…"}
ffmpeg -i talking-head.mp4 \
  -filter_complex "\
[0:v][1:v]overlay=x=W*0.74:y=H*0.24:enable='between(t,12.4,15.4)'[v1];\
[v1][2:v]overlay=x=W*0.06:y=H*0.03:enable='between(t,20.0,22.8)'[vout]" \
  -map "[vout]" -map 0:a -c:v libx264 -crf 18 out/final.mp4
```

> `start` / `end` 取的是**卡片可见窗口**（与 `overlay-spec.json` 的 `animation.visible` 一致），不是整句区间——句子比卡长，按整句叠会让卡片赖在屏幕上不走。

**这条路线的诚实说明**（必须告诉用户）：

| 放弃了什么 | 影响 |
|---|---|
| 逐帧数值滚动 | 数字卡只能做「整块淡入淡出」，或预先渲成 PNG 序列再叠（文件大 5–20 倍） |
| 元素级 stagger | checklist 只能整块出现，或每行一张 PNG 分时段叠 |
| 缓动曲线 | `enable='between()'` 是硬开关，入场靠 PNG 自带 alpha 渐变模拟 |

**什么时候不值得走这条路**：卡片 >12 张、或用户明确要「数字跑起来」的效果 —— 直接说清「本机没有 Node，动效会掉一个档次」，让用户决定装环境还是接受降级（R4：不假装等价）。
