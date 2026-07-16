# Quickstart · 5 分钟跑通

> 第一次用本 skill？照着下面 3 步走。

---

## 第 1 步：装依赖（1-2 分钟）

```bash
bash scripts/install.sh
```

会自动：
1. 找 Python ≥ 3.10
2. 检测 PyPI 是否可达（不可达自动切阿里源）
3. `pip install 'markitdown[all]'`
4. 验证装成功

**如果失败**：看 [troubleshooting.md](troubleshooting.md) 的报错 1 和报错 2。

---

## 第 2 步：转一个文件（10 秒）

```bash
# 转本地 PDF
bash scripts/convert.sh /path/to/your-file.pdf

# 转本地 Word
bash scripts/convert.sh /path/to/your-file.docx

# 转 URL
bash scripts/convert.sh https://example.com/page.html
```

输出就是 Markdown 全文。直接复制走用。

---

## 第 3 步：在 AI 对话里用（30 秒）

在装了本 skill 的 AI 对话里说：

> "帮我速读这份 PDF `/Users/wanfeng/Downloads/report.pdf`"

AI 会：
1. 自动调 `convert.sh` 转 Markdown
2. 给你 3 个选项（A 一句话总结 / B 结构化摘要 / C 完整副本）
3. 默认走 A——你说"默认"就行

---

## 常见问题

### Q: 我装了 markitdown 但脚本说"没装"

A: 多半是 `pip` 装在别的 Python 环境里了。试试：

```bash
python3 -m pip install 'markitdown[all]'
bash scripts/convert.sh your-file.pdf
```

### Q: 转 PDF 出来是空的

A: 多半是**扫描件 PDF**（图片 PDF）。MarkItDown 默认不识别扫描件。

3 种解法：
1. 装 OCR 插件：`pip install markitdown-ocr` + 配 OpenAI key
2. 用 Azure Document Intelligence（要 Azure 账号）
3. 换工具：PaddleOCR / Tesseract

详见 [troubleshooting.md](troubleshooting.md) 报错 4。

### Q: 我在国内，pip 装不上

A: `install.sh` 已经自动切阿里源。如果还慢，手动指定：

```bash
pip install -i https://mirrors.aliyun.com/pypi/simple/ 'markitdown[all]'
```

### Q: 转的文件特别大（> 100MB）

A: MarkItDown 是内存里处理整个文件。100MB+ 的 PPT / 大型 PDF 可能 OOM。

3 种解法：
1. 先用 pdftk / 7-Zip 拆小
2. 装 64 位 Python（不要 32 位）
3. 加机器内存

---

## 下一步

- 看 [formats.md](formats.md) 了解 15+ 格式支持矩阵
- 看 [safety.md](safety.md) 了解安全约束
- 看 [troubleshooting.md](troubleshooting.md) 看 8 个常见报错的 5 段式兜底