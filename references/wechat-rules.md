# 公众号 HTML 规则与交付

## 编辑器会吃掉什么

公众号编辑器粘贴时只保留元素上的内联 `style`，所以：

- **只用内联样式**。不要 `<style>`、`class`、`id` 选择器、外部 CSS、网络字体、`<script>`。
- 布局只用 `section` / `p` / `span` / `table` + `display:inline-block`、`float`、`margin/padding`。不要 flex、grid、position、伪元素、CSS 变量、`calc()`。
- 内联 `<svg>`（circle / path）可以用，图标和 HA 标志都是这样画的。
- 不要外链：正文链接不可点，build.py 会把 `[文字](网址)` 渲染成文字 + 网址。
- 图片宽度用 `width:100%`，圆角 6px。

## 图片

- 图片转成 `data:` URI 内嵌，粘贴时公众号会自动转存到素材库，不需要手动上传。粘贴后要等所有图片转存完成再保存。
- 体积预算：预览页必须 < 16MB（Artifact/网页发布上限），所以整篇图片合计 ≈ 10MB；单张 GIF 300KB–1MB。
- GIF 参数：宽 520px、10fps、3–4 秒。管线：`ffmpeg hqdn3d 去噪 → palettegen/paletteuse dither=none → gifsicle -O3 --lossy=100`，就是 `scripts/make_gif.sh`。胶片颗粒类画面最重，可降到 8fps / 480px。
- 截图用 JPG（质量 80 左右）或 PNG，宽 1080px 以内。

## 交付物

一篇文章一个文件夹：

```
<slug>/
  article.md               稿件
  images/                  单独的图片（方便用户另存）
  <slug>-article.html      正文片段（给要源码的人 / 其他工具）
  <slug>-preview.html      预览页：手机宽度预览 +「复制排版」「复制 HTML 源码」
```

用户的操作：打开预览页 → 点「复制排版」→ 公众号后台新建图文 → 粘贴到正文 → 填预览页上给出的标题和摘要。

「复制排版」用 `ClipboardItem` 同时写入 `text/html` 和 `text/plain`；浏览器不允许时退回到选中内容 + `execCommand('copy')`，再不行提示用户按 ⌘/Ctrl + C。
