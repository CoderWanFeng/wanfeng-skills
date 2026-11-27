---
name: mograph-vlog
display_name: 晚枫自动剪vlog
display_name_en: WanFeng Auto Vlog Cut
description: "晚枫自动剪vlog：只给随手拍的视频、照片和一个素材目录就能出片，不需要口播视频、文稿、字幕或数字人。AI 先真实查看镜头（扫描时长/旋转/音轨 + 抽帧看接触表），再自己选叙事形式、写第一人称旁白、安排转场与丰富动效，先出几秒样片再出成片。旁白讲日常人话，不逐条念屏幕上的花字；画面文字与讲的内容相关即可。可用本人既有克隆音色并按实测时长一次性加速对齐；画幅按发布平台单独排（视频号默认 9:16 竖版），不拉伸凑比例。原真人口播包装与数字人混剪不在本技能里，走姊妹技能「晚枫自动剪视频-Pro」。触发词：晚枫自动剪vlog、剪vlog、日常vlog、随手拍、零碎视频、碎片素材、照片视频混剪、出差记录、旅行记录、活动回顾、把目录剪成视频、没有口播、没有稿子、先出5秒、转场样片、竖版vlog、克隆配音、MiniMax配音、加速配音。"
description_zh: "素材先行的独立 vlog 剪辑技能：给一个装随手拍视频和照片的目录即可，AI 看素材、选形式、写第一人称旁白、排转场和丰富动效，先出几秒样片再出成片。不要求口播、稿子、字幕、数字人或固定封面；旁白不逐条念画面花字；声音可用本人既有克隆音色，加速倍数一次到位；按发布平台单独排版幅。口播包装与数字人混剪仍归 mograph-pro。"
description_en: "A footage-first vlog skill: point it at a folder of casual clips and photos — no talking-head video, script, subtitles, digital presenter or fixed cover required. The agent actually reviews the footage, chooses a narrative form, writes first-person narration, plans transitions and rich motion, and renders a short preview before the full cut. Narration speaks naturally instead of reading on-screen stickers aloud; voice-over may reuse the user's existing MiniMax clone with a single measured speed-up; aspect ratios are laid out per platform (9:16 for vertical feeds). Talking-head packaging and digital-human editing stay in the sibling mograph-pro skill."
version: 1.0.0
agent_created: true
author: 晚枫工作室
license: MIT-0
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
examples_zh:
- "这里只有我随手拍的视频和照片，帮我剪成一条vlog，你先选合适的形式"
- "先出5秒样片，我要看两个素材之间切换的效果，动画丰富一点"
- "把我这个出差目录剪成竖版vlog，用我的克隆声音配音，发视频号"
examples_en:
- "Here are only casual clips and photos — cut them into a vlog and pick the format yourself"
- "Render a 5-second preview first, show me the transition between two clips, keep the motion rich"
- "Turn this business-trip folder into a vertical vlog voiced with my cloned voice for a short-video feed"
metadata:
  emoji: "🎞️"
  requires:
    bins:
      - python3
      - ffmpeg
---

# 晚枫自动剪vlog（mograph-vlog）

> **一句话**：素材目录 → AI 真看镜头 → 选形式 → 写第一人称旁白 → 排转场与动效 → 几秒样片 → 成片。
> **和「晚枫自动剪视频-Pro」的分工**：本技能只管**日常碎片 vlog**——画面是生活，声音是旁白，版式每期重新选。
> 已有对镜头讲话的口播、要给每句话弹卡片、要数字人混剪、要固定底图封面，走 `mograph-pro`，两者互不牵扯。

---

## 一、何时使用

用户这么说就触发：

- 「这些是我日常随手拍的视频」「只有零碎素材，没有稿子」「把这个目录剪成一条 vlog」
- 「帮我选形式，动画丰富一点」「先出 5 秒看看转场效果」「剪成竖的发视频号」
- 「用我的克隆声音配音」「配音太慢，加速 1.2 倍再对画面」

**进来先做一件事：看素材，不看文件名。** 手机随手拍不等于口播视频，目录名不等于故事。素材本身信息够就直接往下做，**不要**回头问用户要口播稿、字幕或数字人；只有缺失信息会实质改变内容时才问一句（例如「这是哪次活动」）。

## 二、不要求什么（写死，防止退回口播打法）

| 不要要求 | 原因 |
|---|---|
| 口播视频、对镜头讲话 | 碎片素材本来就是没对镜头的日常 |
| 文稿、SRT、逐字稿 | 旁白由 AI 按镜头事实自己写 |
| 数字人、固定圆形人头 | vlog 的画面对象是生活场景 |
| 固定品牌版式、三行标题、步骤条、封面模板 | 每期按素材另选母题、字体、配色、节奏 |
| Node / 浏览器 / 联网找现成卡片代码 | 本地 Python + Pillow + ffmpeg 就够 |

不免除的东西照旧：事实核验、人物与证件隐私、原素材只读、付费与上传授权、真实抽帧验收。

## 三、五个阶段

1. **检视**：`python3 scripts/vlog_scan.py --assets <素材目录> --out <选题>/剪辑过程/vlog/检视`
   产出 `inventory.json` + 接触表（时长、旋转、音轨、色彩、抽帧）。然后**用 Read 真的看图**，逐段记「能看到什么 / 可用起止 / 质量问题 / 叙事作用 / 不能证明什么」。
2. **选形式**：按素材特征挑一种叙事（一天时间线＋第一人称轻旁白 / 音乐卡点蒙太奇 / 照片视频混剪 / 路线串联 / 环境声主导），一句话说明理由就继续，不等确认。
3. **写旁白**：口语、短句、第一人称日常话。先给用户看稿就说「先看稿」，就停在稿件。
4. **排画面与动效**：写 JSON 计划（画幅、场景、起止、转场、效果），转场与动效要有**真实中间过程**。
5. **出片**：先按用户要求的秒数渲样片（几秒即可，重点看接缝与动效），确认后再出完整成片。

细则、计划 JSON 契约、效果与转场清单、验收清单见 [references/vlog-workflow.md](references/vlog-workflow.md)。

## 四、旁白与画面文字的关系（硬规则）

- **旁白念的是自然的生活内容，不是把屏幕上的花字一条条读出来。**「去吃个早饭」这种画面贴纸，旁白说「早上先吃点东西，精神足一点再出发」就够了。
- **画面上的字与所讲内容语义相关即可**，标题、贴纸、箭头、日期地点章都不必与旁白逐字相同。
- **同一句话不重复出现两次**：既然已经做成贴纸/大字，底部就别再烧一条一模一样的逐字字幕。
- 人称用「我」，别写「先给讲师充个电」这种把自己当第三方的话；不写新闻通稿腔、不写产品原理课腔。
- 图上没有的数字、地名、价格、学员反馈不许编；拍不到的环节不写成已经拍到。

## 五、声音

- 用户明确要用本人音色时，复用**已配置好的既有克隆音色**（MiniMax `t2a_v2`，原速合成）。密钥只在原配置处读取，不写进任务文件、计划 JSON、日志或发布包；服务不可用或没授权就退回音乐/环境声版本，**不偷偷换公共音色**。
- 供应商返回偏慢时按用户给的倍数（如 1.2×）**只加速一次**：合成原速音频 → 本地 `atempo` → `ffprobe` 实测加速后时长 → 用实测值回填时间轴与画面。禁止为了凑某个镜头反复二次加速。
- 旁白与镜头、贴纸、转场共用同一套实测时间；一段旁白晚于前一段结束就整体后移，别重叠。
- 音乐压在人声下面（先 `volumedetect` 再定倍数），交付前统一响度，避免爆音。

## 六、画幅与平台

- **按发布平台单独排一版**，不把横版拉伸成竖版，也不反过来。视频号 / 抖音竖版：9:16，1080×1920；横版另做左右分栏重排。
- 竖屏素材注意 iPhone 的 `-90` 旋转元数据：成片要真的正过来，抽一帧确认宽高与画面方向。
- 用户指定「只要竖版」时，过程目录里就别再产出横版成片，避免拿错文件发布。

## 七、目录结构

```
mograph-vlog/
├── SKILL.md                        # 本文件：入口与硬规则
├── README.md                       # 30 秒上手 + 示例话术 + FAQ
├── CHANGELOG.md                    # 版本记录
├── LICENSE.md                      # MIT-0 + 音色/肖像说明
├── references/
│   └── vlog-workflow.md            # ⭐ 素材先行全流程与输入/渲染契约、验收、防退化用例
└── scripts/
    ├── vlog_scan.py                # 只读扫描：时长/旋转/音轨/色彩 + 抽帧接触表
    ├── vlog_render.py              # 本地渲染：时间轴、逐帧动效、转场、旁白与配乐混合
    ├── test_vlog_scan.py           # 31 条契约用例
    └── test_vlog_render.py         # 8 条真实 ffmpeg 集成用例
```

## 八、验收与防退化

1. 抽开头、中间、结尾与**动效中间态**帧，真的读图；转场接缝单独看（接缝两侧都不能出现黑帧或错素材）。
2. `ffprobe` 核实测秒数、画幅、帧率、音轨存在；旁白不得被截断，加速只发生一次。
3. `--validate-only` 与单元测试只证明输入契约和基础能力，**不等于**成片已验收；每条真实成片仍要抽帧 + 试听。
4. 过程放 `<选题>/剪辑过程/vlog/`，可发布成片放 `<选题>/发布包/`，原片不入发布包、不被修改。
5. 常见退化：又问用户要口播稿 → 错；旁白逐条念花字 → 错；把贴纸文字又在底部当字幕重复一遍 → 错；横版拉伸成竖版 → 错；配音不够长就二次加速 → 错。
6. 转场报 `The inputs needs to be a constant frame rate` 是滤镜链问题：每条分支末尾要有 `fps=<帧率>`（`setpts` 之后），不是源文件的问题。
