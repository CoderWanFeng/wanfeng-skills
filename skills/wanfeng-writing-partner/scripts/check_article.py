# -*- coding: utf-8 -*-
"""公众号文章发布前格式自检。

用法：
    python3 check_article.py /path/to/article.md

检查项（对齐 SKILL.md 第 7 步清单）：
    - frontmatter 五字段（title/date/tags/categories/cover）齐全
    - tags 首项为「公众号文章」
    - 标题字数（15–30，硬上限 36）
    - 正文汉字数（1500–3000）
    - 主体 ## 小节数量（≤ 3，不含「相关阅读」）
    - 代码围栏 ``` 成对
    - 图片为 http(s) 直链、无占位符
    - 参考链接 ≥ 3 条且用 [标题：URL](URL) 格式
    - 固定 Slogan 一字不差

退出码：有 FAIL 时为 1，仅 WARN 或全通过为 0。
纯标准库实现，无需第三方依赖。
"""
import re
import sys

OK, WARN, FAIL = "✅", "⚠️ ", "❌"
results = []  # (level, message)


def add(level, msg):
    results.append((level, msg))


def cn_count(s):
    """统计中日韩汉字数量。"""
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def check(title, fm, body):
    # ---- frontmatter 字段 ----
    if fm is None:
        add(FAIL, "缺少 frontmatter（--- 包裹的头部信息）")
        return
    fields = {}
    for line in fm.splitlines():
        mm = re.match(r"^(\w+):\s*(.*)$", line.strip())
        if mm:
            fields[mm.group(1)] = mm.group(2).strip()
    for f in ("title", "date", "tags", "categories", "cover"):
        if not fields.get(f):
            add(FAIL, f"frontmatter 缺字段：{f}")
        else:
            add(OK, f"frontmatter 字段齐全：{f}")

    # tags 首项
    tags = fields.get("tags", "")
    if "公众号文章" not in tags:
        add(WARN, "tags 首项建议为「公众号文章」")

    # ---- 标题字数 ----
    t = fields.get("title", "").strip("\"'")
    n = len(t)
    if n == 0:
        add(FAIL, "标题为空")
    elif n > 36:
        add(FAIL, f"标题 {n} 字，超过硬上限 36")
    elif n > 30:
        add(WARN, f"标题 {n} 字，建议压到 30 字以内")
    elif n < 15:
        add(WARN, f"标题 {n} 字，偏短（建议 15–30）")
    else:
        add(OK, f"标题 {n} 字，字数合规")
    if not re.search(r"\d", t) and not re.search(
            r"[A-Za-z]{3,}", t):
        add(WARN, "标题建议含具体数字或产品/英文专有名词")

    # ---- 正文汉字数 ----
    chars = cn_count(body)
    if chars < 1500:
        add(WARN, f"正文 {chars} 汉字，少于建议下限 1500")
    elif chars > 3000:
        add(WARN, f"正文 {chars} 汉字，超过建议上限 3000")
    else:
        add(OK, f"正文 {chars} 汉字，篇幅合规")

    # ---- 主体 ## 小节 ----
    h2 = re.findall(r"^##\s+(.*)$", body, re.MULTILINE)
    main_h2 = [h for h in h2 if "相关阅读" not in h]
    if len(main_h2) > 3:
        add(FAIL, f"主体 ## 小节 {len(main_h2)} 个，超过 3 个上限")
    else:
        add(OK, f"主体 ## 小节 {len(main_h2)} 个（≤3）")

    # ---- 代码围栏配对 ----
    fences = len(re.findall(r"^\s*```", body, re.MULTILINE))
    if fences % 2 != 0:
        add(FAIL, f"代码围栏 ``` 出现 {fences} 次（奇数），未配对")
    else:
        add(OK, "代码围栏成对")

    # ---- 图片链接 ----
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body)
    placeholder_pat = re.compile(
        r"(待补充|example\.com|localhost|127\.0\.0\.1|你的图床|TODO|XXX)",
        re.IGNORECASE)
    if not imgs and "cover" not in fields:
        add(WARN, "正文未发现图片，确认是否漏配图")
    bad = [u for u in imgs if not u.startswith("http")]
    if bad:
        add(FAIL, f"存在非 http 图片链接：{bad}")
    ph = [u for u in imgs if placeholder_pat.search(u)]
    if ph:
        add(FAIL, f"图片链接含占位符/本地路径：{ph}")
    elif imgs:
        add(OK, f"{len(imgs)} 张图片链接格式正常")

    # cover 也检查
    cover = fields.get("cover", "")
    if cover and placeholder_pat.search(cover):
        add(FAIL, f"cover 为占位符：{cover}")

    # ---- 参考链接 ----
    ref_m = re.search(r"###\s*参考链接\s*\n(.*?)(?=\n##\s|\Z)", body,
                      re.DOTALL)
    if not ref_m:
        add(FAIL, "缺少「### 参考链接」小节")
    else:
        block = ref_m.group(1)
        links = re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", block)
        if len(links) < 3:
            add(WARN, f"参考链接 {len(links)} 条，建议 ≥ 3 条")
        else:
            add(OK, f"参考链接 {len(links)} 条")
        # 非微信链接应写成 [标题：URL](URL)
        for txt, url in links:
            if "mp.weixin.qq.com" in url:
                continue
            if url not in txt:
                add(WARN, f"参考链接未用「[标题：URL](URL)」格式：{txt[:30]}")

    # ---- 固定 Slogan ----
    if "科技不高冷，AI很好用。" not in body:
        add(FAIL, "缺少固定 Slogan 第一句「科技不高冷，AI很好用。」")
    if "我是晚枫，关注我，带你一起玩AI！" not in body:
        add(FAIL, "缺少固定 Slogan 第二句")
    if "科技不高冷，AI很好用。" in body and "我是晚枫，关注我，带你一起玩AI！" in body:
        add(OK, "固定 Slogan 存在")

    # ---- 相关阅读 ----
    if not re.search(r"^##\s+相关阅读", body, re.MULTILINE):
        add(WARN, "缺少「## 相关阅读」小节")


def main():
    if len(sys.argv) < 2:
        sys.exit("用法：python3 check_article.py /path/to/article.md")
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        sys.exit(f"找不到文件：{path}")

    fm, body = parse_frontmatter(text)
    title = ""
    if fm:
        m = re.search(r"^title:\s*(.+)$", fm, re.MULTILINE)
        title = m.group(1).strip("\"'") if m else ""
    check(title, fm, body)

    print("=" * 56)
    print("文章自检：%s" % path)
    print("=" * 56)
    fails = sum(1 for lv, _ in results if lv == FAIL)
    warns = sum(1 for lv, _ in results if lv == WARN)
    for lv, msg in results:
        print("%s %s" % (lv, msg))
    print("-" * 56)
    if fails:
        print("结论：%d 项未通过（FAIL），%d 项提醒（WARN）——请修正后再发布。"
              % (fails, warns))
        sys.exit(1)
    if warns:
        print("结论：硬性项全部通过，%d 项提醒（酌情处理）。" % warns)
        sys.exit(0)
    print("结论：全部通过 ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()
