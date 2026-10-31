#!/usr/bin/env python3
"""HalfAI 公众号排版：把一篇 Markdown 稿件排成可直接粘贴进公众号后台的 HTML。

用法:
    python3 scripts/build.py path/to/article.md [-o OUT_DIR] [--name SLUG]

输出（默认写到 article.md 所在目录）:
    <slug>-article.html   正文片段，全部内联样式，图片已转成 base64 内嵌
    <slug>-preview.html   预览页：手机宽度预览 + 「复制排版」/「复制 HTML 源码」按钮

只用 Python 3 标准库，任何 agent / 任何机器都能跑。语法见 references/components.md。
"""
import argparse
import base64
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')

# ---------------------------------------------------------------- 颜色与字体
INK = '#090A09'        # 墨黑
WHITE = '#F2F3F1'      # 白
GRAY = '#7D837F'       # 灰（观点行、注释）
LINE = '#2A2E2B'       # 深色卡上的线
PAPER = '#F2F1EC'      # 纸白底
GREEN = '#2BE08C'      # Half 绿（深色底上用）
DEEP = '#0F6B44'       # 深绿（纸白底上用）
BODY = '#1E2320'       # 正文字色
SUB = '#59605B'        # 次级正文
RULE = '#DCDDD7'       # 浅分隔线
FILL = '#E7E6E0'       # 占位、行内代码底
MONO = "font-family:Menlo,Consolas,'SF Mono',monospace;"
SANS = ("font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Noto Sans SC',"
        "'Hiragino Sans GB','Microsoft YaHei',sans-serif;")

HA_PATH = open(os.path.join(ASSETS, 'ha_path.txt')).read().strip()
WARN = []


# ---------------------------------------------------------------- 图形
def ha(size, va):
    """HalfAI 的 HA 标志，永远是白色（#F2F3F1），只放在深色底上。"""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 344.5 347.8" '
            f'style="display:inline-block;vertical-align:{va}px;">'
            f'<path fill-rule="evenodd" fill="{WHITE}" d="{HA_PATH}"/></svg>')


def circle(size, kind='half', color=DEEP):
    """半圆母题：kind = empty / half / full。"""
    r = size / 2 - 1
    c = size / 2
    s = (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
         f'style="display:inline-block;vertical-align:-2px;">')
    if kind == 'full':
        return s + f'<circle cx="{c}" cy="{c}" r="{r}" fill="{color}" stroke="{color}" stroke-width="1.6"/></svg>'
    s += f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{color}" stroke-width="1.6"/>'
    if kind == 'half':
        s += f'<path d="M{c} {c - r}A{r} {r} 0 0 0 {c} {c + r}Z" fill="{color}"/>'
    return s + '</svg>'


def kicker(text, color=DEEP):
    return f'<span style="{MONO}font-size:11px;letter-spacing:1.5px;color:{color};">{text}</span>'


# ---------------------------------------------------------------- 行内语法
def inline(t, dark=False):
    """**粗** → 深绿加粗；==重点== → 绿色下划线；`代码`；[文字](链接)。"""
    codes = []

    def keep(m):
        codes.append(m.group(1))
        return f'\x00{len(codes) - 1}\x00'

    t = re.sub(r'`([^`]+)`', keep, t)
    if dark:
        t = re.sub(r'\*\*(.+?)\*\*', rf'<strong style="color:{WHITE};font-weight:700;">\1</strong>', t)
        t = re.sub(r'==(.+?)==', r'<span style="border-bottom:2px solid #2BE08C;color:#FFFFFF;">\1</span>', t)
    else:
        t = re.sub(r'\*\*(.+?)\*\*', rf'<strong style="color:{DEEP};font-weight:700;">\1</strong>', t)
        t = re.sub(r'==(.+?)==', rf'<span style="border-bottom:2px solid {GREEN};padding-bottom:1px;'
                   rf'font-weight:600;color:{INK};">\1</span>', t)
    # 公众号正文不能放外链：显示成绿色文字 + 灰色等宽网址
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
               rf'<span style="color:{DEEP};font-weight:600;">\1</span>'
               rf'<span style="{MONO}font-size:12px;color:{GRAY};word-break:break-all;">（\2）</span>', t)

    def put(m):
        c = html.escape(codes[int(m.group(1))])
        if dark:
            return f'<span style="{MONO}font-size:13px;background:#1B1F1C;color:{GREEN};padding:1px 5px;border-radius:3px;">{c}</span>'
        return f'<span style="{MONO}font-size:13px;background:{FILL};color:{INK};padding:1px 5px;border-radius:3px;">{c}</span>'

    return re.sub(r'\x00(\d+)\x00', put, t)


def split(line, n):
    parts = [x.strip() for x in line.split('|')]
    return parts + [''] * (n - len(parts))


# ---------------------------------------------------------------- 组件
def header(m):
    eyebrow = m.get('eyebrow', 'AI 实测')
    left = m.get('bar_left', eyebrow.split('·')[0].strip() or 'HALFAI')
    return f'''  <!-- 片头卡 -->
  <section style="margin:0 0 22px;padding:22px 20px 18px;background:{INK};border-radius:6px;">
    <p style="margin:0 0 18px;line-height:1;">{ha(16, -3)}<span style="margin-left:7px;font-size:12px;font-weight:600;color:{WHITE};vertical-align:0;">HalfAI</span></p>
    <p style="margin:0 0 10px;">{kicker(eyebrow, GREEN)}</p>
    <p style="margin:0;font-size:26px;font-weight:900;line-height:1.3;letter-spacing:-1px;color:{WHITE};">{m.get('title', '标题第一行，说事实，')}</p>
    <p style="margin:0;font-size:26px;font-weight:900;line-height:1.3;letter-spacing:-1px;color:{GRAY};">{m.get('title2', '第二行，给观点')}</p>
    <section style="margin:22px 0 0;line-height:1;">
      <span style="{MONO}font-size:10px;color:{GRAY};">{left}</span>
      <span style="display:inline-block;width:55%;height:2px;margin:0 10px;background:{LINE};vertical-align:middle;"><span style="display:block;width:30%;height:2px;background:{GREEN};"></span></span>
      <span style="{MONO}font-size:10px;color:{GRAY};">{m.get('date', '')}</span>
    </section>
  </section>

  <!-- 作者条 -->
  <section style="margin:0 0 26px;line-height:1.4;">
    <span style="display:inline-block;width:34px;height:34px;line-height:34px;border-radius:6px;background:{INK};text-align:center;vertical-align:middle;">{ha(20, -4)}</span><span style="display:inline-block;margin-left:10px;vertical-align:middle;"><span style="display:block;font-size:15px;font-weight:800;color:{INK};">{m.get('author', 'HalfAI')}</span><span style="display:block;font-size:12px;color:{GRAY};">{m.get('author_desc', 'AI 工具实测 · 每周更新')}</span></span>
  </section>

'''


def footer(m):
    extra = ''
    for key, label in (('next', '下一期'), ('prev', '往期')):
        if m.get(key):
            extra += (f'    <section style="margin:0 0 8px;padding:12px 14px;background:#151816;border:1px solid #262A27;border-radius:4px;">\n'
                      f'      <p style="margin:0;{MONO}font-size:10px;color:{GRAY};">{label}</p>\n'
                      f'      <p style="margin:0;font-size:14px;font-weight:700;color:{WHITE};">{m[key]}</p>\n    </section>\n')
    return f'''
  <!-- 片尾 -->
  <section style="margin:30px 0 0;padding:22px 20px;background:{INK};border-radius:6px;">
    <p style="margin:0;font-size:20px;font-weight:900;line-height:1.35;color:{WHITE};">{m.get('ending', '今天就到这。')}</p>
    <p style="margin:0 0 18px;font-size:20px;font-weight:900;line-height:1.35;color:{GRAY};">{m.get('ending2', '剩下的一半，下期讲。')}</p>
{extra}    <p style="margin:{'10px' if extra else '0'} 0 0;text-align:center;line-height:1.4;">{ha(18, -4)}<span style="margin-left:8px;font-size:14px;font-weight:700;color:{WHITE};">关注 HalfAI</span><span style="font-size:12px;color:{GRAY};">　点上方名片即可关注</span></p>
  </section>
'''


def para(t, lead=False):
    if lead:
        return f'  <p style="margin:0 0 18px;font-size:16px;line-height:1.8;color:{BODY};">{inline(t)}</p>\n'
    return f'  <p style="margin:0 0 18px;">{inline(t)}</p>\n'


def chapter(n, title, sub=''):
    s = (f'  <section style="margin:40px 0 18px;">\n'
         f'    <section style="display:inline-block;vertical-align:middle;width:64px;height:64px;line-height:64px;background:{GREEN};color:{INK};text-align:center;font-size:30px;font-weight:800;letter-spacing:-1px;border-radius:2px;">{n:02d}</section>'
         f'<section style="display:inline-block;vertical-align:middle;margin-left:14px;max-width:70%;">\n'
         f'      <p style="margin:0;">{kicker(f"CHAPTER {n:02d}")}</p>\n'
         f'      <p style="margin:2px 0 0;font-size:21px;font-weight:900;line-height:1.3;letter-spacing:-0.5px;color:{INK};">{inline(title)}</p>\n')
    if sub:
        s += f'      <p style="margin:2px 0 0;font-size:13px;color:{GRAY};">{inline(sub)}</p>\n'
    return s + '    </section>\n  </section>\n'


def item(label, n, total, name, sub='', tag=''):
    s = (f'  <section style="margin:38px 0 14px;padding:0 0 10px;border-bottom:2px solid {INK};">\n'
         f'    <p style="margin:0 0 4px;line-height:1.4;">{circle(12)}<span style="margin-left:7px;">{kicker(f"{label} {n:02d} / {total:02d}")}</span>'
         + (f'<span style="float:right;font-size:12px;color:{GRAY};">{inline(tag)}</span>' if tag else '') + '</p>\n'
         f'    <p style="margin:0;font-size:20px;font-weight:900;line-height:1.35;color:{INK};">{inline(name)}</p>\n')
    if sub:
        s += f'    <p style="margin:2px 0 0;{MONO}font-size:13px;color:{SUB};">{sub}</p>\n'
    return s + '  </section>\n'


def subhead(label, n, name, right=''):
    return (f'  <p style="margin:30px 0 8px;line-height:1.4;">{circle(12)}'
            f'<span style="margin-left:7px;">{kicker(f"{label} {n:02d}")}</span>'
            f'<span style="margin-left:8px;font-size:16px;font-weight:900;color:{INK};">{inline(name)}</span>'
            + (f'<span style="margin-left:6px;font-size:12px;color:{GRAY};">{inline(right)}</span>' if right else '') + '</p>\n')


MIME = {'.gif': 'image/gif', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}


def image(base, alt, src, cap):
    bottom = 8 if cap else 24
    path = src if os.path.isabs(src) else os.path.join(base, src)
    if not os.path.splitext(path)[1]:  # 没写扩展名时按 gif/jpg/png 依次找
        for ext in ('.gif', '.jpg', '.png', '.jpeg', '.webp'):
            if os.path.exists(path + ext):
                path += ext
                break
    if os.path.isfile(path):
        mime = MIME.get(os.path.splitext(path)[1].lower(), 'image/png')
        data = base64.b64encode(open(path, 'rb').read()).decode()
        s = (f'  <p style="margin:24px 0 {bottom}px;text-align:center;line-height:0;">'
             f'<img src="data:{mime};base64,{data}" alt="{html.escape(alt)}" '
             f'style="display:block;width:100%;height:auto;margin:0 auto;border-radius:6px;"></p>\n')
    else:
        WARN.append(f'图片缺失，已放占位：{src}')
        s = (f'  <section style="margin:24px 0 {bottom}px;padding:54px 16px;background:{FILL};border-radius:6px;'
             f'text-align:center;{MONO}font-size:12px;letter-spacing:1px;color:{GRAY};">图位 · {alt}</section>\n')
    if cap:
        s += f'  <p style="margin:0 0 24px;font-size:12px;line-height:1.6;color:{GRAY};text-align:center;">{inline(cap)}</p>\n'
    return s


def divider():
    return (f'  <section style="margin:34px 0;text-align:center;line-height:1;">'
            f'{circle(10, "empty", "#C9CCC6")}&nbsp;&nbsp;&nbsp;{circle(10, "half")}&nbsp;&nbsp;&nbsp;{circle(10, "full", GREEN)}</section>\n')


def white_box(rows_html):
    return f'  <section style="margin:0 0 24px;background:#FFFFFF;border-radius:6px;padding:6px 18px;">{rows_html}</section>\n'


def items_of(body):
    return [re.sub(r'^\s*(?:[-*]|\d+[.、])\s*', '', l) for l in body if l.strip()]


def c_list(arg, body):
    rows = items_of(body)
    out = []
    for i, r in enumerate(rows):
        a, c = split(r, 2)
        border = f'border-bottom:1px solid {RULE};' if i < len(rows) - 1 else ''
        out.append(f'<p style="margin:0;padding:10px 0;{border}"><span style="display:inline-block;width:34px;{MONO}font-size:12px;color:{GRAY};">{i + 1:02d}</span>'
                   f'<span style="font-weight:700;color:{INK};">{inline(a)}</span>'
                   + (f'<span style="float:right;font-size:13px;color:{DEEP};">{inline(c)}</span>' if c else '') + '</p>')
    if arg:  # 合计行
        a, c = split(arg, 2)
        out.append(f'<p style="margin:0;padding:10px 0 8px;border-top:2px solid {INK};"><span style="font-weight:900;color:{INK};">{inline(a)}</span>'
                   f'<span style="float:right;{MONO}font-size:13px;font-weight:700;color:{INK};">{inline(c)}</span></p>')
    return white_box(''.join(out))


def c_steps(arg, body):
    rows = items_of(body)
    cur = int(arg) if arg.strip().isdigit() else len(rows)  # 高亮第几步，默认最后一步
    out = []
    for i, r in enumerate(rows):
        t, d = split(r, 2)
        on = i + 1 == cur
        border = '' if i == len(rows) - 1 else f'border-bottom:1px solid {RULE};'
        num_color = f'{DEEP};font-weight:700' if on else GRAY
        line = (f'<p style="margin:0;padding:12px 0;{border}"><span style="display:inline-block;width:34px;{MONO}font-size:12px;color:{num_color};">{i + 1:02d}</span>'
                f'<span style="font-weight:700;color:{DEEP if on else INK};">{inline(t)}</span>')
        if d:
            line += f'<br><span style="display:inline-block;padding-left:34px;font-size:13px;line-height:1.7;color:{SUB};">{inline(d)}</span>'
        out.append(line + '</p>')
    return white_box(''.join(out))


def c_prompt(arg, body):
    text = inline(' '.join(l.strip() for l in body if l.strip()), dark=True)
    note = arg or '直接复制使用'
    return (f'  <section style="margin:20px 0 22px;padding:16px 18px 18px;background:{INK};border-radius:6px;">\n'
            f'    <p style="margin:0 0 10px;line-height:1.2;">{circle(12, "half", GREEN)}<span style="margin-left:7px;">{kicker("PROMPT", GREEN)}</span>'
            f'<span style="float:right;font-size:11px;color:{GRAY};">{inline(note)}</span></p>\n'
            f'    <p style="margin:0;font-size:14px;line-height:1.9;color:#C9CFCB;">{text}'
            f'<span style="display:inline-block;width:7px;height:15px;background:{GREEN};vertical-align:-2px;margin-left:2px;"></span></p>\n'
            f'  </section>\n')


def c_note(arg, body):
    text = '<br>'.join(inline(l.strip()) for l in body if l.strip())
    text = text.replace(f'color:{DEEP};font-weight:700', f'color:{INK};font-weight:700')
    return (f'  <section style="margin:22px 0;padding:18px;background:#FFFFFF;border-radius:6px;">\n'
            f'    <p style="margin:0 0 6px;line-height:1.4;"><span style="display:inline-block;width:24px;height:24px;line-height:24px;border-radius:50%;background:{INK};color:#FFFFFF;text-align:center;font-size:14px;font-weight:800;vertical-align:middle;">!</span>'
            f'<span style="margin-left:10px;font-size:17px;font-weight:900;color:{INK};vertical-align:middle;">{inline(arg or "注意")}</span></p>\n'
            f'    <p style="margin:0;font-size:14px;line-height:1.8;color:{SUB};">{text}</p>\n'
            f'  </section>\n')


def c_quote(arg, body):
    src, date = split(arg, 2)
    quote, take = [], ''
    for l in body:
        if re.match(r'^\s*(解读|HALFAI 解读)[:：]', l):
            take = re.split(r'[:：]', l, maxsplit=1)[1].strip()
        elif l.strip():
            quote.append(l.strip())
    s = (f'  <section style="margin:26px 0;">\n'
         f'    <p style="margin:0 0 10px;line-height:1.4;">{circle(12)}<span style="margin-left:7px;font-size:13px;font-weight:600;color:{INK};">{inline(src or "引用")}</span>'
         + (f'<span style="{MONO}font-size:11px;color:{GRAY};"> · {date}</span>' if date else '') + '</p>\n'
         f'    <section style="padding:2px 0 2px 16px;border-left:3px solid {RULE};">\n'
         f'      <p style="margin:0;font-size:16px;line-height:1.8;color:{SUB};">{inline(" ".join(quote))}</p>\n'
         f'    </section>\n')
    if take:
        s += f'    <p style="margin:12px 0 0;font-size:15px;font-weight:700;color:{INK};">{kicker("HALFAI 解读")}&nbsp;&nbsp;{inline(take)}</p>\n'
    return s + '  </section>\n'


def c_number(arg, body):
    lines = [l.strip() for l in body if l.strip()]
    num = lines[0] if lines else '0'
    num = re.sub(r'([×x%倍+])$', rf'<span style="color:{GREEN};">\1</span>', num)
    s = f'  <section style="margin:8px 0 26px;text-align:center;">\n'
    if arg:
        s += f'    <p style="margin:0;{MONO}font-size:11px;letter-spacing:1.5px;color:{DEEP};">—— {arg} ——</p>\n'
    s += f'    <p style="margin:0;font-size:64px;font-weight:800;line-height:1.15;letter-spacing:-3px;color:{INK};">{num}</p>\n'
    if len(lines) > 1:
        s += f'    <p style="margin:0;font-size:16px;font-weight:700;color:{INK};">{inline(lines[1])}</p>\n'
    if len(lines) > 2:
        s += f'    <p style="margin:6px 0 0;{MONO}font-size:10px;color:{GRAY};">{inline(lines[2])}</p>\n'
    return s + '  </section>\n'


def c_table(arg, body):
    rows = [l.strip().strip('|') for l in body if l.strip() and not re.match(r'^\s*\|?\s*:?-{2,}', l)]
    rows = [[c.strip() for c in r.split('|')] for r in rows]
    if not rows:
        return ''
    head = rows[0]
    pick = next((i for i, h in enumerate(head) if h.endswith('*')), -1)  # 表头带 * 的列是推荐列
    head = [h.rstrip('*').strip() for h in head]
    td = 'padding:10px 8px;'
    out = [f'  <section style="margin:0 0 26px;">\n    <table style="width:100%;border-collapse:collapse;font-size:13px;line-height:1.4;background:#FFFFFF;">\n']
    for ri, r in enumerate([head] + rows[1:]):
        last = ri == len(rows) - 1
        bb = '' if last else f'border-bottom:1px solid {RULE};'
        cells = []
        for ci, c in enumerate(r):
            if ri == 0:
                if ci == pick:
                    st = f'{td}{bb}border-top:3px solid {GREEN};background:#E4F2EA;color:{DEEP};font-weight:700;text-align:center;'
                else:
                    st = f'{td}{bb}color:{GRAY};text-align:center;' if ci else f'{td}{bb}'
            elif ci == 0:
                st = f'{td}{bb}color:{GRAY};'
            elif ci == pick:
                st = f'{td}{bb}background:#E4F2EA;text-align:center;font-weight:800;color:{INK};'
            else:
                st = f'{td}{bb}text-align:center;'
            cells.append(f'<td style="{st}">{inline(c)}</td>')
        out.append('      <tr>' + ''.join(cells) + '</tr>\n')
    out.append('    </table>\n')
    if arg:
        out.append(f'    <p style="margin:6px 0 0;{MONO}font-size:10px;color:{GRAY};text-align:right;">{arg}</p>\n')
    return ''.join(out) + '  </section>\n'


def dots(score):
    out = []
    for i in range(5):
        v = score - i
        kind = 'full' if v >= 1 else 'half' if v >= 0.5 else 'empty'
        out.append(circle(14, kind, DEEP if kind != 'empty' else '#C9CCC6'))
    return '&nbsp;'.join(out)


def c_score(arg, body):
    title, total = split(arg, 2)
    rows = items_of(body)
    vals = []
    lines = []
    for i, r in enumerate(rows):
        name, desc, sc = split(r, 3)
        v = float(sc or 0)
        vals.append(v)
        pad = '10px 0 0' if i == len(rows) - 1 else '10px 0'
        lines.append(f'    <p style="margin:0;padding:{pad};border-top:1px solid {RULE};"><span style="font-weight:600;color:{INK};">{inline(name)}</span>'
                     f'<span style="font-size:12px;color:{GRAY};">　{inline(desc)}</span><span style="float:right;">{dots(v)}</span></p>\n')
    total = total or (f'{sum(vals) / len(vals):.1f}' if vals else '')
    return (f'  <section style="margin:0 0 26px;padding:18px;background:#FFFFFF;border-radius:6px;">\n'
            f'    <p style="margin:0 0 4px;font-size:18px;font-weight:900;color:{INK};">{inline(title or "值不值得用？")}</p>\n'
            f'    <p style="margin:0 0 10px;"><span style="font-size:34px;font-weight:800;letter-spacing:-1px;color:{DEEP};">{total}</span>'
            f'<span style="margin-left:6px;font-size:12px;color:{GRAY};">/ 5 推荐指数</span></p>\n' + ''.join(lines) + '  </section>\n')


def c_summary(arg, body):
    lines = [l.strip() for l in body if l.strip()]
    s = (f'  <section style="margin:0 0 26px;padding:22px 20px;background:{INK};border-radius:6px;">\n'
         f'    <p style="margin:0 0 10px;">{kicker(arg or "一句话总结", GREEN)}</p>\n')
    for i, l in enumerate(lines[:2]):
        s += f'    <p style="margin:0;font-size:21px;font-weight:900;line-height:1.4;letter-spacing:-0.5px;color:{WHITE if i == 0 else GRAY};">{inline(l, dark=True)}</p>\n'
    return s + '  </section>\n'


def c_card(arg, body):
    text = '<br>'.join(inline(l.strip(), dark=True) for l in body if l.strip())
    return (f'  <section style="margin:0 0 22px;padding:16px 18px;background:{INK};border-radius:6px;">\n'
            f'    <p style="margin:0 0 8px;line-height:1.2;">{ha(13, -2)}<span style="margin-left:7px;">{kicker(arg or "HALFAI", GREEN)}</span></p>\n'
            f'    <p style="margin:0;{MONO}font-size:14px;line-height:1.6;color:{WHITE};word-break:break-all;">{text}</p>\n'
            f'  </section>\n')


def c_html(arg, body):
    return ''.join(l if l.endswith('\n') else l + '\n' for l in body)


BLOCKS = {'list': c_list, 'steps': c_steps, 'prompt': c_prompt, 'note': c_note, 'quote': c_quote,
          'number': c_number, 'table': c_table, 'score': c_score, 'summary': c_summary,
          'card': c_card, 'html': c_html}


# ---------------------------------------------------------------- 解析
def parse_meta(lines):
    meta = {}
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                for l in lines[1:i]:
                    if ':' in l:
                        k, v = l.split(':', 1)
                        meta[k.strip()] = v.strip().strip('"\'')
                return meta, lines[i + 1:]
    return meta, lines


def render(md_path):
    base = os.path.dirname(os.path.abspath(md_path))
    lines = open(md_path, encoding='utf-8').read().splitlines()
    meta, lines = parse_meta(lines)
    item_label = meta.get('item_label', 'NO.')
    sub_label = meta.get('sub_label', 'TYPE')
    total_items = sum(1 for l in lines if l.startswith('## '))
    out = [f'<!-- HalfAI · {meta.get("title", "")}{meta.get("title2", "")} · 公众号排版 -->\n',
           f'<section style="margin:0;padding:24px 16px 28px;background:{PAPER};{SANS}font-size:15px;line-height:1.85;letter-spacing:0.4px;color:{BODY};text-align:left;">\n\n']
    if meta.get('header', 'yes') != 'no':
        out.append(header(meta))
    n_ch = n_item = n_sub = 0
    first_para = True
    buf = []

    def flush():
        nonlocal first_para
        if buf:
            out.append(para(''.join(buf), lead=first_para))
            first_para = False
            buf.clear()

    i = 0
    while i < len(lines):
        l = lines[i]
        s = l.strip()
        m_img = re.match(r'^!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"([^"]*)")?\s*\)$', s)
        if not s:
            flush()
        elif s.startswith(':::'):
            flush()
            name, _, arg = s[3:].strip().partition(' ')
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != ':::':
                body.append(lines[i])
                i += 1
            if name not in BLOCKS:
                WARN.append(f'未知组件 :::{name}，已跳过')
            else:
                out.append(BLOCKS[name](arg.strip(), body))
        elif s.startswith('### '):
            flush()
            n_sub += 1
            a, b = split(s[4:], 2)
            out.append(subhead(sub_label, n_sub, a, b))
        elif s.startswith('## '):
            flush()
            n_item += 1
            a, b, c = split(s[3:], 3)
            out.append(item(item_label, n_item, total_items, a, b, c))
        elif s.startswith('# '):
            flush()
            n_ch += 1
            a, b = split(s[2:], 2)
            out.append(chapter(n_ch, a, b))
        elif re.fullmatch(r'-{3,}|\*{3,}', s):
            flush()
            out.append(divider())
        elif m_img:
            flush()
            out.append(image(base, m_img.group(1), m_img.group(2), m_img.group(3) or ''))
        elif s.startswith('<'):
            flush()
            out.append('  ' + s + '\n')
        else:
            buf.append(s)
        i += 1
    flush()
    if meta.get('footer', 'yes') != 'no':
        out.append(footer(meta))
    out.append('\n</section>\n')
    return meta, ''.join(out)


def main():
    ap = argparse.ArgumentParser(description='HalfAI 公众号排版')
    ap.add_argument('md', help='稿件 Markdown 路径')
    ap.add_argument('-o', '--out', help='输出目录，默认与稿件同目录')
    ap.add_argument('--name', help='输出文件名前缀，默认取稿件文件名')
    a = ap.parse_args()
    meta, article = render(a.md)
    out = a.out or os.path.dirname(os.path.abspath(a.md))
    os.makedirs(out, exist_ok=True)
    slug = a.name or meta.get('slug') or os.path.splitext(os.path.basename(a.md))[0]
    art_path = os.path.join(out, f'{slug}-article.html')
    open(art_path, 'w', encoding='utf-8').write(article)

    title = meta.get('wechat_title') or (meta.get('title', '') + meta.get('title2', ''))
    shell = open(os.path.join(ASSETS, 'preview_shell.html'), encoding='utf-8').read()
    n_img = article.count('<img ')
    rep = {
        '{{PAGE_TITLE}}': html.escape(title),
        '{{EYEBROW}}': meta.get('eyebrow', '公众号图文'),
        '{{H1}}': f'{meta.get("title", "")}<br><span>{meta.get("title2", "")}</span>',
        '{{LEAD}}': meta.get('preview_note', f'按 HalfAI 公众号模板排好，{n_img} 张图已经嵌在正文里，复制后一起带走。'),
        '{{TITLE}}': title,
        '{{DIGEST}}': meta.get('digest', '（在稿件 front matter 里填 digest）'),
        '{{ARTICLE}}': article,
    }
    for k, v in rep.items():
        shell = shell.replace(k, v)
    prev_path = os.path.join(out, f'{slug}-preview.html')
    open(prev_path, 'w', encoding='utf-8').write(shell)

    mb = len(shell.encode()) / 1024 / 1024
    if mb > 15:
        WARN.append(f'预览页 {mb:.1f}MB，超过 15MB：压一压 GIF（scripts/make_gif.sh），否则发不成 Artifact、粘贴也会慢')
    elif mb > 10:
        WARN.append(f'预览页 {mb:.1f}MB，接近上限，图片总量建议控制在 10MB 内')
    print(f'article  {art_path}  ({len(article.encode()) / 1024:.0f} KB)')
    print(f'preview  {prev_path}  ({mb:.2f} MB, {n_img} images)')
    for w in WARN:
        print('WARN', w, file=sys.stderr)


if __name__ == '__main__':
    main()
