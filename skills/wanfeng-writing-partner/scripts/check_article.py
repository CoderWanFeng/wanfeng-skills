# -*- coding: utf-8 -*-
"""公众号文章发布前格式自检（按文章类型）。

用法：
    python3 check_article.py /path/to/article.md
    python3 check_article.py --type tutorial /path/to/article.md
    python3 check_article.py --type auto /path/to/article.md

类型：
    science   科普 / 观点
    tutorial  手把手教程
    release   产品发布 / 评测
    benefit   免费福利 / 活动
    announce  合作 / 身份公告
    auto      按标题关键词推断（默认；推断不准时用 --type 指定）

检查项（对齐 SKILL.md 第 7 步与 references/viral-patterns.md）：
    - frontmatter 五字段（title/date/tags/categories/cover）齐全
    - 标题字数（建议 18–32，硬上限 36）、含具体数字或产品名
    - 正文汉字数（1500–4000）
    - 主体 ## 小节数量（按类型上限，不再一刀切 ≤3）
    - 代码围栏 ``` 成对
    - 图片为 http(s) 直链、无占位符
    - 参考链接数量与格式（按类型）
    - 固定 Slogan（合作 / 身份公告类可省略）
    - 实证写法 WARN：固定开场白 / 主动亮短板 / 共情自嘲 / 表格化 /
      官方口径 / 图片来源 / 科普类 AI 原理段 / 链接位置格式

退出码：有 FAIL 时为 1，仅 WARN 或全通过为 0。
纯标准库实现，无需第三方依赖。
"""
import argparse
import re
import sys

OK, WARN, FAIL = "✅", "⚠️ ", "❌"
results = []  # (level, message)

TYPE_RULES = {
    "science":  {"label": "科普 / 观点",     "max_h2": 3, "principle": True,
                 "slogan": True,  "refs": 3},
    "tutorial": {"label": "手把手教程",     "max_h2": 6, "principle": False,
                 "slogan": True,  "refs": 0},
    "release":  {"label": "产品发布 / 评测", "max_h2": 8, "principle": False,
                 "slogan": True,  "refs": 3},
    "benefit":  {"label": "免费福利 / 活动", "max_h2": 5, "principle": False,
                 "slogan": True,  "refs": 3},
    "announce": {"label": "合作 / 身份公告", "max_h2": 4, "principle": False,
                 "slogan": False, "refs": 0},
}

# 只收录「主动亮短板」的特异表述；命不中就提醒人工确认，不硬判
LIMIT_WORDS = (
    "代价我先摊开说", "摊开说", "做不到", "不会绕着说", "不等于只剩好评",
    "这几条我认", "出不了", "只能出", "不如", "效果也差", "差一截",
    "不能根据", "不支持", "没有字幕", "按量计费", "预估，不是最终账单",
    "以官方审核", "边界", "做不到的事",
)
EMPATHY_WORDS = (
    "说白了", "懂你", "说简单一点", "不算小数目", "都做不到",
    "不想让你踩坑", "一句话：", "不然你以为呢", "大家都是",
)

# 正文里的 markdown 链接（排除图片 ![...]）；只用于「链接位置格式」提醒
LINK_RE = re.compile(r"(?<!\!)\[[^\]]+\]\((https?://[^)]+)\)")


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


def infer_type(title):
    """按标题关键词推断类型；顺序即优先级，推断不准时用 --type 覆盖。"""
    checks = (
        ("announce", ("大使", "合伙人", "授勋", "连任", "第2年", "第 2 年", "合作")),
        ("benefit",  ("免费领", "白嫖", "领积分", "免费领取", "福利", "沙龙", "薅")),
        ("release",  ("发布", "新版本", "上线", "评测", "Skill", "skill")),
        ("tutorial", ("教程", "步就", "三步", "怎么", "如何", "手把手")),
    )
    for name, kws in checks:
        if any(k in title for k in kws):
            return name
    return "science"


def check(title, fm, body, atype):
    rule = TYPE_RULES[atype]

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
    elif n > 32:
        add(WARN, f"标题 {n} 字，建议压到 32 字以内（含英文产品名可到 36）")
    elif n < 18:
        add(WARN, f"标题 {n} 字，偏短（建议 18–32）")
    else:
        add(OK, f"标题 {n} 字，字数合规")
    if not re.search(r"\d", t) and not re.search(r"[A-Za-z]{3,}", t):
        add(WARN, "标题建议含具体数字或产品/英文专有名词")
    if re.search(r"揭秘|震惊|不看后悔|深度解析|万字长文", t):
        add(WARN, "标题含空洞词，实证 P1 建议改成利益前置")

    # ---- 正文汉字数 ----
    chars = cn_count(body)
    if chars < 1500:
        add(WARN, f"正文 {chars} 汉字，少于建议下限 1500")
    elif chars > 4000:
        add(WARN, f"正文 {chars} 汉字，超过建议上限 4000")
    else:
        add(OK, f"正文 {chars} 汉字，篇幅合规")

    # ---- 主体 ## 小节（按类型） ----
    h2 = re.findall(r"^##\s+(.*)$", body, re.MULTILINE)
    main_h2 = [h for h in h2 if "相关阅读" not in h]
    limit = rule["max_h2"]
    if len(main_h2) > limit:
        add(FAIL, f"主体 ## 小节 {len(main_h2)} 个，超过 {rule['label']} 上限 {limit}")
    else:
        add(OK, f"主体 ## 小节 {len(main_h2)} 个（{rule['label']} 上限 {limit}）")

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

    cover = fields.get("cover", "")
    if cover and placeholder_pat.search(cover):
        add(FAIL, f"cover 为占位符：{cover}")

    # ---- 参考链接（按类型） ----
    ref_m = re.search(r"###\s*参考链接\s*\n(.*?)(?=\n##\s|\Z)", body,
                      re.DOTALL)
    need_refs = rule["refs"]
    if not ref_m:
        msg = "缺少「### 参考链接」小节"
        add(FAIL if need_refs else WARN, msg + (
            "" if need_refs else f"（{rule['label']}类不强求）"))
    else:
        block = ref_m.group(1)
        links = re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", block)
        if len(links) < need_refs:
            add(WARN, f"参考链接 {len(links)} 条，{rule['label']}类建议 ≥ {need_refs} 条")
        else:
            add(OK, f"参考链接 {len(links)} 条")
        for txt, url in links:
            if "mp.weixin.qq.com" in url:
                continue
            if url not in txt:
                add(WARN, f"参考链接未用「[标题：URL](URL)」格式：{txt[:30]}")

    # ---- 固定 Slogan（合作/身份公告类可省略） ----
    s1 = "科技不高冷，AI很好用。" in body
    s2 = "我是晚枫，关注我，带你一起玩AI！" in body
    if rule["slogan"]:
        if not s1:
            add(FAIL, "缺少固定 Slogan 第一句「科技不高冷，AI很好用。」")
        if not s2:
            add(FAIL, "缺少固定 Slogan 第二句")
        if s1 and s2:
            add(OK, "固定 Slogan 存在")
    else:
        add(OK, f"{rule['label']}类 Slogan 可省略（当前"
            + ("已写" if s1 and s2 else "未写") + "）")

    # ---- 相关阅读 ----
    if not re.search(r"^##\s+相关阅读", body, re.MULTILINE):
        add(WARN, "缺少「## 相关阅读」小节")

    # ---- 实证写法（只 WARN，不硬判） ----
    if re.search(r"大家好[，,]\s*(我是|这里是)程序员晚枫", body):
        add(OK, "固定开场白存在")
    else:
        add(WARN, "未检出固定开场白「大家好，我是程序员晚枫。」（实证 P2）")

    if any(w in body for w in LIMIT_WORDS):
        add(OK, "检出「主动亮短板」表述")
    else:
        add(WARN, "未检出主动亮短板表述，按实证 P4 人工确认"
            "（代价 / 做不到 / 不如 / 边界 / 预估不是账单）")

    if any(w in body for w in EMPATHY_WORDS):
        add(OK, "检出共情或自嘲表述")
    else:
        add(WARN, "未检出共情 / 自嘲表述，按实证 P5 人工确认")

    table_rows = len(re.findall(r"^\s*\|", body, re.MULTILINE))
    if table_rows >= 3:
        add(OK, f"含表格（{table_rows} 行），决策信息已表格化")
    else:
        add(WARN, "未检出表格，按实证 P7 确认决策 / 对比 / 费用信息是否已表格化")

    if imgs and not re.search(r"图片来源|·\s*来源|图：", body):
        add(WARN, "有图片但未检出 `*图片来源：…*` 斜体注（实证 P8）")
    elif imgs:
        add(OK, "图片来源标注存在")

    if re.search(r"积分|免费|费用|入选|权益|领取|充值|价格|额度", body):
        if re.search(r"以官方|为准|预估|评审决定|活动规则|实际安排", body):
            add(OK, "权益 / 费用类信息带「以官方为准」口径")
        else:
            add(WARN, "含权益 / 费用类信息但缺「以官方为准 / 预估」口径（实证 P8）")

    if rule["principle"] and not re.search(r"为什么|原理|其实是|说白了就是", body):
        add(WARN, "科普 / 观点类建议含一段讲透 AI 原理（其他类型不需要）")

    if not re.search(r"评论区|点个赞|打出来|@晚枫|@user", body):
        add(WARN, "未检出具体互动或可复制指令（实证 P9）")

    # ---- 链接位置格式（用户指定，只 WARN） ----
    check_link_position(body)


def check_link_position(body):
    """链接按位置包装：只 WARN，不硬判（对齐 writing-guide.md §9.2）。"""
    text = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    in_refs = False
    standalone, inline = [], []
    for raw in text.splitlines():
        line = raw.rstrip()
        s = line.strip()
        if not s:
            continue
        if s.startswith("### 参考链接") or s.startswith("## 相关阅读"):
            in_refs = True
            continue
        if s.startswith("## "):
            in_refs = False
        if in_refs or s.startswith(">"):
            continue
        if s.startswith("*图片来源") or s.startswith("*图："):
            continue  # 图片来源斜体标注：豁免
        if s.startswith(("-", "+", "|")) or re.match(r"^\d+[\.、]", s):
            continue
        links = list(LINK_RE.finditer(line))
        if not links:
            continue
        # ① 整段只有这一条链接 → 应当用 > 引用块包住
        if len(links) == 1 and s == links[0].group(0).strip():
            standalone.append(s[:40])
            continue
        # ② 链接与中文混排 → 应当用英文引号把链接前后包住
        for m in links:
            before, after = line[:m.start()], line[m.end():]
            if re.search(r"[\u4e00-\u9fff]", before + after):
                if not (before.rstrip().endswith('"')
                        and after.lstrip().startswith('"')):
                    inline.append(s[:40])
                    break
    if standalone:
        add(WARN, "发现 %d 条单独成段的裸链接，建议用 > 引用块包住"
            "（链接位置格式，见 writing-guide.md §9.2）：%s"
            % (len(standalone), standalone[0]))
    if inline:
        add(WARN, "发现 %d 处嵌入正文的链接未用英文引号包住，"
            "建议用英文引号把整个 [标题：URL](URL) 前后包住"
            "（见 writing-guide.md §9.2）：%s"
            % (len(inline), inline[0]))


def main():
    ap = argparse.ArgumentParser(
        description="公众号文章发布前格式自检（按文章类型）")
    ap.add_argument("--type", default="auto",
                    choices=["auto"] + list(TYPE_RULES),
                    help="文章类型，默认 auto 按标题推断")
    ap.add_argument("article", help="待检查的 Markdown 文件路径")
    args = ap.parse_args()

    try:
        with open(args.article, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        sys.exit(f"找不到文件：{args.article}")

    fm, body = parse_frontmatter(text)
    title = ""
    if fm:
        m = re.search(r"^title:\s*(.+)$", fm, re.MULTILINE)
        title = m.group(1).strip("\"'") if m else ""

    if args.type == "auto":
        atype = infer_type(title)
        type_note = f"{TYPE_RULES[atype]['label']}（{atype}，auto 推断；不对请用 --type 指定）"
    else:
        atype = args.type
        type_note = f"{TYPE_RULES[atype]['label']}（{atype}，手动指定）"

    check(title, fm, body, atype)

    print("=" * 56)
    print("文章自检：%s" % args.article)
    print("文章类型：%s" % type_note)
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
