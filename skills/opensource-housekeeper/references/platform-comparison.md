# 开源平台对比（GitHub vs AtomGit vs Gitee）

> 用户问「该用哪个」时，把这份表给 TA 看。

## 三大平台一览

| 维度 | GitHub | AtomGit | Gitee（码云） |
|---|---|---|---|
| **总部** | 美国（微软旗下） | 中国（CSDN/中科方德） | 中国（OSChina） |
| **网址** | github.com | atomgit.com | gitee.com |
| **国内访问** | 经常抽风，需代理 | 顺畅 | 顺畅 |
| **国际访问** | 顺畅 | 较慢 | 不稳定 |
| **核心用户群** | 全球开源主流 | 国内政企 / 国产生态 | 国内个人开发者 |
| **Git 命令兼容性** | 原生 | 完全兼容 | 完全兼容 |
| **免费私有仓** | ✅ 无限 | ✅ 有限额 | ✅ 有限额 |
| **Star 体系** | 主流认可度高 | 国内社区认知中等 | 国内社区认知中等 |
| **CI/CD** | GitHub Actions | 内置 CI | Gitee Go |
| **大文件存储** | Git LFS（1GB 免费） | 略 | Git LFS（受限） |
| **国产生态绑定** | 无 | ✅ 鸿蒙 / openEuler 等 | 一般 |

## 推荐决策树

```
你的项目主要给谁看？
├── 国外开发者 / 国际开源协作 → ⭐ GitHub
├── 国内开发者 / 政企合作 / 国产生态 → ⭐ AtomGit
└── 国内个人项目 / 已经在用 Gitee → ⭐ Gitee
```

## Gitee 特别说明（国内小白最常踩的坑）

| 注意点 | 说明 |
|---|---|
| **实名认证** | 2022 年起创建 Public 仓库需要实名（身份证 + 人脸） |
| **免费额度** | 单仓库 ≤ 500MB，单文件 ≤ 50MB，超出走 Gitee Go 或付费 |
| **同步限制** | 从 GitHub 同步到 Gitee 有 5 分钟延迟（Push 触发） |
| **企业版广告** | 免费版在仓库页有「企业版推荐」banner，可忽略 |
| **联系方式** | 注册只需手机号（不像 GitHub 必须邮箱） |
| **国际化** | 仓库地址在国内访问速度最稳，但海外用户访问慢 |

## 同时推两个平台（推荐：双备份）

一份代码同时推到 GitHub + AtomGit，国内国外都顺：

```bash
git remote add github  git@github.com:用户名/仓库名.git
git remote add atomgit git@atomgit.com:用户名/仓库名.git
git remote add gitee   git@gitee.com:用户名/仓库名.git

# 推送到任意平台
git push github  main
git push atomgit main
git push gitee   main
```

⚠️ 注意：两边都要建空仓库（不要勾 README），且 `main` 分支结构要一致。

## 三个平台的「建空仓库」入口

| 平台 | URL |
|---|---|
| GitHub | https://github.com/new |
| AtomGit | https://atomgit.com/new |
| Gitee | https://gitee.com/projects/new |

> ⚠️ **创建时的关键点**：下面的勾**全部不选**：
> - ❌ Add a README file
> - ❌ Add .gitignore
> - ❌ Choose a license
>
> 否则会和本地冲突，push 会失败。

## 仓库名规范（建议）

- ✅ 全小写英文 + 短横线：`my-awesome-tool`、`react-component-lib`
- ❌ 不要用空格：`My Project` ❌
- ❌ 不要用中文：`我的项目` ❌（有些工具会乱码）
- ❌ 不要用下划线开头：`_private` ❌
- 💡 项目名 = 用户最容易搜索到的关键词

## 隐私 & 安全

| 场景 | 建议 |
|---|---|
| 学习项目 / 练手 | Public，放心 |
| 含个人信息 / 公司代码 | **Private**（先私有，未来再考虑公开） |
| 含密钥 / 密码 | **绝对不要 push**，先放进 `.gitignore` 或环境变量 |
| 误推了密钥 | 立刻去平台 `Revoke` + 改密码 + `git filter-branch` 清除历史 |
