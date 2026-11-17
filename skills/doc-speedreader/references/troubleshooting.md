# 失败兜底 · 8 个常见报错的 5 段式回答

> 当用户报某个错时，AI 在对话里**按这个模板回应**：
> **原文 → 人话 → 根因 → 3 步 → 兜底**

---

## 报错 1：markitdown 没装

**原文**：
```
ModuleNotFoundError: No module named 'markitdown'
```

**人话**：你电脑里没装 markitdown 这个 Python 包。

**根因**：第一次用这个 skill，没装依赖。

**3 步搞定**：
1. 跑 `bash scripts/install.sh`（自动装）
2. 装完再跑 `bash scripts/convert.sh <file>`
3. 如果还报，检查 `python3 -c "import markitdown"` 能不能成功

**兜底**：手动装 `pip install 'markitdown[all]'`

---

## 报错 2：Python 版本不够

**原文**：
```
ERROR: markitdown requires Python >= 3.10
```

**人话**：你的 Python 版本太老，markitdown 不支持。

**根因**：markitdown 用了 Python 3.10+ 才有的语法。

**3 步搞定**：
1. 看当前版本：`python3 --version`
2. macOS 用户：`brew install python@3.12`
3. Linux 用户：`sudo apt install python3.12`

**兜底**：用 conda 装新版本：`conda create -n markitdown python=3.12 && conda activate markitdown`

---

## 报错 3：pip 装得慢 / 装不上（国内）

**原文**：
```
Read timed out.
WARNING: Retrying (Retry(total=4, connect=5, read=5, ...)) after connection broken by 'ReadTimeoutError'
```

**人话**：在国内 pip 默认源很慢 / 经常断。

**根因**：PyPI 官方源在中国大陆访问慢且不稳。

**3 步搞定**：
1. 用本 skill 自带的 install.sh（已自动切阿里源）
2. 如果还慢，手动指定：`pip install -i https://mirrors.aliyun.com/pypi/simple/ 'markitdown[all]'`
3. 如果阿里源也慢，换清华源：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ 'markitdown[all]'`

**兜底**：用国内镜像站的 wheel：`pip install --only-binary=:all: -i https://mirrors.aliyun.com/pypi/simple/ 'markitdown[all]'`

---

## 报错 4：PDF 扫描件，转换出来是空

**原文**：
```
# 转换成功，但输出是几行空字符串或占位符
```

**人话**：你这个 PDF 是扫描件（图片 PDF），里面的文字其实是图片，markitdown 认不出来。

**根因**：扫描件 PDF 的"文字层"是图片，markitdown 默认不做 OCR。

**3 步搞定**：
1. 装 OCR 插件：`pip install markitdown-ocr`
2. 配 OpenAI key（要花钱）
3. 用法：`MarkItDown(enable_plugins=True, llm_client=OpenAI(), llm_model='gpt-4o')`

**兜底**：换工具：
- **PaddleOCR**（中文强，本地运行）
- **Tesseract**（英文，免费）
- **Azure Document Intelligence**（云端，准但要订阅）

---

## 报错 5：PDF 加密 / 权限不够

**原文**：
```
PdfReadError: File has not been decrypted
```
或
```
PermissionError: [Errno 13] Permission denied
```

**人话**：PDF 加密了 / 你没读权限。

**根因**：
- 加密：原作者加了密码
- 权限：文件 owner 不是你，或 chmod 600

**3 步搞定**：
1. 如果是密码 PDF：先用 `qpdf --decrypt input.pdf output.pdf`（要原密码）
2. 如果是权限问题：`chmod 644 file.pdf`（前提是你有 sudo）
3. 如果文件 owner 不是你：`sudo chown $USER file.pdf`

**兜底**：问发文件的人要解密版本。

---

## 报错 6：URL 转换超时

**原文**：
```
requests.exceptions.Timeout: HTTPConnectionPool(...): Read timed out.
```

**人话**：那个网站响应太慢，10 秒没回。

**根因**：网站本身慢 / 你网速慢 / 网站墙了你。

**3 步搞定**：
1. 手动打开 URL 看能不能打开
2. 如果能打开，重试一次（可能是网络抖动）
3. 如果经常超时，换 `--response` 模式自己 fetch（自己控超时）

**兜底**：把页面"另存为 HTML" → 让 AI 转本地 HTML 文件。

---

## 报错 7：URL 拒绝访问（403/401）

**原文**：
```
requests.exceptions.HTTPError: 403 Client Error: Forbidden
```
或
```
requests.exceptions.HTTPError: 401 Client Error: Unauthorized
```

**人话**：那个网站不让你访问（要登录 / 你的 IP 被封）。

**根因**：网站有反爬 / 要鉴权 / 地理限制。

**3 步搞定**：
1. 手动打开 URL 看是不是要登录
2. 如果要登录，自己登录后用 `--response` 模式（带 cookies）
3. 如果是反爬（如 Cloudflare），可能需要无头浏览器（playwright）→ 换工具

**兜底**：放弃在线转，下载后转。

---

## 报错 8：文件超大，OOM（内存溢出）

**原文**：
```
MemoryError
```
或脚本被 kill：
```
Killed
```

**人话**：文件太大，内存爆了。

**根因**：markitdown 是内存里处理整个文件。1GB+ 的 PPT / 大型 PDF 会 OOM。

**3 步搞定**：
1. 先 `ls -lh file.pptx` 看文件多大
2. > 500MB：先用工具拆小（pdftk / 7-Zip）
3. > 1GB：直接放弃 markitdown，用专业工具（Apache Tika / Unstructured）

**兜底**：用更轻量的工具只读前 N 页：
```bash
# 装 pypdf
pip install pypdf
python3 -c "
from pypdf import PdfReader
reader = PdfReader('huge.pdf')
for i, page in enumerate(reader.pages[:10]):
    print(page.extract_text())
"
```

---

## 其他未列出的报错

如果用户报的错不在上面 8 个里：

1. 先看报错最后 1-2 行（最重要的信息在最后）
2. 搜报错信息（去掉路径 / 行号）
3. 如果 markitdown 上游有相关 issue，引导用户去看：https://github.com/microsoft/markitdown/issues
4. 如果都不行，让用户提供：Python 版本 / markitdown 版本 / 文件类型 / 文件大小 / 完整报错