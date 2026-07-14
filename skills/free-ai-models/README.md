# free-ai-models · 维护说明

> **本文件给维护者看**——用户不会读这个。用户看 [SKILL.md](SKILL.md)。

---

## 维护职责

| 任务 | 频率 | 谁做 |
|---|---|---|
| 全量 WebFetch 重抓 | 每月 1 号 | 维护者（或 cron + AI 配合） |
| 新模型/新平台新增条目 | 出现即加 | 维护者 |
| 数据日期批量更新 | 每次抓取后 | AI 抓取时同步 |
| 失效活动标"⚠️ 已结束" | 即时 | AI / 维护者 |

---

## 数据基准日管理

- **每张表头**加 `数据日期：YYYY-MM-DD`
- **每个条目**的"修改日期"列 = `data_date`
- **超过 30 天**的数据 → 必须重抓才能继续用

---

## 新增平台的流程

1. 在合适的 `reference/*.md` 找对应类别
2. 写一条记录（含：平台、模型、额度、注册方式、国内可用、URL）
3. 标 `数据日期 = YYYY-MM-DD`
4. 在表头更新 `数据日期`
5. 同步更新 `README.md` 索引（如果新增了 reference 文件）

---

## WebFetch 自动化的建议

> 目前靠 AI 手动触发。可以用 cron 跑：

```bash
# 每月 1 号 0:00 跑一次
0 0 1 * * /usr/local/bin/free-ai-models-monthly-update.sh
```

**脚本伪代码**：

```bash
#!/bin/bash
URLS=$(grep -oE 'https?://[^ )]+' /Users/wanfeng/code/wanfeng-skills/skills/free-ai-models/reference/*.md | sort -u)

for URL in $URLS; do
  echo "===== Checking $URL ====="
  # 调 AI 抓取 + 判断 + 更新
  # 实际实现可以用 claude / openai / 本地 LLM
done
```

---

## 关键约束

- **不污染数据**：WebFetch 抓不到准确信息时，宁可不更新本地
- **不引战**：不比较"哪个模型最强"，只列客观数据
- **不卖课**：不推荐任何付费训练营 / 课程
- **不教绕过付费墙**：只列"官方提供"的部分
- **国内/海外分开**：让用户一眼能看到"国内能不能用"

---

## 数据准确性自检

> 维护者每月 1 号跑这个清单：

- [ ] 30 天前的数据全部 WebFetch 过
- [ ] 标"⚠️ 已结束"的活动确实结束了
- [ ] 新出现的模型/平台已加入
- [ ] 失效的平台/模型已移除或标"已下线"
- [ ] 国内可用性已二次验证（偶尔有变化）
- [ ] URL 全部可达（curl 一下）

---

## changelog 模板

每次更新 reference/*.md 时，留一个 changelog 记录：

```markdown
# Changelog · YYYY-MM-DD

## 更新内容
- DeepSeek V3 价格更新：1 元/百万 input → 0.5 元/百万 input
- 智谱 GLM-4-Flash 永久免费额度从 100 万/日 → 200 万/日
- 新增：硅基流动（SiliconFlow）"永久免费"专区
- 失效：Anthropic Claude Pro 试用取消

## 数据来源
- platform.deepseek.com/api-docs/pricing
- bigmodel.cn/dev/howuse/glm-4
- siliconflow.cn/pricing
- anthropic.com/news
```

---

## 已知问题

| 问题 | 临时方案 |
|---|---|
| 平台经常调"免费层" | 月度重抓 + 主动标"⚠️ 活动可能已结束" |
| 部分平台反爬 | 只抓 Pricing 页，不抓论坛 |
| 某些额度需要登录才能看到 | 让用户自己确认 |
| 平台 URL 偶尔改版 | 每月 1 号验证 URL 可达性 |
| 国内平台偶尔临时维护 | 标"维护中" + 兜底推荐 |
