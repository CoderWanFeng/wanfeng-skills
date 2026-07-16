# task/ · 用户的历史 task

> 这个目录装本 skill 跑过的"完整 Markdown 副本"产物。
> **命名规则**：`YYYYMMDD-<slug>/<原文件名>.md`

---

## 目录说明

- 每次用户选「C. 完整 Markdown」时，会在这里建一个 `YYYYMMDD-<slug>/` 子目录
- slug = 用户给的文件名（或自动从文件名提取，去扩展名）
- 同一个 slug 多次跑会**覆盖**之前的产物（不是追加）

---

## 清理建议

- 这个目录会**一直变大**，定期清理即可
- 清理时按 `rm -rf task/2026*` 一把删掉也行（产物都是临时的）
- 想保留某个 task？把它移出去到 `~/Documents/` 或别的地方

---

## 隐私提醒

- 本目录里的 Markdown 包含原文全部内容
- **敏感文件转完请检查**：客户名 / 合同号 / 金额 / 个人隐私是否需要脱敏
- 同步到云端 / git 之前先 review

---

## 例子

```
task/
├── 20260716-acme-report/
│   └── acme-q3-report.md     # 来自 acme-q3-report.pdf
├── 20260716-meeting-notes/
│   └── meeting-20260715.md    # 来自 meeting-20260715.docx
└── 20260717-paper-arxiv/
    └── 2401.12345.md          # 来自 arxiv URL
```