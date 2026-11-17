# Remotion 路线 · engine-remotion.md

> Step 5 的选项 A。适合：**复杂数值动画、图表、需要组件复用与参数化**。
> ⚠️ 先看 §0 的授权检查，再决定商用能不能走这条。

---

## 0. 授权检查（必读，别等成片了才发现）

| 项目 | 事实 | 怎么办 |
|---|---|---|
| Remotion 本身 | **源码可得但非 OSI 开源**：个人与小团队免费，超过一定规模的公司需要购买公司授权 | 商用前查 `remotion.dev/docs/licensing`，把结论写进 `research-notes.md`（R5） |
| 从社区抓来的组件 | 许可各不同（MIT / PolyForm Noncommercial / 无声明） | 逐个按 `research-protocol.md` §4 打分，非商业许可的组件**不进商单工程** |
| 你本 skill 生成的代码 | agent 现写，无外部素材 | 无风险 |

**要完全避开 Remotion 授权问题** → 走 HyperFrames（MIT）或 ffmpeg 兜底路线。

---

## 1. 最小工程

```bash
npx create-video@latest --blank remotion-project   # 或手工搭 src/index.ts
cd remotion-project && npm i remotion @remotion/cli @remotion/media-utils react react-dom
```

目录约定（与本 skill 产物对齐）：

```
src/
├── index.ts                 # registerRoot
├── Main.tsx                 # 唯一 Composition：背景口播视频 + 卡片层
├── overlay-spec.json        # ← make_spec.py 的产物，直接 import
└── components/
    ├── NumberRoll.tsx  BarChart.tsx  SplitCompare.tsx  Checklist.tsx
    ├── QuoteCard.tsx   Timeline.tsx  LogoCard.tsx      KeywordPop.tsx
    └── Card.tsx          # 通用外壳：slot 定位 + 入场出场 + 安全区
```

---

## 2. `Card.tsx`：把 spec 的 slot / visible 翻译成坐标（本 skill 的关键胶水）

```tsx
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
const SLOT: Record<string, React.CSSProperties> = {
  top:    {left:'6%',  right:'6%',  top:'3%',  alignItems:'center'},
  bottom: {left:'6%',  right:'6%',  bottom:'4%',alignItems:'center'},
  left:   {left:'3%',  top:'24%',   bottom:'24%', width:'23%'},
  right:  {right:'9%', top:'24%',   bottom:'24%', width:'23%'},   // 右留 9% 给平台按钮
};
export const Card = ({slot, inS, outS, children}: any) => {
  const f = useCurrentFrame(), {fps} = useVideoConfig();
  const t = f / fps;
  const enter = spring({frame: f - inS * fps, fps, config: {damping: 200}});
  const exit  = interpolate(t, [outS - 0.2, outS], [1, 0], {
    extrapolateClamp: true, easing: (x) => x * x,   // ease-in
  });
  const o = Math.min(enter, exit);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{...SLOT[slot], position:'absolute', display:'flex', flexDirection:'column',
                   opacity: o, transform:`translateY(${(1 - enter) * 24}px)`,
                   willChange:'transform,opacity'}}>{children}</div>
    </AbsoluteFill>
  );
};
```

**约定**：入场只用 `translateY/translateX + opacity`，缓动靠 `spring(damping:200)`（≈ease-out，无过冲）；出场时长 = 入场 × 0.7（`animation-brief.md` §10）。

---

## 3. `Main.tsx`：背景视频 + 按 spec 铺卡

```tsx
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile} from 'remotion';
import spec from './overlay-spec.json';
import {Card} from './components/Card';
import {NumberRoll, BarChart /* ... */} from './components/registry';

export const Main = () => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{backgroundColor: '#0b0b0b'}}>
      <OffthreadVideo src={staticFile('talking-head.mp4')} />
      {spec.segments.filter(s => s.animation).map(s => {
        const a = s.animation;
        const Comp = ({
          'number-roll': NumberRoll, 'bar-chart': BarChart /* …8 类补齐 */,
        } as any)[a.type];
        if (!Comp) return null;                       // 未实现的类型直接跳过，不降级成纯文字
        return (
          <Sequence key={s.id} from={Math.floor(a.visible.start * fps)}
                    durationInFrames={Math.floor((a.visible.end - a.visible.start) * fps)}>
            <Card slot={a.slot} inS={0} outS={(a.visible.end - a.visible.start)}>
              <Comp text={s.text} keywords={a.keywords} brief={a.brief} aspect={spec.meta.aspect} />
            </Card>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
```

**每个卡片组件的 props 契约固定为 `{text, keywords, brief, aspect}`** —— 这样从社区抓来的实现只要包一层适配函数就能接进来（`research-notes.md` 里「迁移要改」那一行就是在写这层适配）。

---

## 4. 渲染

```bash
npx remotion render src/index.ts Main out/final.mp4 \
  --props='{"fps":30}'          # 竖屏 1080x1920 用 --width=1080 --height=1920
npx remotion still src/index.ts Main out/check.png --frame=120   # 抽帧自检用，看完删
```

`durationInFrames` 必须 ≥ `spec.segments` 最后一段的 end × fps，否则尾卡被截。

---

## 5. 这条路线的已知坑

| 坑 | 现象 | 规避 |
|---|---|---|
| `<Video>` 与 `<OffthreadVideo>` 混用 | 渲染时背景黑屏 | 口播源一律用 `OffthreadVideo`（离线解码，不进浏览器） |
| `useState`/`useEffect` 驱动动画 | 抽帧不一致、渲染结果与预览不符 | 只用 `useCurrentFrame()` 纯函数派生（Remotion 的基本契约） |
| 数值滚动用 `frame` 直接算 | 卡点后数字跳变 | `interpolate(frame, [0, 1.2*fps], [0, target], {extrapolateRight:'clamp'})` + `Math.round` |
| 字体没打进容器 | 中文变豆腐块 | `@font-face` + 本地 woff2，或 `--gl` 无头浏览器装中文字体 |
| 逐帧渲染慢 | 60s 片渲 10+ 分钟 | `npx remotion render --concurrency=<核数/2>`；改单卡只重渲该 `<Sequence>`（`--sequence`） |
