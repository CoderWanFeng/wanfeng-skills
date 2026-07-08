// 示例 AI 工具数据
// 你可以自由编辑、添加、删除

export const categories = [
  {
    id: 'chat',
    name: 'AI 对话',
    icon: '💬',
    tools: [
      {
        name: 'ChatGPT',
        desc: 'OpenAI 的大语言模型，支持对话、写作、编程',
        url: 'https://chat.openai.com'
      },
      {
        name: 'Claude',
        desc: 'Anthropic 开发的 AI 助手，长文本处理强',
        url: 'https://claude.ai'
      },
      {
        name: 'Gemini',
        desc: 'Google 的多模态 AI 模型',
        url: 'https://gemini.google.com'
      }
    ]
  },
  {
    id: 'image',
    name: 'AI 图像',
    icon: '🎨',
    tools: [
      {
        name: 'Midjourney',
        desc: '顶级 AI 绘画工具，风格艺术感强',
        url: 'https://midjourney.com'
      },
      {
        name: 'Stable Diffusion',
        desc: '开源 AI 绘画，可本地部署',
        url: 'https://stability.ai'
      },
      {
        name: 'DALL·E 3',
        desc: 'OpenAI 的图像生成模型',
        url: 'https://openai.com/dall-e-3'
      }
    ]
  },
  {
    id: 'code',
    name: 'AI 编程',
    icon: '💻',
    tools: [
      {
        name: 'GitHub Copilot',
        desc: 'GitHub 和 OpenAI 联合推出的 AI 编程助手',
        url: 'https://github.com/features/copilot'
      },
      {
        name: 'Cursor',
        desc: 'AI-first 的代码编辑器',
        url: 'https://cursor.sh'
      },
      {
        name: 'v0.dev',
        desc: 'Vercel 推出的 UI 生成 AI',
        url: 'https://v0.dev'
      }
    ]
  },
  {
    id: 'writing',
    name: 'AI 写作',
    icon: '✍️',
    tools: [
      {
        name: 'Notion AI',
        desc: 'Notion 内置的 AI 写作助手',
        url: 'https://notion.so'
      },
      {
        name: 'Jasper',
        desc: '面向营销的 AI 内容生成',
        url: 'https://jasper.ai'
      }
    ]
  }
]