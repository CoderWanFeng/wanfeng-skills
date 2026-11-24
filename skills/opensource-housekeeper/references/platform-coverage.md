# 全平台开源项目检索清单（找项目专用）

> **这份文件只管「找」**。
> 「找项目」= 国内外所有主流开源平台**全覆盖**；
> 「发布项目」= 仍以 GitHub / AtomGit / Gitee 三家为主推（要注册、要凭证），见 [platform-comparison.md](platform-comparison.md)。
> 两件事不要混淆：用户只说「找点 AI 项目」时，**绝不追问账号、绝不只搜一家**。

## 一句话原则

用户选完「今天想找哪方面的 AI 项目」之后，AI 要按本清单**逐平台检索 → 记录每个平台「已搜 / 跳过及原因」 → 去重 → 筛 Top 3 → 标来源平台**，
最后用人话呈现（模板见 SKILL.md 的 Step A0.4）。**一个平台都不许默默漏掉**。

## 平台总览

| 圈层 | 平台 | 域名 | 找什么最划算 |
|---|---|---|---|
| 国际代码托管 | GitHub | github.com | 全方向，项目最全 |
| 国际代码托管 | GitLab | gitlab.com | 全方向，企业 / 自建实例项目 |
| 国际代码托管 | Codeberg | codeberg.org | 轻量工具、隐私向项目 |
| 国际代码托管 | Bitbucket | bitbucket.org | 老项目、Atlassian 生态 |
| 国际代码托管 | SourceForge | sourceforge.net | 老牌桌面软件 / 工具 |
| 国际 AI 专属 | Hugging Face | huggingface.co | 模型、Spaces 演示、数据集 |
| 国内代码托管 | **AtomGit** | atomgit.com | 国产生态、鸿蒙 / openEuler、国产 AI |
| 国内代码托管 | **Gitee 码云** | gitee.com | 国内个人项目、中文 README、GitHub 同步仓 |
| 国内代码托管 | **GitCode** | gitcode.com | AI 项目、CSDN 社区项目 |
| 国内代码托管 | **GitLink** | gitlink.org.cn | 高校 / 科研 / 国产开源 |
| 国内代码托管 | CODING | coding.net | 补充发现 |
| 国内代码托管 | 开源中国 OSChina | oschina.net | 项目收录、中文资讯、找线索 |
| 国内 AI 专属 | **魔搭 ModelScope** | modelscope.cn | 国产模型、配套工具 |
| 国内 AI 专属 | **启智 OpenI** | openi.cn | 科研 AI、算力平台配套项目 |
| 国内 AI 专属 | **飞桨 AI Studio / PaddlePaddle** | aistudio.baidu.com / gitee.com/paddlepaddle | 中文 NLP / CV、产业项目 |
| 国内 AI 专属 | 始智 AI wisemodel | wisemodel.cn | 国产模型社区，补充发现 |

---

## 分组详表（含检索入口）

`{K}` = 关键词（方向映射见 SKILL.md Step A0.1）。**检索入口以站点当前 UI 为准**；路径变了就用站内搜索或 `WebSearch` 的 `site:域名 {K}` 兜底。

### A. 国际代码托管

| 平台 | 检索入口 | 开放 API | 是否需登录 | 国内网络 | 备注 |
|---|---|---|---|---|---|
| GitHub | `https://github.com/search?q={K}&type=repositories` | `https://api.github.com/search/repositories?q={K}&sort=stars&per_page=10` | 否（API 有频率限制） | 常不稳 | 网页搜索常被拦，**优先用 API** |
| GitLab | `https://gitlab.com/search?search={K}` | `https://gitlab.com/api/v4/search?scope=projects&search={K}&per_page=10` | **API 需 token** | 一般 | 实测 401 / 403 → 用 `site:gitlab.com {K}` 补 |
| Codeberg | `https://codeberg.org/explore/repos?q={K}` | `https://codeberg.org/api/v1/repos/search?q={K}&limit=10` | 否 | 一般 | API 易 429 限流 → 优先网页入口 |
| Bitbucket | `https://bitbucket.org/repo/all?search={K}` | 2.0 API 多需认证 | 部分 | 一般 | 老项目多，补充发现 |
| SourceForge | `https://sourceforge.net/directory/?q={K}` | — | 否 | 一般 | 可能 403 → 用 `site:sourceforge.net {K}` 补 |

### B. 国际 AI 专属

| 平台 | 检索入口 | 开放 API | 是否需登录 | 国内网络 | 备注 |
|---|---|---|---|---|---|
| Hugging Face | `https://huggingface.co/models?search={K}`<br>`https://huggingface.co/spaces?search={K}` | `https://huggingface.co/api/models?search={K}&limit=10`<br>`https://huggingface.co/api/spaces?search={K}&limit=10` | 否 | **常连不上** | 连不上就用 `WebSearch` 补；模型权重 ≠ 可装软件项目，要标注清楚 |

### C. 国内代码托管（重点，国内用户 clone 更快）

| 平台 | 检索入口 | 是否需登录 | 国内网络 | 备注 |
|---|---|---|---|---|
| **AtomGit** | `https://atomgit.com/search?q={K}` | 否 | ✅ 顺畅 | 国产生态、鸿蒙 / openEuler 项目集中 |
| **Gitee 码云** | `https://search.gitee.com/?skin=rec&type=repository&q={K}` | 否 | ✅ 顺畅 | 大量 GitHub 同步仓，去重时留意 |
| **GitCode** | `https://gitcode.com/search?q={K}` | 否 | ✅ 顺畅 | CSDN 旗下，AI 项目密度高 |
| **GitLink** | `https://www.gitlink.org.cn/search?keyword={K}` | 否 | ✅ 顺畅 | CCF 开源生态、高校科研项目 |
| CODING | 站内检索 / `site:coding.net {K}` | 部分 | ✅ 顺畅 | 补充发现 |
| 开源中国 OSChina | `https://www.oschina.net/search?q={K}&scope=project`<br>`https://www.oschina.net/project` | 否 | ✅ 顺畅 | 找线索、看中文介绍最方便 |

### D. 国内 AI 专属

| 平台 | 检索入口 | 是否需登录 | 国内网络 | 备注 |
|---|---|---|---|---|
| **魔搭 ModelScope** | `https://modelscope.cn/search?search={K}`<br>`https://modelscope.cn/models?name={K}` | 否 | ✅ 顺畅 | ⚠️ 旧 `api/v1/models?Name=` 已 404，别再用 |
| **启智 OpenI** | `https://openi.cn/search?keyword={K}` | 否 | ✅ 顺畅 | 科研 AI 项目 |
| **飞桨 AI Studio** | `https://aistudio.baidu.com/aistudio/projectoverview?keyword={K}` | 否 | ✅ 顺畅 | 项目多为 Notebook；代码仓看 `gitee.com/paddlepaddle`、`github.com/PaddlePaddle` |
| 始智 AI wisemodel | `https://www.wisemodel.cn/` + 站内检索 | 否 | ✅ 顺畅 | 补充发现 |

### E. 榜单 / 聚合发现（用户说「今天啥火」时优先跑）

| 渠道 | 入口 | 说明 |
|---|---|---|
| GitHub Trending | `https://github.com/trending` | 日 / 周榜，按语言筛 |
| GitHub Topics | `https://github.com/topics/{topic}` | 按主题聚合 |
| Hugging Face Trending | `https://huggingface.co/models?sort=trending` | 模型热度榜 |
| Gitee / GitCode / AtomGit 站内榜单 | 各站「推荐 / 热门 / 探索」页 | 入口以站点当前 UI 为准 |
| OSChina 项目库 | `https://www.oschina.net/project` | 中文项目收录 |
| `awesome-{方向}` 清单 | 各平台搜 `awesome-{K}` | 一个清单能带出十几个同类项目 |

---

## 方向 → 优先平台（不用问用户，AI 自己定）

| Step 00 方向 | 优先跑的平台（其余平台仍要覆盖） |
|---|---|
| 1 AI 编程 | GitHub、GitCode、AtomGit、GitLab |
| 2 AI 画图 / 视频 / 音频 | GitHub、Hugging Face Spaces、ModelScope、GitCode |
| 3 本地跑大模型 | GitHub、Hugging Face、ModelScope、wisemodel、Gitee（同步仓） |
| 4 AI Agent / 工作流 | GitHub、GitCode、AtomGit、Gitee |
| 5 AI 办公 | Gitee、GitCode、OSChina、GitHub |
| 6 AI 搜索 / 知识库 / RAG | GitHub、Gitee、GitCode、ModelScope |
| 7 AI 建站 / 前端 / 小工具 | GitHub、Codeberg、Gitee |
| 8 今日热门 | 各平台 Trending / Topics + OSChina 项目库 |

---

## 检索 SOP（Step A0 / Step A3.2 共用）

```text
1. 关键词：方向 → 中英各一组（Step A0.1）；用户给了名字就直接用原名 + 同义词
2. 逐圈层检索：A 国际代码 → B 国际 AI → C 国内代码 → D 国内 AI → E 榜单
   每个平台至少 1 次；优先 WebSearch / WebFetch 的 site: 过滤，curl 开放 API / 网页兜底
3. 记录台账：平台名 | 已搜 / 跳过 | 跳过原因 | 命中数
4. 汇总字段：项目名、来源平台、原始地址、Star/热度、最近更新、一句话人话、
             国内镜像地址、是否需 GPU / 付费、是否中文 README
5. 去重：同一项目的多平台镜像合并为 1 条，镜像地址留作 clone 备选
6. 筛选：剔除 Star<50、2 年未更新、无 README、纯搬运、闭源收费项
7. 排序：热度 + 新鲜度 + 描述匹配 + 小白友好度；Top 3 至少 1 国际 + 1 国内
8. 呈现：SKILL.md Step A0.4 模板（必须写「本次覆盖 / 跳过」）
```

**每个候选必须带「来源平台」**。用户看到的不是一坨链接，而是「从哪找来的、为什么值得看」。

## 去重 & 可信度

| 情形 | 处理 |
|---|---|
| GitHub 原仓 + Gitee / AtomGit / GitCode 同步仓 | 合并成 1 条，备注「国内也有镜像，clone 更快」，镜像地址留给 Step A2 |
| 同一项目多个 `awesome` 清单反复出现 | 只计 1 条，但可作为「社区认可度」加分 |
| 模型权重 / Notebook / 演示 Demo（HF、ModelScope、AI Studio） | 标注「不是可直接装来跑的软件项目」，不混进主候选 |
| 平台自家的「推荐位」项目 | 可作为热度参考，不自动加分 |
| 明确闭源、免费但非开源、需付费 API 才能用 | 剔除或明确标注，别让小白白装一遍 |

排序权重：⭐ Star / 热度（高）> 描述匹配度（高）> 最近更新（中）> 跨圈层多样性（中）> 国内可直连（中）> 有中文 README / Quick Start（中）。

## 实测可达性（2026-11）

> 用 `curl -s -o /dev/null -w "%{http_code}" -L --max-time 8` 探测，结果仅代表当时网络；
> **任何非 2xx 都改用 `WebSearch` 的 `site:域名 {K}` 补，不许判「这个平台没有」**。

| 入口 | 状态 | 结论 |
|---|---|---|
| `api.github.com/search/repositories` | 200 | ✅ 主力，免登录 |
| `github.com/search?...` | 000 | 网页搜索被拦 → 用 API |
| `gitlab.com/api/v4/search` | 401 | 需 token → 用 site: 搜索补 |
| `gitlab.com/search?search=` | 403 | 反爬 → 用 site: 搜索补 |
| `codeberg.org/api/v1/repos/search` | 429 | 限流 → 降速 / 用网页入口 |
| `codeberg.org/explore/repos?q=` | 200 | ✅ 可用 |
| `huggingface.co/api/models` / `spaces?search=` | 000 | 国内常连不上 → 用 WebSearch 补 |
| `atomgit.com/search?q=` | 200 | ✅ 可用 |
| `search.gitee.com/?...&q=` | 200 | ✅ 可用 |
| `gitcode.com/search?q=` | 200 | ✅ 可用 |
| `gitlink.org.cn/search?keyword=` | 200 | ✅ 可用 |
| `oschina.net/search?q=&scope=project` | 200 | ✅ 可用 |
| `modelscope.cn/api/v1/models?Name=` | 404 | ❌ 已失效，别再用 |
| `modelscope.cn/search?search=` / `models?name=` | 200 | ✅ 可用 |
| `openi.cn/search?keyword=` | 200 | ✅ 可用 |
| `aistudio.baidu.com/aistudio/projectoverview?keyword=` | 200 | ✅ 可用 |
| `wisemodel.cn` / `coding.net` / `gitlink.org.cn` 主页 | 200 | ✅ 可达 |

## 常见坑

1. **国内平台的「同步仓」不等于原仓**：Star 数、更新时间都可能滞后，判断项目活不活跃要看原仓。
2. **AI 社区里大量是模型 / Notebook，不是软件**：别把「下载一个模型」当成「装好一个项目」，要在候选里写清楚。
3. **GitHub 搜得到 ≠ 拉得动**：搜索阶段不用镜像，clone 阶段才按 SKILL.md Step A2 切 `ghfast.top` 等镜像。
4. **别只看 Star**：Star 高但 3 年没更新的项目，对小白是坑；优先有 Quick Start、有中文 README 的。
5. **闭源「免费 AI 工具」不算开源项目**：用户要的是能拉下来、能改、能自己跑的东西，混进来会白忙一场。

## 失败兜底

| 症状 | 处理 |
|---|---|
| `401` / `403` | 需登录或反爬 → `WebSearch site:域名 {K}` 补齐，台账标「网页不可达，已用搜索补」 |
| `429` | 限流 → 平台间隔 ≥ 0.5s 串行、换网页入口 |
| `000` / 超时 | 网络不通 → WebSearch 补 + 优先换国内同类平台 |
| 所有结果都是同一个项目的镜像 | 合并后换同义词 / 英文关键词再搜一轮 |
| 全部平台都找不到 | 走 SKILL.md Step A0.5：换关键词 / 给文章链接 / 看今日榜单，三条出路都要给 |
| 只找到闭源或付费项目 | 如实说明「这个方向目前开源方案少」，并给最接近的开源替代 |

## 维护约定

新增平台时，**三处要同步改**：
1. 本文件（总览表 + 分组详表 + 实测可达性）；
2. `SKILL.md` 的 **Step 00 开场白**里那一句平台清单；
3. `SKILL.md` 的 **Step A0.2 最低覆盖要求**表 + **Step A3.2** 的 `curl` 模板。

不要只在某一处加，否则会出现「开场说全平台、实际只搜三家」的自相矛盾。
