# WorkBuddy 每日积分自动领取 —— 上手与演示说明

一句话：**一条命令，把 WorkBuddy 每天白送的积分领完（签到 100 分 + 猫猫旅行 + 盲盒）。**

- 不需要装任何第三方库（纯 Python 标准库）
- 不模拟点击、不控制浏览器，直接调官方接口
- Windows / macOS / Linux 都能跑
- 包里**不含任何账号凭据**，只在你自己的电脑上读你自己的登录态

---

## 一、30 秒上手

### macOS / Linux

```bash
cd workbuddy-daily-credits
python3 scripts/wb_credits.py --dry-run    # 先预览，不改任何数据
python3 scripts/wb_credits.py              # 真跑
```

### Windows（PowerShell）

```powershell
cd workbuddy-daily-credits

# 用 WorkBuddy 自带的 Python（把版本号换成你机器上实际有的）
& "$env:USERPROFILE\.workbuddy\binaries\python\versions\3.13.12\python.exe" scripts\wb_credits.py --dry-run
& "$env:USERPROFILE\.workbuddy\binaries\python\versions\3.13.12\python.exe" scripts\wb_credits.py
```

> 不知道自带 Python 装在哪？在 PowerShell 里跑：
> `Get-ChildItem "$env:USERPROFILE\.workbuddy\binaries\python\versions" -Directory`

### 期望看到什么

```
== WorkBuddy 每日积分 ==
① 签到：今日已签到，无需重复打卡
② 猫猫：状态 idle｜今日派遣次数已用完，跳过派遣
③ 盲盒：能量 5 / 每次 10，不够开一次，未开箱
----------------------------------------
积分余额：1800｜连续登录：18 天｜今日已签到：True
```

三条都对上了，就说明跑通了。

---

## 二、（可选）装成 WorkBuddy 技能，让它自己每天跑

1. 把整个 `workbuddy-daily-credits` 文件夹放进技能目录：
   - macOS / Linux：`~/.workbuddy/skills/`
   - Windows：`%USERPROFILE%\.workbuddy\skills\`
2. 在对话里说一句：
   > 每天早上 8:30 和晚上 18:30，跑一下 workbuddy-daily-credits，然后告诉我积分情况
3. 它会自动建成两条定时任务。

**为什么要两次？** 猫猫出门要 1–4 小时才回来。早上派出去，晚上才有得领。只跑一次也能拿到积分，只是"领回到期奖励"这一步会拖到第二天。

---

## 三、拍视频可以这么走（约 2 分钟）

| 段落 | 画面 | 口播要点 |
|---|---|---|
| 0–15s 痛点 | 打开成长中心，手指点三下：签到、派猫猫、开盲盒 | "这三下，每天都要点，忙起来就断签了" |
| 15–35s 准备 | 展示文件夹结构，指出 `SKILL.md` 和 `scripts/wb_credits.py` | "不用装环境，Python 自带就够；也没碰浏览器" |
| 35–60s 先预览 | 跑 `--dry-run` | "先只看不动手，确认它要干什么" |
| 60–100s 真跑 | 跑正式命令，屏幕滚动出三段结果 | "签到、派猫猫、开盲盒，一条命令三件事；能量不够它会自己停手" |
| 100–120s 收尾 | 展示 `config.json` 或定时任务 | "设一次，以后每天自己跑；改开箱上限改这一个数字" |

**演示时最好踩到的点（观众最爱看）**：

- 连跑两次，第二次显示"今日已签到"——证明幂等，不会重复领、不会报错。
- 能量不足时显示"不够开一次，未开箱"——证明它不瞎点。
- 断网或没登录时，它会明确报错而不是假装成功——这条最能建立信任。

---

## 四、常见问题

| 现象 | 原因 | 怎么办 |
|---|---|---|
| `登录态不可用` / `无法解密 accessToken` | 客户端没登录，或 macOS 上新版本把 token 加密了 | 先确认客户端是登录状态；Mac 还是不行，用 `scripts/web_auth.py` 走一次性网页授权（见 SKILL.md 第七节） |
| `python3: command not found` | Windows 没装 Python 或没加 PATH | 用 WorkBuddy 自带 Python 的完整路径（见上文） |
| `开箱失败：HTTP 400/403` | 能量不足、或当日开箱上限已到、或接口微调 | 脚本会打印原始报文，按提示隔天再试；持续失败说明接口变了 |
| 积分没涨 | 当天签到已领过（100 分每天只有一次） | 看"连续登录天数"是否 +1，别只看余额 |

---

## 五、必须知道的两件事

1. **这是对你自己的账号做自动化**。用的是你自己客户端的登录态，性质和你手点一样，但仍属于自动化操作；如果哪天官方收紧，出现限权或积分回收是有可能的。建议每天只跑 1–2 次，别做高频轮询。
2. **别把 zip 里的东西和你的 token 一起发出去**。包里本身不含凭据，但如果你在本机跑过之后又打包，注意不要顺手带上 `.profile/`、`checkin-cred.json` 这类文件。
