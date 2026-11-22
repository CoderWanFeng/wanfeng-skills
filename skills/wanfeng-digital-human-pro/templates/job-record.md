# 任务卡：<job 名>

> 每个 job 存一份，放在工作目录 `records/` 下。目的是三个月后还能复现同一条片子。

## 输入

| 项 | 值 |
| --- | --- |
| 日期 | YYYY-MM-DD |
| 文稿文件 | `input/script/<名字>.txt` |
| 文稿字数 | |
| 文稿摘要指纹 | `sha256` 前 8 位： |
| 音色 ID | |
| 形象素材 | `input/persona/<文件名>`（视频 / 图片） |
| 形象素材摘要 | `sha256` 前 8 位： |
| 稿子里的镜头标记 | A-roll __ 段 / B-roll __ 段 |

## 参数

| 项 | 值 |
| --- | --- |
| 语音模型 | `speech-2.8-hd` |
| 视频模型 | `MiniMax-H3-Lite` |
| 分辨率 / 比例 | 768P / 9:16 |
| `--segment-seconds` | 13.0 |
| `--transition` | 0.25 |
| `--max-workers` | 4 |

## 花费（估算，以平台账单为准）

| 阶段 | 预估 | 实际 |
| --- | --- | --- |
| 配音 | | |
| 数字人 | | |
| 形象图（如有） | | |
| 合计 | | |

## 产物

| 类型 | 路径 |
| --- | --- |
| 分镜表 | `output/final/plan/<job>/storyboard.json` |
| 时间码表 | `output/final/talking/<job>/a_roll.json` |
| 字幕 | `output/final/talking/<job>/a_roll.srt` |
| A-roll 片段 | `output/final/talking/<job>/seg_*.mp4` |
| 拼接片（非成片） | `output/final/talking/<job>/talking.mp4` |
| 最终交付 | |
| 封面 | |

## 验收

- [ ] 段落顺序与出镜段正确，无残留占位
- [ ] 字幕按最终配音校时
- [ ] 音画时长一致，完整解码通过
- [ ] 无标签朗读、无双重声音
- [ ] 无制作者信息（段号 / B-roll 字样 / 版式示意）
- [ ] 关键帧与切换点已抽查

## 备注

- 本版与上一版的差异：
- 已知问题 / 下次要改的：
