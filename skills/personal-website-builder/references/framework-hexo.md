# Hexo 框架详解

## 为什么选 Hexo

- **Node.js 生态**：中文文档最完善，社区最活跃
- **主题丰富**：500+ 主题可选（Hexo Themes）
- **部署简单**：`hexo generate` → `hexo deploy` 一条龙
- **Markdown 优先**：和程序员习惯高度契合

## 核心概念

- **scaffolds/**：文章模板（draft.md、post.md、page.md）
- **source/**：源文件（Markdown、图片、未渲染的 HTML）
- **public/**：构建产物（最终上传到服务器的内容）
- **themes/**：主题目录
- **_config.yml**：主配置
- **_config.{theme}.yml**：主题独立配置（推荐放在根目录）

## init-hexo.sh 做了什么

```bash
1. npx --yes hexo init . --no-install    # 初始化结构
2. npm install                            # 安装 Hexo 默认依赖
3. npm install --save hexo-theme-butterfly hexo-renderer-pug hexo-renderer-stylus
4. cp node_modules/hexo-theme-butterfly/_config.yml _config.butterfly.yml
5. rm -f source/_posts/hello-world.md
6. 复制欢迎文章（中英双语）并替换占位符
7. 复制 _config.yml 模板并替换占位符
8. 复制 README.md 模板并替换占位符
9. git init -b main + 复制 .gitignore
```

## 已知坑

### 1. 主题更新会覆盖 `_config.yml`

**坑**：`node_modules/hexo-theme-butterfly/_config.yml` 升级主题后会被覆盖。
**解**：在 Hexo 根目录创建 `_config.butterfly.yml`，Hexo 优先使用这个文件而非主题内的。

本 skill 已经做了这步（脚本第 4 步）。

### 2. `hexo deploy` 不会自动安装 deployer

需要单独装：
```bash
npm install --save hexo-deployer-git    # 部署到 GitHub
npm install --save hexo-deployer-heroku  # 部署到 Heroku
```

### 3. 资源文件夹（图片）

默认 `post_asset_folder: false`。开启后：
```yaml
post_asset_folder: true
```
然后 `npx hexo new "post"`，会在同目录生成 `post/` 文件夹，放图片用 `![](post/image.png)` 引用。

## 常用插件

| 插件 | 作用 |
|------|------|
| `hexo-blog-encrypt` | 文章加密 |
| `hexo-abbrlink` | 自定义永久链接 |
| `hexo-wordcount` | 字数统计 |
| `hexo-generator-sitemap` | 生成 sitemap |
| `hexo-deployer-git` | Git 部署 |
| `hexo-algoliasearch` | Algolia 搜索 |

## 升级版本

```bash
npm update                    # 升级所有依赖
npm install --save hexo@latest  # 升级 Hexo 主程序
```

升级前看 [CHANGELOG](https://github.com/hexojs/hexo/releases)，新版可能有 breaking changes。

## 进一步学习

- [Hexo 官方文档](https://hexo.io/docs/)
- [Butterfly 主题文档](https://butterfly.js.org/)
- [Hexo 主题列表](https://hexo.io/themes/)