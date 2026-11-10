---
name: workbuddy-daily-credits
display_name: WorkBuddy 每日积分自动领取（签到+猫猫+盲盒）
display_name_en: WorkBuddy Daily Credits (check-in · Buddy travel · blind box)
description: "一键跑完 WorkBuddy 成长中心每天的免费积分：Buddy 加油站签到（每日 100 积分）、派猫猫（Buddy）去旅行并领回到期奖励、能量够时自动开盲盒。跨平台 Windows / macOS / Linux，纯 Python 标准库，读本机登录态直调官方接口，不模拟点击、不碰浏览器。触发词：WorkBuddy 签到、领积分、Buddy 加油站、派猫猫、派 Buddy 去旅行、喵喵旅行、开盲盒、能量、自动领积分、每日积分、积分不够、断签。"
description_en: "Runs the daily WorkBuddy growth-center freebies in one command: Buddy Station check-in (100 credits/day), dispatch & claim Buddy travel rewards, and open blind boxes when energy allows. Cross-platform, stdlib-only, uses the local login state to call official endpoints directly — no clicking, no browser automation."
category: automation
version: 1.0.0
license: MIT-0
metadata:
  openclaw:
    emoji: "💰"
    requires:
      bins:
        - python3
      os:
        - windows
        - darwin
        - linux
allowed-tools: Bash
---

# WorkBuddy 每日积分自动领取

一条命令跑完三件事，跨 Windows / macOS / Linux：

| # | 做什么 | 背后的接口 | 幂等性 |
|---|---|---|---|
| ① | Buddy 加油站签到（每日本 100 积分） | `POST /v2/billing/meter/daily-checkin` | 幂等，当天已签返回"已签到"，不重复发 |
| ② | 派猫猫（Buddy）旅行 | 先 `POST .../travel/claim` 领，再 `POST .../travel/depart` 派 | 到达奖励一直挂着，不会被扣掉 |
| ③ | 开盲盒 | `GET /activity/growth/energy` → `POST /activity/growth/buddy/open` | 能量不足不发写请求 |

> **为什么不用模拟点击**：成长中心本身就是 `workbuddy.cn` 的网页，客户端只是用带登录态的 webview 打开它。走接口比点界面稳，也不会因为页面改版而失效。

---

## 一、何时使用

用户说这些话时用它：

- **签到类**：帮我签到、自动签到、每日签到、打卡、领今天的积分、领那 100 积分
- **猫猫类**：派猫猫、派 Buddy 去旅行、猫猫回来了吗、领旅行奖励
- **盲盒类**：开盲盒、能量够不够、抽一下
- **综合**：每天的积分任务做了吗、帮我把 WorkBuddy 积分领了、以后每天自动领

---

## 二、前置条件

1. **WorkBuddy 客户端已登录**（装了、用着就行，脚本自己去找登录态文件）。
2. **Python 3.8+**。
   - macOS / Linux：系统自带 `python3`。
   - Windows：用 WorkBuddy 自带的 Python，路径形如
     `%USERPROFILE%\.workbuddy\binaries\python\versions\<版本>\python.exe`；
     或者自己装一个 Python 3，装的时候勾选 "Add python.exe to PATH"。
3. 首次使用建议先 `--dry-run` 看一眼（只读，不改任何数据）。

---

## 三、命令

在技能目录下执行（`<技能目录>` 换成你解压的位置）：

```bash
# ① 预览：只读，不提交任何写请求
python3 scripts/wb_credits.py --dry-run

# ② 真跑：签到 + 猫猫 + 盲盒
python3 scripts/wb_credits.py

# ③ 只看，不动手
python3 scripts/wb_credits.py --dry-run --no-box

# ④ 机器可读（给定时任务/二次开发用）
python3 scripts/wb_credits.py --json
```

Windows（PowerShell）把 `python3` 换成具体路径，例如：

```powershell
& "$env:USERPROFILE\.workbuddy\binaries\python\versions\3.13.12\python.exe" scripts\wb_credits.py
```

### 参数

| 参数 | 作用 |
|---|---|
| `--dry-run` | 预览模式：只查询、不提交任何写请求 |
| `--no-box` | 跳过盲盒（只做签到 + 猫猫） |
| `--max-box N` | 本次最多开 N 个盲盒（默认取 `config.json` 的 `max_box_per_run`） |
| `--channel auto\|local\|web` | 登录态通道，默认 `auto` |
| `--config <路径>` | 指定配置文件 |
| `--json` | 输出 JSON（含 checkin / travel / blindbox / summary 四段） |

### 输出示例

```
== WorkBuddy 每日积分 ==
① 签到：今日已签到，无需重复打卡
② 猫猫：状态 idle｜今日派遣次数已用完，跳过派遣
③ 盲盒：能量 5 / 每次 10，不够开一次，未开箱
----------------------------------------
积分余额：1800｜连续登录：18 天｜今日已签到：True
```

---

## 四、改成每天自动跑

用宿主（WorkBuddy / CodeBuddy）的**定时任务 / 自动化**功能，每天跑两次：

- **早上一次**：签到 + 派猫猫出门
- **晚上一次**：领回已到达的旅行奖励（猫在路 1–4 小时，单次跑不到"领取"这一步）

给自动化写这句话就够了（路径按实际改）：

> 每天 8:30 和 18:30，执行
> `python3 <技能目录>/scripts/wb_credits.py`，
> 然后用中文简报：积分余额、签到结果、连续登录天数、猫猫状态、能量、盲盒结果。
> 报错就如实说原因，不要编造数字。

两条任务共用同一条命令是安全的：签到幂等，旅行"到达未领"会一直等你下次来领。

---

## 五、安全边界

- **只读登录态**：读本机 `workbuddy-desktop.info`（macOS 需解密），**绝不打印、绝不上传** token。
- **写操作只有三个接口**：签到、旅行领取、旅行派出、开盲盒。不碰兑换、抽奖、支付。
- **能量护栏**：`能量 < 单次成本` 时直接返回，不发送任何开箱请求。单次开箱上限默认 2 个。
- **不修改任何文件**，不写注册表，不留后台进程。

## 六、已知限制

1. **开箱收益无法预先保证**：能开出什么由服务端决定，脚本只负责"点"。
2. **成长计划里的任务不能代做**（体验某专家、关注公众号、用模板等）：没有对应接口，只能人工点。
3. **断签要靠对话**：官方规则是"当天完成过一次对话才算记录一天"，脚本只负责签到那 100 分，不代聊。
4. **收益规则随时可能被官方调整**，字段做了容错，取不到就如实报错，不会编造。
5. 仅作用于**你自己的账号**，不含批量/多账号能力。

---

## 七、目录结构

```
workbuddy-daily-credits/
├── SKILL.md                     # 本文件：技能说明（必需）
├── README.md                    # 给第一次用的人：3 步上手 + 演示流程
├── config.json                  # 可选配置（关掉某项、改开箱上限）
├── scripts/
│   ├── wb_credits.py            # 唯一入口：签到 + 猫猫 + 盲盒
│   ├── buddy_station.py         # 登录态解密 + 接口封装（来自 WorkBuddy积分助手，MIT-0）
│   └── web_auth.py              # 备用：macOS 无法本地解密时的一次性网页授权
└── templates/
    └── auth-snippet.js          # 备用：网页授权要在浏览器控制台粘贴的那段 JS
```

**正常情况只需要 `wb_credits.py` + `buddy_station.py`**。`web_auth.py` 和 `auth-snippet.js` 是 Mac 上万一提示"无法解密登录态"时的兜底，Windows 基本用不到。

### 备用通道怎么用（macOS 提示凭据不可用时）

```bash
python3 scripts/web_auth.py --snippet      # 生成授权片段
# 按提示到浏览器控制台粘贴 → 拿到 WBAUTH1: 开头的授权码
python3 scripts/web_auth.py --setup-code "WBAUTH1:..."
```

具体参数以 `python3 scripts/web_auth.py --help` 为准。

---

## 八、许可与致谢

`scripts/buddy_station.py`、`scripts/web_auth.py`、`templates/auth-snippet.js` 来自开源技能
**WorkBuddy积分助手（totorosir-workbuddy-score，作者 totorosir，MIT-0 许可）**，
本包在其基础上增加了统一的盲盒入口与跨平台使用说明。
