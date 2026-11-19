# 发布前脱敏检查清单

截图和文章在发布前，必须逐项确认以下信息已经处理。

---

## 截图脱敏

### 必须去除（出现任何一项都不能发）

- [ ] 真实姓名（身份证上的名字、后台"真实姓名"字段）
- [ ] 个人头像（右上角账号头像、评论区头像）
- [ ] 手机号、邮箱地址
- [ ] 账号 ID / 用户标识（如 `os_xxx`、`user_xxx`、`uid_xxx` 等内部编号）
- [ ] 身份证号、银行卡号
- [ ] 真实订单号、交易流水号
- [ ] 内部系统 URL（带 token 或签名的管理后台地址）
- [ ] 浏览器书签栏（可能含个人账号名）
- [ ] 微信/钉钉等即时通讯的个人昵称与头像

### 可以保留（属于公开信息）

- [x] 产品/平台的公开品牌名
- [x] 开发者对外展示的公开昵称（如平台上的"程序员晚枫"）
- [x] 公开价格、版本号
- [x] 功能描述文字
- [x] 平台 Logo 和 UI 界面元素

### 遮盖方法

**白色矩形覆盖**（最常用，适合纯色背景区域）：

```python
from PIL import Image, ImageDraw

img = Image.open('screenshot.png').convert('RGB')
draw = ImageDraw.Draw(img)
# 用白色覆盖敏感区域，坐标根据实际图片调整
draw.rectangle([x1, y1, x2, y2], fill='#FFFFFF')
img.save('screenshot_clean.jpg', quality=94)
```

**高斯模糊**（适合背景复杂的区域）：

```python
from PIL import Image, ImageDraw, ImageFilter

img = Image.open('screenshot.png').convert('RGB')
region = img.crop((x1, y1, x2, y2))
blurred = region.filter(ImageFilter.GaussianBlur(radius=15))
img.paste(blurred, (x1, y1))
img.save('screenshot_clean.jpg', quality=94)
```

**裁剪**（如果敏感信息在画面边缘，直接裁掉更干净）：

```python
img = Image.open('screenshot.png')
cropped = img.crop((x1, y1, x2, y2))  # 只保留必要区域
```

### 脱敏后必做

- [ ] 逐张打开目检：确认敏感信息完全消失
- [ ] 确认关键信息仍然可见：价格、功能名、版本号没有被误盖
- [ ] 遮盖框不要盖住文章需要引用的内容（如 ¥9 价格标签）
- [ ] 如果遮盖框坐标不准导致残留，调整坐标重新生成

---

## 文章脱敏

### 正文中不能出现

- [ ] 作者的真实邮箱、手机号
- [ ] 图床账号的 Token、密钥或配置路径
- [ ] 本地绝对路径（如 `/Users/xxx/...`）
- [ ] 未公开的内部系统地址
- [ ] 其他人的个人隐私信息（未经授权的截图、对话记录）

### 可以出现

- [x] 公开的产品官网 URL
- [x] 官方文档链接
- [x] 公开的 GitHub 仓库地址
- [x] 平台公开的品牌名和产品名
- [x] 作者自己的公开昵称（对外展示名）

---

## 链接安全检查

- [ ] 所有图片 URL 都能公开访问（不需要登录、没有过期签名参数）
- [ ] 分享链接（带 `sig=` 或 `token=` 参数的）确认有效期
- [ ] 参考链接都是官方/权威来源，不是临时预览地址
- [ ] 没有 `localhost`、`127.0.0.1` 或内网地址
