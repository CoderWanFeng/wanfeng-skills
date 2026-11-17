# 联网检索协议 · research-protocol.md

> **这是本 skill 的心脏。** skill 不自带动效库，靠这一份协议让你在**运行时**把社区最新的实现拉下来。
> 执行者：**用户本地的 AI agent**（不是云端服务，不需要 API Key）。
> 时间预算：v1 硬上限 **8 次搜索 + 4 次全文抓取**，超了就降级用内置最小实现（见 §5）。

---

## 1. 什么时候必须联网

| 场景 | 要不要联网 | 说明 |
|---|---|---|
| 用户要「像某某视频那样」的动效 | ✅ 必须 | 检索目标 = 复现参考片的动效语法 |
| 口播稿里有数据图 / 对比 / 时间轴需求 | ✅ 必须 | 这类组件自带实现最值钱 |
| 只要 3–5 张字卡，且用户赶时间 | ⚠️ 可跳 | 直接用 `animation-brief.md` 内置最小实现 |
| 完全离线（飞机上 / 无网） | ❌ 不能 | **必须在交付里写明「本次未联网」**（硬规则 R4） |

---

## 2. 检索词矩阵（照着拼，不要自由发挥）

**公式**：`<动画类型> + <引擎> + <上下文> + <限定词>`

| 动画类型 | 中文检索词 | 英文检索词（社区密度更高，优先） |
|---|---|---|
| number-roll 数字滚动 | `Remotion 数字滚动 组件 口播` | `Remotion counting number animation talking head` |
| bar-chart 数据图 | `Remotion 柱状图 动画 视频叠加` | `Remotion chart animation data visualization video` |
| split-compare 分屏对比 | `口播视频 分屏对比 动效 开源` | `split screen comparison overlay Remotion component` |
| checklist 逐条清单 | `视频 逐条出现 清单 动画 GSAP` | `staggered list reveal animation Remotion` |
| quote-card 引用卡 | `引用卡片 花字 视频叠加` | `kinetic typography quote card overlay Remotion` |
| timeline 时间轴 | `视频 时间轴 动画 组件 开源` | `timeline animation component Remotion` |
| logo-card 品牌卡 | `视频 品牌 logo 弹出入场 动画` | `logo animation lower third Remotion component` |
| keyword-pop 关键词弹字 | `花字 关键词 弹字 视频 GSAP` | `word highlight karaoke text animation video` |

**限定词（按需追加，命中率差别很大）**：`github`、`awesome-remotion`、`site:remotion.dev`、`open source`、`MIT`、`2026`。

---

## 3. 来源优先级（白名单，按这个顺序抓）

> ⚠️ 下表是 **v1 写作时（2026-11）核到的种子**，不是权威清单。**每次运行都要重新确认它还在、许可没变**——这正是本协议存在的意义。

| 级别 | 来源 | 抓什么 | 备注 |
|---|---|---|---|
| **A** | `remotion.dev/docs/ai/skills` + 官方 skills 仓库（`npx skills add remotion-dev/skills`） | 官方推荐的 agent 写法与示例组件 | 许可看仓库 LICENSE，商用注意 Remotion 自身授权 |
| **A** | `github.com/Vincentwei1021/video-talkcraft` | **108 张动效配方卡**（自包含 tsx + HTML demo），与本 skill 的 8 类几乎一一对应 | ⚠️ 许可 **PolyForm Noncommercial**：个人/教育/研究免费，**商业使用需作者授权**。商单成片不要直接搬代码，只读它的方法论（分镜格式、人脸安全区、排版预算） |
| **B** | `github.com/bozhouDev/video-skills-toolkit` | 爆款调研→转写→配音字幕→口播成片的 skill 链路 | 看仓库 LICENSE 再决定能否复用 |
| **B** | `github.com/vibe-motion/remotion-code-motion-explainer` | 代码/原理讲解类动效的导演 skill 写法 | 同上 |
| **C** | 社区文章（腾讯云开发者 / 知乎 / B 站专栏里「口播 + Remotion 叠加图表」这类实操贴） | 布局坐标、ffmpeg 合成参数、踩坑 | 文章里的代码片段**默认无授权声明** → 只借鉴思路，复制要标注来源 |
| **C** | skills 目录站（`skillsdirectory.com`、`mcpservers.org/agent-skills`） | 找同类 skill 交叉验证做法 | 仅作对比，不安装未审源的 skill |

**明确不看**：模板站付费素材（剪映模板 / AE 模板市场）、无 LICENSE 的个人仓库快照、需要登录才能拿的源码。

---

## 4. 四维评分卡（每个候选打分，≥7 分才进 `research-notes.md`）

| 维度 | 满分 | 判据 |
|---|---|---|
| **能跑** | 3 | 有完整可复制片段（3）/ 只有截图无代码（1）/ 只有标题（0） |
| **许可** | 2 | MIT/Apache-2.0/0BSD（2）；CC-BY 需署名（1）；Noncommercial/无许可/不明（0，**直接淘汰商用场景**） |
| **引擎匹配** | 2 | 目标引擎原生（2）；同框架可移植（1）；别的框架/AE/剪映（0） |
| **迁移成本** | 1 | 改 3 行内（1）；要重写数据接口（0.5）；依赖一堆外部资源（0） |

**许可分 = 0 时**：商单一律不许采用，个人项目采用必须在 `research-notes.md` 里写明「非商业许可，仅限学习/个人发布」。

---

## 5. 落盘格式（`research-notes.md`，每个候选一段）

```markdown
## 候选 #2 · bar-chart 对比柱图
- 来源：https://github.com/<owner>/<repo>/<path>
- 许可：MIT（已在页面确认，2026-11-12）
- 引擎：Remotion 4.x ｜ 评分：能跑 3 + 许可 2 + 引擎 2 + 迁移 1 = 8 ✅
- 最小片段：见下（复制进 src/components/BarChart.tsx）
- 迁移要改：① 数据从 props 换成本卡 keywords ② 颜色换成本片风格档
- 已知坑：<一句话>
```

**抓不到 3 个候选时怎么办**（常见，别慌）：

1. 换英文检索词再试 2 次（英文社区密度约为中文 3 倍）；
2. 仍不足 → **降级**：用 `animation-brief.md` 每类自带的「内置最小实现」（纯 CSS/GSAP，无外部依赖），并在 `overlay-spec.json` 的 `warnings` 里追加一条「内置实现，未采用社区代码」；
3. **绝对禁止**：把搜到的代码改个变量名就声称是自己写的；也禁止「凭印象」写一个根本没抓到的库的名字。

---

## 6. 联网动作怎么做（给 agent 的具体指令）

```bash
# 1) 有浏览器/抓取工具就用你自己的；没有就用这条兜底（不装任何东西）
python3 - <<'PY'
import urllib.request
url = "https://raw.githubusercontent.com/<owner>/<repo>/main/README.md"
print(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"}), timeout=15).read()[:4000].decode("utf-8","replace"))
PY

# 2) 拿 LICENSE 再确认一次许可（别看网页文案，看文件）
#    https://raw.githubusercontent.com/<owner>/<repo>/main/LICENSE
```

**抓取纪律**：

- 只抓 `raw.githubusercontent.com` / 官方文档域名 / 用户给的参考链接，不爬全站；
- 每个 URL 最多抓 1 次，失败就换候选，不重试超过 2 次；
- 抓到的代码**先进 `research-notes.md`，再进 `src/`**，顺序不能反（保证可追溯）。

---

## 7. 什么时候停止检索

满足任一即停：

- ✅ 8 类动画里 ≥6 类有可用实现；
- ✅ 累计已搜 8 次 / 抓 4 次；
- ✅ 用户说「先出一版看看」；
- ✅ 已连续 3 次搜不到相关结果（说明这类动效社区确实没有，直接内置实现 + 如实告知）。

停下来时必须在交付说明里写：**本次搜了几次 / 命中几个 / 哪些类走了内置实现**。
