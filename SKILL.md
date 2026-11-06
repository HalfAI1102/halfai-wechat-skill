---
name: halfai-wechat-layout
description: HalfAI 公众号图文排版：把稿件（Markdown）排成墨黑/纸白/Half 绿风格、全内联样式、图片内嵌的公众号 HTML，并生成带「复制排版」按钮的预览页。用户说"排版""公众号排版""做成公众号文章""按我的模板排"时使用。
---

# HalfAI 公众号排版 skill

把一篇稿子变成可以直接粘贴进公众号后台的图文。这里汇总的都是用户已经确认过的做法，**直接照做，不要再出多套备选**，除非用户要求。

文件索引：
- `scripts/build.py`：排版器。Markdown 稿 → `<slug>-article.html`（正文片段）+ `<slug>-preview.html`（预览页 + 复制按钮）。只依赖 Python 3 标准库。
- `scripts/make_gif.sh`：视频 → 公众号用 GIF（ffmpeg，可选 gifsicle）。
- `references/components.md`：稿件语法和全部组件（**写稿前先读**）。
- `references/style.md`：品牌视觉规范和写作规则。
- `references/wechat-rules.md`：公众号 HTML 的限制、图片体积预算、粘贴流程。
- `examples/demo/article.md`：用到了所有组件的示例稿；`demo-preview.html` 是它排出来的样子。
- `assets/`：HA 标志路径（`ha_path.txt`）、HA logo PNG、像素风品牌横幅（`halfai-pixel-banner.gif`）、预览页外壳。

## 标准流程

1. **拿到稿子**：用户给的口播稿/草稿先清洗成书面语（只顺句子，不改观点），按 `references/style.md` 的写作规则检查。
2. **建文件夹**：`<slug>/article.md` + `<slug>/images/`。图片文件名用英文短横线（`find-skills.gif`）。
3. **配图**：用户要的是真实截图/实际跑出来的动图，不是图库图、不是占位。视频转 GIF 用 `scripts/make_gif.sh`；整篇图片合计控制在约 10MB。暂时没有的图照写 `![说明](images/xxx.gif "图注")`，排版器会放一个灰色「图位」占位并在输出里提示，补图后重跑即可。
4. **品牌横幅（按需启用）**：需要展示 HalfAI 像素风品牌动画时，在 front matter 设置 `brand_banner: yes`。排版器自动在片头卡、作者条之后插入 `assets/halfai-pixel-banner.gif`（900×383，循环动图，内嵌到 HTML）。默认不插入，不要重复在正文里引用同一动图。
5. **写 article.md**：front matter 填标题两行、eyebrow、日期、摘要；正文用 `references/components.md` 里的语法。
6. **排版**：`python3 scripts/build.py <slug>/article.md`。看终端的 WARN（缺图、体积超限、未知组件）。
7. **自查**：用浏览器打开 `<slug>-preview.html` 看一遍手机宽度效果（能截图就截图看）。
8. **交付**：把预览页给用户（能发布网页/Artifact 就发布成页面，用户在页面上点「复制排版」→ 公众号后台粘贴）。同时给出标题和摘要。

## 最重要的规则（每次都检查）

1. **只用一种强调色**：Half 绿 `#2BE08C`（深色底）/ 深绿 `#0F6B44`（纸白底）。其余只有墨黑、白、灰、纸白。
2. **标题两行**：第一行白字说事实，第二行灰字给观点。片尾固定「今天就到这。/ 剩下的一半，下期讲。」
3. **HA 标志必须出现**在片头卡、作者条、片尾，永远是白色，放在墨黑底上；不要用半圆替代 logo。build.py 已自动处理。
4. **像素横幅可选**：使用 `brand_banner: yes` 时必须保留原图的 HA Logo、像素人物、猫咪、绿色 `AI` 和 `上限` 以及完整标语「让 AI 成为你的下限，你来决定上限。」；禁止再生成或重画该素材。
5. **每段最多一个**深绿加粗关键词（`**...**`），全篇最关键的几句才用绿色下划线（`==...==`）。
6. **图片内嵌**：所有图都转成 base64 写进 HTML，复制排版时一起带走，不给用户留占位。
7. **全部内联样式**：不要 `<style>`、class、外部 CSS/字体、JS、flex/grid、外链。自己加 HTML 时同样遵守（见 `references/wechat-rules.md`）。
8. 预览页总大小 **< 15MB**（发布网页的上限是 16MB），超了就压 GIF。
9. 写作：不用感叹号；小标题 ≤ 10 个字；不堆形容词，写实测数据（耗时、花费、结果）。

## 给其他 agent 的最短用法

```bash
python3 scripts/build.py path/to/article.md            # 输出到稿件同目录
python3 scripts/build.py path/to/article.md -o out/ --name my-post
```

不能跑 Python 的环境：照 `examples/demo/demo-article.html` 的结构手写内联样式 HTML，规则同上。
