#!/usr/bin/env python3
"""在用户项目中准备写作使用示例：离线、仅补缺、不覆盖，使用 Python 3 标准库。"""

import argparse
import json
from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PARTS = ("workflow", "写作搭子", "示例")
# 每个场景按「素材、中文请求、英文请求、预期产物、边界」生成，不执行请求本身。
SCENARIOS = (
    (
        "热点长文", "产品名、目标读者、官方公告 URL",
        "请根据【产品名】的【官方公告 URL】，为【目标读者】写一篇 1500–3000 字的中文公众号长文。先核实信息，未知内容标为待核实。",
        "Write a 1500–3000-character Chinese article about [product] for [audience], using [official announcement URL]. Verify claims first and mark unknowns as unverified.",
        "标题候选、结构提纲、Markdown 长文和参考链接。", "不得把公告之外的推测写成已发布功能。",
    ),
    (
        "官方文档教程", "产品名、官方文档 URL、读者基础、要完成的任务",
        "把【产品名】的【官方文档 URL】整理成面向【读者基础】的中文教程，目标是完成【任务】。列出前置条件、操作步骤和失败兜底。",
        "Turn [official documentation URL] for [product] into a Chinese tutorial for [reader level] to complete [task]. Include prerequisites, steps and troubleshooting.",
        "分步骤教程、所需截图清单、引用来源。", "未实测的步骤必须标明依据，不宣称已经跑通。",
    ),
    (
        "产品体验评测", "产品名、自己的体验记录、官方说明 URL",
        "根据【产品名】的【体验记录】和【官方说明 URL】写中文评测，区分我的实测、官方说法和个人判断，也写清限制与不适合的人群。",
        "Write a Chinese review of [product] from [my experience notes] and [official documentation URL]. Separate observations, official claims and opinions; include limitations.",
        "含使用场景、体验、局限和适用人群的评测草稿。", "不编造使用体验、耗时、性能或收益数据。",
    ),
    (
        "标题优化", "产品名、正文或选题、目标读者",
        "为【产品名】的【正文或选题】起 6–8 个中文标题，面向【目标读者】，逐个标注字数，控制在 30 字以内，推荐一个并说明理由。",
        "Suggest 6–8 Chinese titles for [article or topic] about [product] for [audience]. Count characters, keep each within 30 characters and recommend one with reasons.",
        "6–8 个标题、字数和推荐理由。", "标题里的数字和承诺必须有正文依据。",
    ),
    (
        "正文结构", "选题、现有素材、读者最关心的问题",
        "根据【选题】和【素材】，围绕【读者问题】搭中文长文结构。主体最多 3 个二级小节，包含一段通俗原理解释，暂不扩写全文。",
        "Outline a Chinese long-form article about [topic] from [materials], addressing [reader question]. Use at most three main H2 sections and include a plain-language explanation; do not draft the full article yet.",
        "开头钩子、主体提纲、证据缺口和结尾方向。", "缺少素材时标明缺口，不用想象补齐证据。",
    ),
    (
        "旧文改写", "自己拥有或获授权的旧文、读者、更新资料",
        "把【有权使用的旧文】改写成面向【目标读者】的中文长文，用【更新资料】复核过期信息，保留出处，不直接沿用旧价格和日期。",
        "Rewrite [an article I own or may reuse] in Chinese for [audience], checking outdated claims against [updated sources]. Preserve attribution and recheck prices and dates.",
        "改写稿、变更说明、仍需核实的信息清单。", "不默认拥有他人文章的转载或改写授权。",
    ),
    (
        "暖白流程插图", "要解释的流程、每个节点的短文案",
        "为【文章段落】设计一张暖白流程插图，节点为【节点文案】。一张图只讲一件事，沿用 Skill 色板，生成后检查文字溢出。",
        "Create a warm-style flow illustration for [article paragraph] using [node labels]. Explain one idea, use the Skill palette and inspect text overflow after rendering.",
        "本地插图文件、图注和目检结果。", "这里只准备请求示例；实际绘图时再检查 Pillow，不调用付费生图接口。",
    ),
    (
        "网页截图规划", "公开页面 URL、要讲解的操作或区域",
        "文章要介绍【公开页面 URL】里的【操作或区域】，请规划必要截图；实际截图时只保留相关区域，并检查是否含账号或个人信息。",
        "Plan screenshots of [operation or region] on [public page URL] for my article. When capturing, keep only relevant areas and check for account or personal information.",
        "截图位置、用途、来源标注和脱敏检查项。", "不把示意图冒充真实界面，不绕过登录和访问限制。",
    ),
    (
        "截图脱敏", "用户指定的本地截图、需要公开的内容",
        "检查【本地截图】中的姓名、头像、账号 ID、邮箱、手机号和订单号，把敏感信息遮盖后另存副本，保留原图，先不要上传。",
        "Inspect [local screenshot] for names, avatars, account IDs, email addresses, phone numbers and order numbers. Redact sensitive details into a separate copy; preserve the original and do not upload.",
        "脱敏副本、处理项目和仍需人工确认的区域。", "不读取无关文件，不覆盖原图，不展示被遮盖的私人内容。",
    ),
    (
        "图床上传", "已脱敏图片、用户选定的图床方案和授权范围",
        "【截图】需要脱敏后上传到我自己的【图床方案】。先检查脱敏、解释配置与上传范围，等我明确确认后再上传；不要在对话里索要 Token。",
        "Help anonymize [screenshot] and upload it to my own [image hosting service]. Check redaction and explain setup and upload scope first; wait for my explicit confirmation and do not ask me to paste a token.",
        "脱敏与配置检查、授权后的上传结果和直链验证。", "此示例不是上传授权；没有明确授权或配置时只给引导。",
    ),
    (
        "图片与引用链接", "正文、已上传图片 URL、官方来源 URL",
        "把【已上传图片 URL】和【官方来源 URL】插入【正文】，补齐图注。检查图片直链，非微信来源使用 [标题：完整URL](完整URL) 格式。",
        "Insert [uploaded image URLs] and [official source URLs] into [article] with captions. Verify image links and format non-WeChat references as [title: full URL](full URL).",
        "图片与引用格式修订稿、失效链接清单。", "不可把本地图片路径或占位 URL 当成已验证外链。",
    ),
    (
        "发布前检查", "用户指定的 Markdown 草稿和引用来源",
        "按写作搭子的第 7 步检查【Markdown 草稿】，列出标题、字数、结构、事实来源、图片脱敏和链接问题，先给检查结果，不替我发布。",
        "Check [Markdown draft] using step 7 of the Writing Partner workflow. Report title, length, structure, sources, redaction and link issues; do not publish it for me.",
        "格式检查结果、事实与图片的人工复核项、修改建议。", "格式脚本通过不等于事实已核实，也不代表已发布。",
    ),
)


def build_examples():
    """生成纯文本示例库；不读取用户素材，不访问网络。"""
    files = {}
    links = []
    for number, (title, inputs, zh, en, output, boundary) in enumerate(SCENARIOS, 1):
        name = f"{number:02d}-{title}.md"
        links.append(f"- [{title}]({name})")
        files[name] = (
            f"# {title} · 使用示例\n\n"
            "> 仅演示怎么提需求，不是事实、成稿或执行授权。请替换占位内容后再使用。\n\n"
            f"## 需要准备\n{inputs}\n\n"
            f"## 中文请求\n```text\n{zh}\n```\n\n"
            f"## 英文请求\n```text\n{en}\n```\n\n"
            f"## 预期产物\n{output}\n\n"
            f"## 注意边界\n{boundary}\n"
        )
    files["00-使用说明.md"] = (
        "# 写作搭子 · 本地使用示例\n\n"
        f"默认提供 {len(SCENARIOS)} 类场景，每类中英文各一条，共 {len(SCENARIOS) * 2} 条请求示例。\n"
        "这些文件由本地规则生成，未执行任何示例请求，也未联网、生成图片或上传文件。\n\n"
        "## 怎么用\n"
        "选择与你的任务相关的一项，替换【占位内容】或 [placeholders]，再把请求交给写作搭子。\n"
        "英文请求也以中文文章为主要产物；示例不是已核实的产品信息或可以直接发布的文章。\n"
        "不需要逐项选择；已经说清需求时直接开展任务。不要在示例文件或对话中填写密钥。\n\n"
        "## 场景目录\n" + "\n".join(links) + "\n\n"
        "## 保留规则\n"
        "初始化只补缺失文件，已存在的非空 UTF-8 文件保留，不覆盖你的修改。\n"
        "若同名位置是空文件、目录、符号链接或不可读文件，会报告冲突，不自动清理。\n"
    )
    return files


def existing_file(path):
    """已有普通文件按用户内容保留，空文件或异常占位不能冒充可用示例。"""
    if path.is_symlink():
        raise ValueError(f"示例路径是符号链接，未跟随：{path}")
    if not path.exists():
        return False
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        raise ValueError(f"示例路径不是非空文本文件，已保留，请确认后另存冲突项：{path}")
    return True


def init_examples(project):
    project = Path(project).expanduser().resolve(strict=True)
    if not project.is_dir():
        raise ValueError("--project 必须指向已存在的用户项目目录")
    if project == SKILL_ROOT or SKILL_ROOT in project.parents:
        raise ValueError("不能在 Skill 源目录或安装目录内生成示例，请指定用户项目")

    output = project
    for part in OUTPUT_PARTS:
        output = output / part
        if output.is_symlink():
            raise ValueError(f"输出目录含符号链接，未跟随：{output}")
        if output.exists() and not output.is_dir():
            raise ValueError(f"输出目录被同名文件占用，已保留：{output}")
    files = build_examples()
    # 先检查所有已知冲突，避免发现冲突之前就写入其它示例。
    for name in files:
        existing_file(output / name)
    output.mkdir(parents=True, exist_ok=True)
    created, kept = [], []
    for name, content in files.items():
        path = output / name
        if existing_file(path):
            kept.append(name)
            continue
        try:
            # 排他创建，即使同时启动两次，也不会截断另一个进程创建的文件。
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
            created.append(name)
        except FileExistsError:
            if not existing_file(path):
                raise ValueError(f"示例文件状态发生变化，请重试：{path}")
            kept.append(name)
    for name in files:
        if not existing_file(output / name):
            raise ValueError(f"示例生成后缺失：{output / name}")
    return {
        "ok": True,
        "directory": str(output),
        "index": str(output / "00-使用说明.md"),
        "created": created,
        "kept": kept,
        "total_files": len(files),
        "default_scenarios": len(SCENARIOS),
        "default_prompts": len(SCENARIOS) * 2,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path, help="已存在的用户项目目录，不是 Skill 安装目录")
    args = parser.parse_args(argv)
    try:
        result = init_examples(args.project)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({
            "ok": False,
            "error": str(exc),
            "hint": "本地示例未全部就绪；已有文件和可能已写入的部分示例均保留。请检查项目路径、写权限或同名冲突后重试，不要覆盖旧文件。",
        }, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
