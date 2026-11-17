# 15+ 格式支持矩阵

> MarkItDown v0.1.x 支持的格式一览。每个格式标了：**默认 extras / 已知坑 / 适合场景**。

---

## 总表

| 格式 | 扩展名 | 底层库 | 默认 extras | 已知坑 | 适合场景 |
|---|---|---|---|---|---|
| **PDF** | `.pdf` | pdfminer.six + pdfplumber | `[pdf]` | 扫描件 PDF 默认不识别 | 报告 / 论文 / 合同 |
| **Word** | `.docx` | mammoth + lxml | `[docx]` | 旧版 .doc 不支持（要装 `[xls]`） | 文档 / 论文 |
| **PowerPoint** | `.pptx` | python-pptx | `[pptx]` | 默认不给图片加 AI 描述 | 演示稿 / 课件 |
| **Excel** | `.xlsx` | pandas + openpyxl | `[xlsx]` | 公式 / 图表可能丢 | 表格 / 数据 |
| **Excel 旧版** | `.xls` | pandas + xlrd | `[xls]` | 只读，不写 | 旧表格 |
| **图片** | `.jpg` `.png` `.gif` `.webp` | EXIF + 可选 LLM | 默认有 EXIF | 不传 `llm_client` 时不识别图内容 | 截图 / 照片 |
| **音频** | `.wav` `.mp3` | EXIF + 可选转写 | `[audio-transcription]` | 不装 extras 只能拿 EXIF 元数据 | 播客 / 录音 |
| **HTML** | `.html` `.htm` | beautifulsoup4 | 默认 | 复杂 JS 渲染的页面拿不到 | 网页存档 |
| **CSV** | `.csv` | 内置 | 默认 | 大文件 (100MB+) 可能 OOM | 表格数据 |
| **JSON** | `.json` | 内置 | 默认 | 嵌套深格式化可能丑 | 数据 |
| **XML** | `.xml` | defusedxml | 默认 | — | 配置 / 数据 |
| **ZIP** | `.zip` | 内置 | 默认 | 递归处理内嵌文件，体积大 | 打包资料 |
| **EPUB** | `.epub` | 内置 | 默认 | 复杂排版可能丢 | 电子书 |
| **YouTube** | URL | youtube-transcript-api | `[youtube-transcription]` | 需要字幕的视频才能转 | 视频字幕 |
| **Outlook MSG** | `.msg` | olefile | `[outlook]` | — | 邮件存档 |
| **Jupyter** | `.ipynb` | 内置 | 默认 | 输出 cell 可能很长 | 笔记 / 教程 |
| **Wikipedia URL** | URL | 内置 | 默认 | 中文维基可能取不全 | 百科资料 |
| **RSS URL** | URL | 内置 | 默认 | — | 订阅源 |

---

## 高级选项（v1 默认不开）

### LLM 图像描述（图片 / PPTX）

```python
from markitdown import MarkItDown
from openai import OpenAI
md = MarkItDown(llm_client=OpenAI(), llm_model="gpt-4o")
result = md.convert("slides.pptx")
```

> 需要 OpenAI key。本 skill v1 默认不引导用户开（要 key 是门槛）。用户主动问时，告知即可。

### Azure Document Intelligence（PDF）

```python
md = MarkItDown(docintel_endpoint="<endpoint>")
result = md.convert("complex.pdf")
```

> 需要 Azure 订阅。本 skill v1 不引导。

### Azure Content Understanding（音视频 / 结构化字段）

```python
md = MarkItDown(cu_endpoint="<endpoint>", cu_analyzer_id="my-analyzer")
result = md.convert("invoice.pdf")
```

> 计费 API。本 skill v1 不引导。

### 插件系统

```bash
# 列出已装插件
markitdown --list-plugins

# 启用插件
markitdown --use-plugins file.pdf
```

推荐插件：
- **markitdown-ocr** —— 用 LLM Vision 给 PDF/Word/PPT/Excel 内嵌图做 OCR
- **markitdown-sample-plugin** —— 自己写插件的模板

本 skill v1 默认不开（要 OpenAI key / 写代码是门槛）。

---

## 各格式的"已知坑"速查

### PDF

- ❌ **扫描件 PDF 默认不识别**——装 `markitdown-ocr` 或换 PaddleOCR
- ❌ **加密 PDF**——markitdown 报权限错误，需先解密
- ⚠️ **复杂版面表格**——pdfminer 偶尔抽错列序
- ⚠️ **超大 PDF（> 500 页）**——处理慢，可能 OOM

### Word

- ❌ **旧版 .doc**——`[docx]` extras 不支持，要先转 .docx 或装老 Word
- ⚠️ **页眉页脚**——通常被丢掉
- ⚠️ **批注 / 修订**——不被保留

### PPT

- ❌ **图表（chart）**——只能拿文本数据，图表本身丢了
- ⚠️ **动画 / 切换效果**——完全丢
- ⚠️ **母版版式**——丢

### Excel

- ❌ **公式**——只拿计算结果，不保留公式
- ❌ **图表**——丢了
- ⚠️ **多 sheet**——按 sheet 顺序拼起来
- ⚠️ **合并单元格**——可能重复内容

### 图片

- ❌ **不传 llm_client**——只拿 EXIF 元数据（拍摄时间、GPS、设备型号），不识别图内容
- ⚠️ **HEIC 格式**——markitdown 默认不支持，要先转 JPG

### 音频

- ❌ **不装 `[audio-transcription]` extras**——只拿 ID3 元数据（歌手、专辑、年份），不转写
- ⚠️ **长音频（> 1 小时）**——转写慢，可能超时

### HTML

- ❌ **JS 渲染的 SPA**——markitdown 不跑 JS，只拿 HTML 源码
- ⚠️ **登录墙**——拿不到登录后内容

---

## 各格式的最佳 extras

| 场景 | 推荐装 |
|---|---|
| 只读 PDF / Word / PPT / Excel | `pip install 'markitdown[pdf,docx,pptx,xlsx]'` |
| 啥都要 | `pip install 'markitdown[all]'` |
| 只要 PDF | `pip install 'markitdown[pdf]'` |
| 接 Azure | `pip install 'markitdown[az-doc-intel]'` 或 `[az-content-understanding]` |

> 推荐 `[all]`（一劳永逸，多 200MB 而已）。