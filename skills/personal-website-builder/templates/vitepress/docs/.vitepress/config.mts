import { defineConfig } from 'vitepress'

export default defineConfig({
  title: '{{SITE_NAME}}',
  description: '{{SITE_DESCRIPTION}}',
  lang: 'zh-CN',
  lastUpdated: true,
  cleanUrls: true,

  // VitePress 1.6+ 的死链检查太严格，忽略本地地址
  ignoreDeadLinks: [/^http:\/\/localhost:/],

  themeConfig: {
    siteTitle: '{{SITE_NAME}}',

    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide/getting-started' }
    ],

    sidebar: [
      {
        text: '入门',
        items: [
          { text: '开始使用', link: '/guide/getting-started' }
        ]
      }
    ],

    socialLinks: [
      {{GITHUB_OR_EMPTY}}{ icon: 'github', link: 'https://github.com/{{GITHUB_USERNAME}}' }
    ],

    footer: {
      message: '基于 VitePress 构建',
      copyright: 'Copyright © {{YEAR}} {{AUTHOR_NAME_OR_DEFAULT}}'
    },

    search: {
      provider: 'local'
    }
  }
})