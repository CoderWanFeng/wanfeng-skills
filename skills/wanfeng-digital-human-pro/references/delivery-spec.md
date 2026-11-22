# 施工图三件套：字段规范与验收

v3 的交付不是 mp4，是**一份让任何数字人平台都能直接开工的施工图**。这份文档定义它的字段与验收标准。

## 1. 交付四份文件

工作目录约定：`./digital-human-work/`（首次运行由 skill 引导用户创建，只 mkdir，不写任何密钥）。

```
digital-human-work/
├── segments.json                分段脚本（一份 JSON 承载所有段的结构化字段）
├── prompts/
│   ├── seg_001.txt              每段独立提示词
│   ├── seg_002.txt
│   └── ...
├── asset-checklist.md           素材体检清单
└── README-for-platform.md       复制到平台后台即可开工的施工说明
```

**不交付**：mp4、mp3、srt、A-roll 拼接片、时间码表。这些要么是数字人平台自己的产物，要么是后期（mograph / 晚枫自动剪视频）的输入。

## 2. `segments.json` 字段规范

```json
{
  "target_platform": "minimax",
  "max_seconds_per_segment": 10,
  "speech_rate_cps": 4,
  "source_script": "input/script.txt",
  "generated_at": "2026-11-19T10:00:00Z",
  "segments": [
    {
      "id": "seg_001",
      "text": "大家好，我是这个账号的作者。",
      "duration_hint": 3.5,
      "emotion": "happy",
      "scene": "明亮的书房",
      "shot": "medium-frontal",
      "refs": {
        "persona": "input/persona/face.jpg",
        "voice": "input/voice/source.mp3"
      },
      "notes": "开场句，微笑 + 微微点头"
    }
  ]
}
```

### 顶层字段（必填）

| 字段 | 含义 | 允许值 |
| --- | --- | --- |
| `target_platform` | 目标平台代号 | `minimax` `kling` `vidu` `heygen` `d-id` `wanxiang` `zhiying` `huoshan` `comfyui` `generic` |
| `max_seconds_per_segment` | 本次切段用的单段上限（秒） | 见 `platform-notes.md` §5 表 |
| `speech_rate_cps` | 折算语速（字/秒） | 默认 4 |
| `source_script` | 原稿相对路径 | 用于复现 |
| `generated_at` | 生成时间（UTC ISO8601） | 用于版本比对 |
| `segments` | 段数组 | 见下 |

### 每段字段

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `id` | ✅ | `seg_001` 起递增，与 `prompts/seg_XXX.txt` 文件名对齐 |
| `text` | ✅ | 本段完整台词（已剔除标记） |
| `duration_hint` | ✅ | 按 `speech_rate_cps` 折算的预计秒数 |
| `emotion` | 建议 | 9 值之一，见 `script-writing.md`；不填按 `calm` 处理 |
| `scene` | 建议 | 场景描述（用于生成 prompt 里的背景字段） |
| `shot` | 可选 | 景别：`close-up` `medium-frontal` `full-body` 等 |
| `refs.persona` | ✅（当平台需要） | 相对路径 |
| `refs.voice` | 可选 | 需要克隆音色时给 |
| `notes` | 可选 | 自由文本，给下一环节（人或平台）看的备忘 |

### 保留标记

原稿中的 `[[A]]`、`[[A:happy]]`、`[[A:happy|scene=...]]`、`[[B]]` / `[[BROLL]]`、`[[BROLL:画面提示]]` 这些**在切段时解析成结构化字段**（`emotion`、`scene`、`kind`），**不再原样写入 `text`**。

新增：本 skill 支持 `kind` 字段区分 A/B：

```json
{"id": "seg_003", "kind": "b", "text": "...", "broll_hint": "展示聊天界面"}
```

- `kind: "a"`（默认）：数字人出镜段
- `kind: "b"`：仅台词，画面交给后期 B-roll（本 skill 只写 hint，不生成）

## 3. `prompts/seg_XXX.txt` 排版

### 自然语言型（MiniMax / 可灵 / Vidu / 通用）

一段连贯的话，把六要素融合进去，末尾附台词：

```
一位 30 岁左右的亚洲男性在明亮的书房里，正面中景，自然光从左侧窗户斜射，
面带微笑、语气轻松地对着镜头说话。他微微点头，双手自然垂放在桌面上，
背景是浅木色书架和米色墙壁。竖屏 9:16，浅景深，纪实感。

台词：大家好，我是这个账号的作者。
```

### 结构化字段型（HeyGen / D-ID / 云厂商控制台）

每行一个 `key: value`：

```
subject: 30 岁亚洲男性
shot: medium-frontal
lighting: 自然光 侧顺
emotion: calm
action: 说话 + 微微点头
background: 明亮书房 浅木色书架
duration_hint: 3.5
speech: 大家好，我是这个账号的作者。
```

### 平台特化字段

目标平台有本 skill 不知道的自定义字段时，把字段名与值直接追加到 txt 末尾，用注释行标注：

```
# 以下为 MiniMax 特有字段
ratio: 9:16
voice_id: my-clone-voice
```

## 4. `asset-checklist.md`

见 `material-prep.md` §6 模板。核心是三档状态（✅ / ⚠️ / 🔄）+ 每项实测数据 + 目标平台的要求对照 + 补素材的具体动作。

## 5. `README-for-platform.md` 结构

这份是**给人复制粘贴用的**。它的组织原则：用户拿到它，从上到下打开目标平台后台，一栏一栏填就行。

```markdown
# 施工说明 · <目标平台>

## 一次配置（本任务只需设一次）

- 形象参考：<asset-checklist.md 里标 ✅ 的 persona 文件路径>
- 音色：<voice 文件路径 或 voice_id>
- 默认场景：<从 segments[0].scene 推>
- 画幅：<比例>

## 分段清单

| 段号 | 时长（秒） | 情绪 | 台词摘要 | 提示词 |
| --- | --- | --- | --- | --- |
| seg_001 | 3.5 | happy | 大家好，我是… | [打开](prompts/seg_001.txt) |
| seg_002 | ... | ... | ... | ... |

## 开工顺序建议

1. 先做最短的一段试效果（示例：seg_XXX，<n> 秒）
2. 效果满意 → 按段号顺序补齐余下 N-1 段
3. 每段生成后按 a_roll 顺序交给后期（本 skill 不做拼接）

## 已知不确定项

- <列出 platform-notes.md 里未覆盖的、需要用户自查平台文档的点>
```

## 6. 验收清单（S3 结束前）

**产物层**：

- [ ] `segments.json` 是合法 JSON；顶层与每段字段齐
- [ ] `prompts/` 里每个 `seg_XXX.txt` 都能被 `segments.json` 里的 `id` 对上
- [ ] `asset-checklist.md` 里**至少一项 persona** 是 ✅
- [ ] `README-for-platform.md` 里的段数与 `segments.json` 一致

**内容层**：

- [ ] 每段 `duration_hint` ≤ 目标平台单段上限（`platform-notes.md` §5）
- [ ] 每段 `emotion` 落在 9 值内；不合法值改回 `calm`
- [ ] 原稿里的 `[[A]]`、`[[BROLL:xxx]]` 标记**都不出现在** `text` 里（已解析进字段）
- [ ] 单括号 `[A]` 之类未替换的标记**一个都不残留**（这条最容易翻车，见 `troubleshooting.md`）

**用户确认**：

- [ ] 一共几段、最长段几秒、哪几段有情绪切换 —— 已念给用户听并确认
- [ ] 用户回复"就这样"或已按用户要求改过一轮

## 7. 什么情况下这份交付不合格

- 用户拿着 `README-for-platform.md` 到平台后台**不知道下一步点哪里** → `README-for-platform.md` 结构不完整
- 平台拒绝某段（超长） → `segments.json` 的 `max_seconds_per_segment` 与实际平台上限不符，回 `platform-notes.md` §5 更新表
- 生成出来"嘴在动但不对词" → 目标平台其实不接受参考音频（走错了平台），见 `platform-notes.md` §2

以上任何一条命中，都算 S3 未完成。不要交付出去让用户自己踩。
