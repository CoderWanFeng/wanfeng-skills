# 品牌 Logo 自动采集规范 · brand-logo.md

> **适用范围**：mograph-pro 的 **Step A2-2**（配图采集之后、切场景表之前）。
> **一句话**：**口播里点了哪个品牌的名字，就自动去下载那个品牌的官方 logo，用进成片画面里。**
>
> 用户不用找图、不用给链接、也不用问「这个 logo 在哪」——提到品牌的地方，logo 自己长出来。

---

## 0. 这份文档管什么、不管什么

| 文档 | 管的是 | 什么时候看 |
|---|---|---|
| `visual-assets.md` | **配图**：截图 / 找图 / 标注 / 素材台账 | Step A2 |
| `wanfeng-cover.md` | **封面 logo**：Step H 换皮时挂的那个 logo | Step H |
| **本文件** | **成片画面里的品牌 logo**：识别 → 取件 → 上屏 → 兜底 | Step A2-2 |

**封面 logo 与画面 logo 是两件事，但标准一致**：

- 封面用 `scripts/get_logo.py`（按 URL 取件），画面用 `scripts/brand_logo.py`（按**品牌名**自动找源）；
- 两边共用同一个准确性标准（W18 三关）和同一份台账（W15）；
- 同一个品牌只取一次件，封面与画面**共用同一个 PNG 文件**（放 `assets/logos/<品牌>.png`），不要下两遍。

---

## 1. 什么时候做这一步

命中任意一条就做：

- 口播稿 / SRT 里点名了品牌（GLM、MiniMax、WorkBuddy、Hy4-Flash、腾讯云、飞书…）；
- 用户说「提到 XX 的时候把它的 logo 放上去」「这个产品要有 logo」；
- 本片是产品介绍 / 对比 / 推荐类内容。

**不做的情况**：

- 只说了泛称（「大模型」「某个工具」「这个软件」）——那不是品牌，不许挂 logo；
- 品牌已经以截图形式出现在配图里——不要再叠一个 logo 上去（重复且挡内容）；
- 只是封面要 logo——那是 Step H 的事，走 `wanfeng-cover.md`。

---

## 2. 三步流程

### 2.1 ① 扫出候选品牌（离线，不联网）

```bash
~/.workbuddy/binaries/python/envs/default/bin/python3 \
  skills/mograph-pro/scripts/brand_scan.py \
  --script "<选题>/口播稿.md" \
  --out "<选题>/mograph-task/品牌候选.md" \
  --assets-dir "<选题>/mograph-task/assets/logos"
```

扫出的是**候选**，不是结论。表格里每行给：出现次数 / 首现句 / 置信度 / 判据 / 本地是否已有 logo。

| 置信度 | 含义 | 你要做的判断 |
|---|---|---|
| 高 | 引号包裹 + 产品名形态 + 上下文动词 | 基本可以当品牌用，仍要确认是哪个品牌 |
| 中 | 形态像品牌，但只出现过一次 | 看首现句是不是真在讲这个产品 |
| 低 | 只有一个弱信号 | 默认**不用**，除非 Agent 人工确认 |

**中文品牌名扫不出来是正常的**（「腾讯云」不带引号时无法与普通名词区分）。
两种补法：

```bash
# ① 扫描时手工补（推荐，一次说全）
python3 scripts/brand_scan.py --script 口播稿.md --add 腾讯云 --add 通义千问
# ② 直接跳过扫描，手工补进取件命令的 --brand
```

**已在本地的 logo 优先用**：`--assets-dir` 标了「本地已有」的，直接复用本地文件，不重新下载。

### 2.2 ② 取官方 logo（唯一联网的一步）

```bash
~/.workbuddy/binaries/python/envs/default/bin/python3 \
  skills/mograph-pro/scripts/brand_logo.py \
  --brand GLM --site https://glm.cn \
  --out "<选题>/mograph-task/assets/logos/GLM.png" \
  --manifest "<选题>/mograph-task/assets/asset-manifest.json" \
  --segment "第 12 句「我用的是 GLM」"
```

**来源按权威度选**（脚本一次只吃一个来源，先 `--dry-run` 看候选再决定）：

| 来源 | 命令 | 官方性 | 说明 |
|---|---|---|---|
| 官方直链 | `--url "https://cdn.../glm.svg"` | 看域名 | 用户给的 CDN / GitHub raw；给了 `--site` 时脚本会比对域名 |
| **品牌官网** | `--site https://glm.cn` | **同域 = 官方** | 脚本扒 `og:logo` → `apple-touch-icon` → `favicon` → `og:image`，按权威度依次尝试 |
| Wikimedia Commons | `--commons` | **不是官方源** | 次选，必须人工确认是官方件 |
| GitHub 仓库 | `--repo owner/repo` | **不是官方源** | 取组织头像，次选，必须人工确认 |

脚本已做：SVG 转 PNG（cairosvg → sips → qlmanage）→ 白底转透明 → 裁留白 → 缩放 → 登记台账。

**退出码就是下一步指令**：

| 退出码 | 含义 | 你要做的 |
|---|---|---|
| 0 | 取到了 | 进 §2.3 上屏 |
| 2 | 参数错 | 补 `--url / --site / --commons / --repo` 之一 |
| 3 | 下载失败 | 换来源（直链 / 官网 / 另一个源），**不要反复重试同一地址** |
| 4 | 源图太小或格式不对 | 让用户给更高清的官方直链，或退纯文字（§4） |
| 6 | **没找到官方源** | **退成纯文字品牌名**（§4），不许拿近似 logo 硬凑 |

### 2.3 ③ 上屏：logo 往画面哪里放

三种档位，按这句口播的重要程度选。**默认用档 1**，不要一提到品牌就铺一张 logo 满屏。

#### 档 1 · 品牌角标（默认）

跟那句的卡片一起入场，标出「这里是 XX」。

| 项 | 规格 |
|---|---|
| 落点 | `fs` 场景放**标签行右侧**（与 `60,190` 那一行同高）；`overlay` 场景放**卡片右上角**内缩 24px |
| 尺寸 | icon 版式最长边 **≤120px**；lockup（横排整条）宽 **≤240px**、高 **≤72px** |
| 入场 | 随卡片一起淡入 + 上移 12px，**不单独飘、不单独转**（避免抢主效果） |
| 避让 | 右上有人头时改放**左上标签行**；任何情况下不遮圆头（W22）、不压正文 |

#### 档 2 · 品牌卡（这句就是在讲这个品牌）

单独一场 `overlay` 卡：logo（居中，最大边 ≤260px）+ 品牌名 + 一句结论。

- 走 `semantic-to-effect.md` §4 的 `hero_settle`（收尾落版）或 `beat_card`（短句卡点）；
- **一句一效果**：这一场别再叠别的基元，主效果只有一个。

#### 档 3 · 片尾聚合（可选）

本片出现 **≥2 个**品牌时，可在片尾 `hero_settle` 的 logo 位把品牌 logo 排一行。

- 只在片尾用一次；
- 品牌 ≤4 个，排不下就少排；
- 片尾已经有 WorkBuddy 图标之类的主标识时，不重复排。

#### 通用规则

| # | 规则 |
|---|---|
| 1 | 一句话里出现多个品牌 → **只上主品牌**（离这句中心最近的那个） |
| 2 | **每片 logo 上屏 ≤3 次**；超了就去掉次要的，保留第一次出现的那次 |
| 3 | logo 不叠 logo、不叠水印、不盖圆形人头、不压正文 |
| 4 | 横版按 `aspect-ratio.md` §4 的 `CANVAS` 换算落位，**不照抄竖版像素** |
| 5 | 上屏后回填台账：`used_at`（时间点）、`segments`（挂在哪句） |
| 6 | logo 只是**辅助标识**，不替代品牌名文字——观众看不清图也要认得出名字 |

---

## 3. 准确性三关（W26）

**与封面 logo 同一把尺子（W18），但视频内更容易翻车——观众盯着画面看的时间更长。**

| 关 | 判断 | 怎么判 |
|---|---|---|
| ① **是不是这个品牌** | 别把 A 公司的 logo 挂到 B 公司头上 | 看候选表的首现句；同名词条尤其要核对（"MiniMax" vs "MiniMax 智语"） |
| ② **是不是官方源** | 官网 / 官方 GitHub / 官方社媒 | `--site` 同域 = 官方；Commons / GitHub 头像 = **必须人工确认**；直链看域名 |
| ③ **是不是同一版本** | 别用旧 logo 代表新版产品 | 看官网当期 logo 与取到的是否一致；不一致就用当期的那一版 |

**三关任何一关不过就不许上屏。** 脚本只能帮你判第②关的一部分，第①③关是人的判断。

---

## 4. 兜底：取不到 / 不确定怎么办

按顺序降级，**不许跳级**：

1. **换成别的官方源再试一次**（官网 → 直链 → 官方 GitHub），每片最多试 3 个来源；
2. **退成纯文字品牌名**：用文字卡写「GLM」，不挂任何图标（**W18 / W26 的硬底线**）；
3. **什么都不放**：这一句按普通观点句处理，走 `beat_card`。

> **绝对不许**：拿相似 logo 凑、拿第三方博客扒的图凑、拿旧版本 logo 凑、
> 或者从别的品牌官网上扒一个长得差不多的图。**挂错 logo 是事实错误，比不好看严重得多。**

---

## 5. 台账登记（与配图共用一份表）

logo 也要进 `assets/asset-manifest.json`，字段与 `visual-assets.md` §6 一致：

```json
{
  "file": "logos/GLM.png",
  "used_at": [12.4],
  "segments": ["第 12 句「我用的是 GLM」"],
  "source": "web-logo",
  "url": "https://glm.cn/assets/logo.svg",
  "captured_at": "2026-11-27",
  "shows": "GLM 官方 logo（icon 版式）",
  "proves": "口播里点名 GLM 的那句",
  "license": "official-brand-asset",
  "logo_source_kind": "official-site"
}
```

- `shows` / `proves` 两栏是判据 1 的落地形式——**写不出 `proves` 的 logo，说明它不该出现在这条片子里**；
- `logo_source_kind` 是本文件新增的字段：`official-site` / `direct-url` / `commons` / `github-org`，
  后两种在交付说明里要写明「非官方源，人工确认过」。

---

## 6. 预算与上限

| 项 | 上限 |
|---|---|
| 候选扫描 | 每次全稿扫一遍，不逐句扫 |
| 取件来源尝试 | 每品牌 ≤3 个来源（官网 → 直链 → 另一个官方源） |
| 联网取件总数 | 每片 ≤5 个品牌 |
| logo 上屏次数 | 每片 ≤3 次 |
| 片尾聚合 | ≤4 个 logo，且只在片尾用一次 |

超预算时**先减 logo，不要减画面信息量**。

---

## 7. 交付前检查清单

- [ ] 每个上屏的 logo 都过了三关（是它 / 官方源 / 同一版本）
- [ ] 每个 logo 都在 `asset-manifest.json` 里有登记，`shows` 与 `proves` 都填了
- [ ] 静帧逐张 Read 过（Step C）：logo 清晰、不糊、不遮圆头、不压正文
- [ ] logo 上屏 ≤3 次，没有刷屏
- [ ] 取不到官方源的，**确实是纯文字**而不是近似 logo
- [ ] 交付说明里写了「片中有几处品牌 logo、来源是什么、哪几个是人工确认过的」

---

## 8. 相关文档

| 文件 | 内容 |
|---|---|
| `references/wanfeng-path.md` | 主规范（版式分层 §5.2 / 圆形人头 §5.3 / pill 配色 §5.7 / W 规则 §11） |
| `references/semantic-to-effect.md` | 效果基元库（`hero_settle` / `beat_card` / `card_stagger`） |
| `references/visual-assets.md` | 配图规范与台账字段（logo 与配图共用一份表） |
| `references/wanfeng-cover.md` | Step H 封面换皮的 logo |
| `references/aspect-ratio.md` | 画幅参数化与安全区（横版落位换算） |
