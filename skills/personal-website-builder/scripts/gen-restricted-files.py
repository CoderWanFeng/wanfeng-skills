#!/usr/bin/env python3
"""gen-restricted-files.py · 晚枫个人网站 · 按规律重建受平台限制的模板文件。

背景
----
部分安装平台会过滤掉三类文件：``.`` 开头的隐藏文件（``templates/*/.gitignore``）、
``.template`` 后缀文件（``templates/*/package.json.template``）、
``.vue`` 组件文件（``templates/vue3-vite/src/**/*.vue``）。
这些文件一旦丢失，``init-*.sh`` 的裸 ``cp`` 会因 ``set -e`` 中止，AI 导航站类型还会整体不可用。

本脚本是这些文件的**生成器** —— 把生成规律固化成代码，平台丢了就在本地一键重建，
不必让 AI 逐字抄写几千字节。

用法
----
    python3 scripts/gen-restricted-files.py --check      # 只检查：列出缺失 / 漂移 / 一致
    python3 scripts/gen-restricted-files.py             # 只重建缺失的文件（默认，幂等）
    python3 scripts/gen-restricted-files.py --force     # 强制重建全部 12 个文件
    python3 scripts/gen-restricted-files.py --target DIR # 指定 skill 根目录（默认本脚本上级）

产物（相对 skill 根目录，共 12 个）
--------------------------------
    templates/<框架>/.gitignore              × 5
    templates/<框架>/package.json.template   × 2
    templates/vue3-vite/src/**/*.vue          × 5

三项自检（每次运行都做，不一致直接报错）
--------------------------------------
1. **CSS 变量闭环**：``.vue`` 里引用的 ``var(--x)`` 必须在 ``src/style.css`` 里定义过；
2. **产物目录对齐**：``.gitignore`` 忽略的构建产物目录必须等于 ``substitute.sh`` 的
   ``get_dist()`` 查表结果（vitepress 必须写全路径 ``docs/.vitepress/dist/``）；
3. **依赖版本对齐**：``package.json.template`` 的版本范围必须等于 ``init-*.sh`` 里
   ``npm install`` 的版本。

依赖：仅 Python 3 标准库，不引入任何第三方包，不访问网络。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tarfile
from pathlib import Path

# ---------------------------------------------------------------------------
# 一、.gitignore 的生成规律
#
# 结构固定为 4 段：标题注释 → 主体块 → （空行 + 分组注释 + 条目）× N
# 「主体块」放框架专属项，通用项（.DS_Store / node_modules/ / .vscode/ / .idea/）
# 按框架实际情况混排其中；纯静态站（portfolio / resume）没有分组块。
# ---------------------------------------------------------------------------

GITIGNORE_SPEC = {
    "hexo": {
        "title": "Hexo",
        "head": [
            ".DS_Store",
            "Thumbs.db",
            "db.json",
            "*.log",
            "node_modules/",
            "public/",
            ".deploy*/",
            "_multiconfig.yml",
        ],
        "groups": [
            ("IDE", [".vscode/", ".idea/", "*.swp", "*.swo"]),
            ("环境", [".env", ".env.local"]),
            ("临时", ["*.tmp", ".cache/"]),
        ],
    },
    "vitepress": {
        "title": "VitePress",
        "head": [
            ".DS_Store",
            "node_modules/",
            "docs/.vitepress/dist/",
            "docs/.vitepress/cache/",
        ],
        "groups": [
            ("IDE", [".vscode/", ".idea/"]),
            ("环境", [".env", ".env.local"]),
        ],
    },
    "vue3": {
        "title": "Vue 3 + Vite",
        "head": [
            ".DS_Store",
            "node_modules/",
            "dist/",
            "dist-ssr/",
        ],
        "groups": [
            ("IDE", [".vscode/", ".idea/"]),
            ("环境", [".env", ".env.local"]),
            (
                "日志",
                [
                    "*.log",
                    "npm-debug.log*",
                    "yarn-debug.log*",
                    "yarn-error.log*",
                    "pnpm-debug.log*",
                ],
            ),
        ],
    },
    "portfolio": {
        "title": "个人作品集",
        "head": [".DS_Store", "node_modules/", ".vscode/", ".idea/"],
        "groups": [],
    },
    "resume": {
        "title": "个人简历站",
        "head": [".DS_Store", ".vscode/", ".idea/"],
        "groups": [],
    },
}

# ---------------------------------------------------------------------------
# 二、package.json.template 的生成规律
#
# 字段顺序固定：name / version / private / description / type / scripts /
# dependencies / devDependencies。name 与 description 用占位符，
# 版本用 ^ 语义化范围且必须与 init 脚本的 npm install 一致。
# ---------------------------------------------------------------------------

PACKAGE_JSON_SPEC = {
    "vitepress": {
        "name": "{{SITE_NAME_SLUG}}",
        "version": "0.0.0",
        "private": True,
        "description": "{{SITE_DESCRIPTION}}",
        "type": "module",
        "scripts": {
            "docs:dev": "vitepress dev docs",
            "docs:build": "vitepress build docs",
            "docs:preview": "vitepress preview docs",
        },
        "dependencies": {},
        "devDependencies": {
            "vitepress": "^1.5.0",
            "vue": "^3.5.0",
        },
    },
    "vue3": {
        "name": "{{SITE_NAME_SLUG}}",
        "version": "0.0.0",
        "private": True,
        "description": "{{SITE_DESCRIPTION}}",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
        },
        "dependencies": {
            "vue": "^3.5.0",
            "vue-router": "^4.4.0",
        },
        "devDependencies": {
            "@vitejs/plugin-vue": "^5.1.0",
            "vite": "^5.4.0",
        },
    },
}

# ---------------------------------------------------------------------------
# 三、.vue 组件的生成规律
#
# Vue 3 SFC 三段式，块顺序固定 <script setup> → <template> → <style scoped>。
# 组件之间只通过两个契约耦合：
#   · 数据源 src/data/tools.js 导出 categories[{ id, name, icon, tools[] }]
#   · 样式全部走 src/style.css 里的 CSS 变量，不写死颜色
# 因此增删导航内容只改 tools.js，不用动组件。
# ---------------------------------------------------------------------------

VUE_COMPONENTS = {
    "src/App.vue": {
        "role": "应用外壳：顶栏 + 路由出口 + 页脚",
        "script": """import HeaderNav from './components/HeaderNav.vue'""",
        "template": """  <div class="app">
    <HeaderNav />
    <main class="main">
      <router-view />
    </main>
    <footer class="footer">
      <div class="container">
        <p>{{SITE_NAME}} · {{YEAR}}</p>
        <p>Made with Vue 3 + Vite</p>
      </div>
    </footer>
  </div>""",
        "style": """.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main {
  flex: 1;
  padding: 2rem 0;
}

.footer {
  background: var(--color-bg-alt);
  border-top: 1px solid var(--color-border);
  padding: 2rem 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.footer p {
  margin: 0.25rem 0;
}""",
    },
    "src/components/HeaderNav.vue": {
        "role": "顶部导航：按 categories 生成分类入口",
        "script": """import { categories } from '../data/tools.js'
import { RouterLink } from 'vue-router'""",
        "template": """  <header class="header">
    <div class="container header-inner">
      <RouterLink to="/" class="logo">{{SITE_NAME}}</RouterLink>
      <nav class="nav">
        <RouterLink
          v-for="cat in categories"
          :key="cat.id"
          :to="`/category/${cat.id}`"
          class="nav-link"
        >
          {{ cat.icon }} {{ cat.name }}
        </RouterLink>
      </nav>
    </div>
  </header>""",
        "style": """.header {
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(8px);
  background-color: rgba(255, 255, 255, 0.8);
}

@media (prefers-color-scheme: dark) {
  .header {
    background-color: rgba(15, 23, 42, 0.8);
  }
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  gap: 2rem;
}

.logo {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
}

.logo:hover {
  color: var(--color-primary);
}

.nav {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.nav-link {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius);
  text-decoration: none;
  transition: all 0.15s;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: var(--color-primary);
  background: var(--color-bg-alt);
  text-decoration: none;
}

@media (max-width: 640px) {
  .header-inner {
    flex-direction: column;
    height: auto;
    padding: 1rem 0;
  }

  .nav {
    gap: 0.5rem;
  }
}""",
    },
    "src/components/ToolCard.vue": {
        "role": "工具卡片：接收单个 tool 对象（name / desc / url）",
        "script": """defineProps({
  tool: {
    type: Object,
    required: true
  }
})""",
        "template": """  <a :href="tool.url" target="_blank" rel="noopener noreferrer" class="card">
    <h3 class="card-name">{{ tool.name }}</h3>
    <p class="card-desc">{{ tool.desc }}</p>
    <span class="card-link">访问 →</span>
  </a>""",
        "style": """.card {
  display: block;
  padding: 1.5rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--color-text);
  transition: all 0.2s;
  box-shadow: var(--shadow);
}

.card:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
  text-decoration: none;
}

.card-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.card-desc {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.card-link {
  color: var(--color-primary);
  font-size: 0.85rem;
  font-weight: 500;
}""",
    },
    "src/views/Home.vue": {
        "role": "首页：按 categories 铺开全部工具",
        "script": """import { categories } from '../data/tools.js'
import ToolCard from '../components/ToolCard.vue'""",
        "template": """  <div class="container">
    <header class="hero">
      <h1>{{SITE_NAME}}</h1>
      <p class="hero-tagline">{{SITE_DESCRIPTION}}</p>
    </header>

    <div v-for="cat in categories" :key="cat.id" class="category-section">
      <h2 class="category-title">
        <span class="category-icon">{{ cat.icon }}</span>
        {{ cat.name }}
      </h2>
      <div class="tools-grid">
        <ToolCard v-for="tool in cat.tools" :key="tool.name" :tool="tool" />
      </div>
    </div>
  </div>""",
        "style": """.hero {
  text-align: center;
  padding: 3rem 0 4rem;
}

.hero h1 {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-tagline {
  font-size: 1.25rem;
  color: var(--color-text-muted);
  max-width: 600px;
  margin: 0 auto;
}

.category-section {
  margin-bottom: 4rem;
}

.category-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.category-icon {
  font-size: 2rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}""",
    },
    "src/views/Category.vue": {
        "role": "分类详情页：按 route.params.id 从 categories 匹配",
        "script": """import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { categories } from '../data/tools.js'
import ToolCard from '../components/ToolCard.vue'

const route = useRoute()
const router = useRouter()

const category = computed(() => {
  return categories.find(c => c.id === route.params.id)
})""",
        "template": """  <div class="container">
    <button class="back-btn" @click="router.push('/')">← 返回首页</button>

    <div v-if="category" class="category-page">
      <h1>
        <span class="icon">{{ category.icon }}</span>
        {{ category.name }}
      </h1>
      <p class="count">共 {{ category.tools.length }} 个工具</p>
      <div class="tools-grid">
        <ToolCard v-for="tool in category.tools" :key="tool.name" :tool="tool" />
      </div>
    </div>

    <div v-else class="not-found">
      <h2>分类不存在</h2>
    </div>
  </div>""",
        "style": """.back-btn {
  background: none;
  border: 1px solid var(--color-border);
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  cursor: pointer;
  color: var(--color-text);
  margin-bottom: 2rem;
  font-size: 0.9rem;
}

.back-btn:hover {
  background: var(--color-bg-alt);
}

.category-page h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.icon {
  font-size: 2.5rem;
  margin-right: 0.5rem;
}

.count {
  color: var(--color-text-muted);
  margin-bottom: 2rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.not-found {
  text-align: center;
  padding: 4rem 0;
  color: var(--color-text-muted);
}""",
    },
}

# 框架标识 ↔ 模板目录名 ↔ init 脚本名的对应关系
FRAMEWORK_DIR = {
    "hexo": "hexo",
    "vitepress": "vitepress",
    "vue3": "vue3-vite",
    "portfolio": "portfolio",
    "resume": "resume",
}


# ---------------------------------------------------------------------------
# 生成函数
# ---------------------------------------------------------------------------


def render_gitignore(spec: dict) -> str:
    """标题 + 主体块 + 分组块；末尾不带换行符。"""
    lines = [f"# {spec['title']}"]
    lines.extend(spec["head"])
    for name, entries in spec["groups"]:
        lines.append("")
        lines.append(f"# {name}")
        lines.extend(entries)
    return "\n".join(lines)


def render_package_json(spec: dict) -> str:
    """标准 package.json，2 空格缩进，末尾不带换行符。

    dependencies / devDependencies 为空时不输出该键 —— 与模板保持一致。
    """
    ordered = {}
    for key in ("name", "version", "private", "description", "type", "scripts"):
        ordered[key] = spec[key]
    for key in ("dependencies", "devDependencies"):
        if spec[key]:
            ordered[key] = spec[key]
    return json.dumps(ordered, indent=2, ensure_ascii=False)


def render_vue(component: dict) -> str:
    """Vue 3 SFC 三段式；末尾不带换行符。"""
    return (
        f"<script setup>\n{component['script']}\n</script>\n"
        f"\n<template>\n{component['template']}\n</template>\n"
        f"\n<style scoped>\n{component['style']}\n</style>"
    )


def build_targets(root: Path) -> dict:
    """返回 {相对路径: 内容} —— 全部 12 个受平台限制的文件。"""
    targets = {}
    for framework, spec in GITIGNORE_SPEC.items():
        directory = FRAMEWORK_DIR[framework]
        targets[f"templates/{directory}/.gitignore"] = render_gitignore(spec)
    for framework, spec in PACKAGE_JSON_SPEC.items():
        directory = FRAMEWORK_DIR[framework]
        targets[f"templates/{directory}/package.json.template"] = render_package_json(spec)
    for relative, component in VUE_COMPONENTS.items():
        targets[f"templates/vue3-vite/{relative}"] = render_vue(component)
    return targets


# ---------------------------------------------------------------------------
# 存储形态：目录形态 vs 归档形态
#
# 目录形态 —— skill 根下有 templates/ 目录（开发态、GitHub 安装）
# 归档形态 —— skill 根下有 templates-<框架>.tar.gz（第三方平台安装）。
#   平台限制压缩包内最多一层子目录，打包脚本会把深层模板转成归档；
#   归档内部保留完整目录结构与隐藏文件，平台扫不到也就过滤不掉。
# 两种形态都要能被本脚本正确识别，否则装包后会误判「文件全丢」。
# ---------------------------------------------------------------------------


def archive_path(root: Path, framework: str) -> Path:
    """某框架的模板归档路径。"""
    return root / f"templates-{FRAMEWORK_DIR[framework]}.tar.gz"


class TemplateStore:
    """受限文件的读取入口，自动适配目录形态与归档形态。"""

    def __init__(self, root: Path):
        self.root = root
        self.archives = {}
        for framework in FRAMEWORK_DIR:
            path = archive_path(root, framework)
            if path.exists():
                self.archives[framework] = path
        self.archived = bool(self.archives)

    def framework_of(self, relative: str) -> str:
        """templates/hexo/.gitignore → hexo"""
        directory = relative.split("/")[1]
        for framework, name in FRAMEWORK_DIR.items():
            if name == directory:
                return framework
        raise KeyError(relative)

    def read(self, relative: str):
        """读 templates/ 下的相对路径内容；不存在返回 None。"""
        if not self.archived:
            path = self.root / relative
            return path.read_text(encoding="utf-8") if path.exists() else None
        archive = self.archives.get(self.framework_of(relative))
        if archive is None:
            return None
        inner = "/".join(relative.split("/")[1:])       # hexo/.gitignore
        with tarfile.open(archive, "r:gz") as handle:
            try:
                member = handle.getmember(inner)
            except KeyError:
                return None
            stream = handle.extractfile(member)
            return stream.read().decode("utf-8") if stream else None

    def write(self, relative: str, content: str) -> bool:
        """写回文件；归档形态下不可直接写（需先展开），返回是否成功。"""
        if self.archived:
            return False
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
        return True


def extract_archives(root: Path, store: "TemplateStore") -> int:
    """把归档展开成目录形态（templates/），便于本地查看与手工修复。"""
    if not store.archived:
        print("当前已是目录形态，无需展开")
        return 0
    target = root / "templates"
    target.mkdir(parents=True, exist_ok=True)
    for framework, archive in sorted(store.archives.items()):
        with tarfile.open(archive, "r:gz") as handle:
            try:
                handle.extractall(target, filter="data")
            except TypeError:                     # Python < 3.12 没有 filter 参数
                handle.extractall(target)
        print(f"  ✅ {archive.name} → templates/{FRAMEWORK_DIR[framework]}/")
    print(f"已展开 {len(store.archives)} 个归档到 {target}")
    return 0


# ---------------------------------------------------------------------------
# 三项自检
# ---------------------------------------------------------------------------


def parse_get_dist(root: Path) -> dict:
    """从 substitute.sh 的 get_dist() 查表里解析框架 → 产物目录。"""
    text = (root / "scripts/substitute.sh").read_text(encoding="utf-8")
    block = re.search(r"get_dist\(\)\s*\{(.*?)\n\}", text, re.S)
    if not block:
        raise ValueError("substitute.sh 里找不到 get_dist() 查表")
    mapping = {}
    for framework, dist in re.findall(r"(\w+)\)\s+echo\s+\"([^\"]+)\"", block.group(1)):
        mapping[framework] = dist
    return mapping


def parse_install_versions(root: Path) -> dict:
    """从 init 脚本的 npm install 命令里解析框架 → {包名: 版本范围}。

    只认 `--save` / `--save-dev` 两种形式；注意 `--save-dev` 必须先判，
    否则会被 `--save` 的子串匹配吃掉。
    """
    result = {}
    for framework, directory in FRAMEWORK_DIR.items():
        script = root / "scripts" / f"init-{framework}.sh"
        if not script.exists():
            continue
        text = script.read_text(encoding="utf-8")
        versions = {}
        for line in text.splitlines():
            if "npm install" not in line:
                continue
            if "--save-dev" in line:
                target = "devDependencies"
            elif "--save" in line:
                target = "dependencies"
            else:
                continue
            for package, version in re.findall(r"(@?[\w./-]+)@(\^[^\s]+)", line):
                versions[package] = (version, target)
        result[framework] = versions
    return result


def check_css_variables(root: Path, targets: dict, store: "TemplateStore") -> list:
    """1) .vue 引用的 var(--x) 必须在 src/style.css 里定义过。"""
    css = store.read("templates/vue3-vite/src/style.css")
    if css is None:
        return ["style.css 不存在，跳过 CSS 变量校验"]
    defined = set(re.findall(r"(--[\w-]+)\s*:", css))
    problems = []
    for relative, content in targets.items():
        if not relative.endswith(".vue"):
            continue
        for name in sorted(set(re.findall(r"var\((--[\w-]+)\)", content))):
            if name not in defined:
                problems.append(f"{relative} 引用了 style.css 里不存在的变量 {name}")
    return problems


def check_dist_dirs(root: Path, targets: dict) -> list:
    """2) .gitignore 的构建产物目录必须等于 get_dist() 的查表结果。"""
    mapping = parse_get_dist(root)
    problems = []
    for framework, directory in FRAMEWORK_DIR.items():
        content = targets.get(f"templates/{directory}/.gitignore")
        if content is None:
            continue
        dist = mapping.get(framework)
        if dist is None:
            problems.append(f"get_dist() 里没有 {framework} 的映射")
            continue
        expected = f"{dist}/" if dist != "." else None
        has = expected is not None and expected in content.splitlines()
        if expected is None:
            # 纯静态站不应出现任何构建产物目录
            for line in content.splitlines():
                if line in ("public/", "dist/", "docs/.vitepress/dist/"):
                    problems.append(f"{directory}/.gitignore 含构建产物行 {line}，但 get_dist={framework} 是 '.'")
        elif not has:
            problems.append(f"{directory}/.gitignore 缺少构建产物目录 {expected}（get_dist {framework}={dist}）")
    return problems


def check_dependency_versions(root: Path, targets: dict) -> list:
    """3) package.json.template 的版本范围必须等于 init 脚本 npm install 的版本。"""
    installed = parse_install_versions(root)
    problems = []
    for framework, spec in PACKAGE_JSON_SPEC.items():
        expected = installed.get(framework, {})
        actual = {}
        actual.update(spec["dependencies"])
        actual.update(spec["devDependencies"])
        for package, (version, _target) in expected.items():
            if package not in actual:
                problems.append(f"{framework}/package.json.template 缺少依赖 {package}（init 脚本会装 {version}）")
            elif actual[package] != version:
                problems.append(
                    f"{framework}/package.json.template 的 {package} 是 {actual[package]}，"
                    f"但 init 脚本装的是 {version}"
                )
        for package in actual:
            if package not in expected:
                problems.append(f"{framework}/package.json.template 多出依赖 {package}，init 脚本不会装它")
    return problems


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="按规律重建受平台限制的模板文件")
    default_root = Path(__file__).resolve().parent.parent
    parser.add_argument("--target", default=str(default_root), help="skill 根目录（默认本脚本上级）")
    parser.add_argument("--check", action="store_true", help="只检查，不写文件")
    parser.add_argument("--force", action="store_true", help="强制重建全部（默认只补缺失的）")
    parser.add_argument("--quiet", action="store_true", help="只输出结果，不打印每个文件")
    parser.add_argument("--extract", action="store_true", help="归档形态下把 templates-*.tar.gz 展开成 templates/ 目录")
    args = parser.parse_args()

    root = Path(args.target).resolve()
    if not (root / "SKILL.md").exists():
        print(f"✗ 不是 skill 根目录（缺 SKILL.md）：{root}", file=sys.stderr)
        return 2

    store = TemplateStore(root)
    if args.extract:
        return extract_archives(root, store)

    targets = build_targets(root)

    # 自检：任何一项不通过都不写文件，避免把坏模板写进包里
    problems = []
    problems.extend(check_css_variables(root, targets, store))
    problems.extend(check_dist_dirs(root, targets))
    problems.extend(check_dependency_versions(root, targets))
    if problems:
        print("✗ 自检未通过，未写入任何文件：")
        for problem in problems:
            print(f"  · {problem}")
        return 1

    missing, drifted, same = [], [], []
    for relative, content in targets.items():
        current = store.read(relative)
        if current is None:
            missing.append((relative, content))
        elif current != content:
            drifted.append((relative, content))
        else:
            same.append(relative)

    mode = "归档形态（模板以 templates-*.tar.gz 分发）" if store.archived else "目录形态"
    if args.check:
        print(f"检查 {root} · {mode}")
        print(f"  ✅ 一致 {len(same)} 个")
        print(f"  ❌ 缺失 {len(missing)} 个")
        for relative, _ in missing:
            print(f"      · {relative}")
        print(f"  ⚠️  漂移 {len(drifted)} 个（磁盘内容 ≠ 生成器产出）")
        for relative, _ in drifted:
            print(f"      · {relative}")
        return 1 if (missing or drifted) else 0

    if store.archived and (missing or drifted):
        print("归档形态下不能就地改写 tar 内容。请先展开成目录形态再重建：")
        print(f"    python3 scripts/gen-restricted-files.py --extract")
        print("（展开后重新执行本脚本即可补齐；或重新获取安装包）")
        return 1

    to_write = list(targets.items()) if args.force else missing
    written = 0
    for relative, content in to_write:
        if not store.write(relative, content):
            continue
        written += 1
        if not args.quiet:
            print(f"  ✅ {relative}")

    # 写入后复核：以磁盘实际内容为准，而不是写入前的快照
    remaining = []
    for relative, content in targets.items():
        current = store.read(relative)
        if current is None:
            remaining.append((relative, "仍然缺失"))
        elif current != content:
            remaining.append((relative, "内容与生成器产出不一致"))

    print("")
    print(f"受限文件 {len(targets)} 个 —— 写前齐 {len(same)}，缺 {len(missing)}，漂移 {len(drifted)}")
    print(f"本次写入 {written} 个" + ("（--force 全量重建）" if args.force else "（仅补缺失）"))
    print("自检 3 项全部通过：CSS 变量闭环 / 产物目录对齐 get_dist / 依赖版本对齐 init 脚本")

    if remaining:
        print("")
        print(f"⚠️  复核未通过（{len(remaining)} 个），请手动核对：")
        for relative, reason in remaining:
            print(f"    · {relative} —— {reason}")
        return 1
    print(f"复核通过：{len(targets)} 个受限文件全部就位")
    return 0


if __name__ == "__main__":
    sys.exit(main())