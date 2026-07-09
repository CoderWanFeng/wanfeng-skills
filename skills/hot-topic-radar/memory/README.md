# 记忆目录

存放选题雷达的**去重记忆**和**历史推送记录**。

## 文件说明

- **`dedup-history.jsonl`** · 每行一条 JSON，记录已推送过的热点：
  ```json
  {"title": "OpenAI 推出 GPT-6", "platform": "weibo", "url": "https://...", "pushed_at": "2026-07-10T15:30:00"}
  ```

## 自动清理

主流程每 30 天会自动清理 `window_days` 之外的旧记录（防止文件无限膨胀）。

## 手动清空

```bash
python scripts/fetch_hot.py --clear-memory
```

清空后会强制重推所有历史热点（慎用）。

## 数据隐私

所有数据**仅本地存储**，不会上传到任何服务器。