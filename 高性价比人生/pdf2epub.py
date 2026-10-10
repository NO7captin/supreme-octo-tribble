# -*- coding: utf-8 -*-
import re
import pymupdf
from ebooklib import epub

SRC = "齐民要术.pdf"
OUT = "高性价比人生指南.epub"

CHAPTER_TITLES = {
    1: "不要早死", 2: "不要慢慢死", 3: "不要浪费精力", 4: "不要浪费时间",
    5: "不要浪费钱", 6: "反面清单", 7: "没钱的时候怎么活",
    8: "别把自己搭进去：法律与财产安全", 9: "普通人容易踩的法律红线",
    10: "恋爱和结婚划不划算", 11: "程序员和技术人容易踩的红线",
    12: "创业与做生意：别把家底赔进去", 13: "紧急情况：先做什么",
    14: "账号与信息安全", 15: "租房与买房", 16: "得了慢性病之后怎么活",
    17: "家里有老人", 18: "养孩子划不划算", 19: "在职、离职和工伤",
    20: "刚出生的孩子怎么带", 21: "出国、旅行与境外安全",
    22: "怎么放松：娱乐场所和减压", 23: "学什么技能划算",
    24: "看病：怎么少花钱少走弯路", 25: "人走了以后要办什么",
    26: "做一个网站或平台：资质、备案和服务器", 27: "怀孕和生产：从发现怀孕到出院办证",
    28: "别为了外形把身体搞坏", 29: "遭遇重大打击之后", 30: "上学以后的孩子",
    31: "十八岁之后有哪几条路", 32: "出国留学：身份、打工、保险和回国认证",
    33: "残疾之后怎么活", 34: "家里的常备药别吃出事",
}

doc = pymupdf.open(SRC)

def is_toc_page(t):
    return len(re.findall(r"\.{5,}|…{3,}", t)) >= 5

# 收集每一章的文本
chapters = {k: [] for k in CHAPTER_TITLES}
front = []   # 前言 / 各节简介等无章节号内容
appendix = []  # 34章之后的附录

hdr_re = re.compile(r"^(\d{1,2})\.\s+.{1,30}$")

for pno, page in enumerate(doc):
    lines = page.get_text().split("\n")
    lines = [ln.rstrip() for ln in lines]
    # 去页眉第一行
    while lines and lines[0].strip() == "":
        lines.pop(0)
    if lines and lines[0].strip() == "高性价比人生指南":
        lines.pop(0)
    while lines and lines[0].strip() == "":
        lines.pop(0)

    # 判断本页章节归属：第二行可能是 "N. 标题" 页眉
    chap_no = None
    if lines and hdr_re.match(lines[0].strip()):
        m = hdr_re.match(lines[0].strip())
        chap_no = int(m.group(1))
        if chap_no in CHAPTER_TITLES:
            lines.pop(0)  # 删掉页眉章节名
        else:
            chap_no = None
    elif lines and lines[0].strip() in ("前言", "各节简介"):
        chap_no = 0  # 前言区

    body = "\n".join(lines).strip()
    if not body:
        continue
    if is_toc_page(body):
        continue

    if chap_no == 0:
        front.append(body)
    elif chap_no is not None:
        chapters[chap_no].append(body)
    else:
        # 无页眉章节号：若已有章节内容则归到最后一章，否则算 front
        if any(chapters[c] for c in chapters):
            # 归到最近一章（简单处理：appendix）
            appendix.append(body)
        else:
            front.append(body)

# 段落重组：合并普通行，保留 • 条目
def reflow(text):
    paras = []
    buf = ""
    for raw in text.split("\n"):
        ln = raw.strip()
        if not ln:
            if buf:
                paras.append(buf); buf = ""
            continue
        if ln.startswith("•"):
            if buf:
                paras.append(buf); buf = ""
            paras.append(ln)
        else:
            # 去掉 PDF 行尾断字/连字符，中文直接拼接
            if buf and not re.search(r"[。！？：；，、」）]$", buf):
                buf += ln
            elif buf:
                buf += ln
            else:
                buf = ln
    if buf:
        paras.append(buf)
    return paras

# 构建 EPUB
book = epub.EpubBook()
book.set_identifier("how-to-live-better-2026")
book.set_title("高性价比人生指南")
book.set_language("zh-CN")
book.add_author("NO7队长整理")

style = "body{font-family:sans-serif;line-height:1.8;} h1{font-size:1.4em;} .item{margin:0.6em 0;}"
nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style.encode("utf-8"))
book.add_item(nav_css)

def paras_to_html(paras):
    out = []
    for p in paras:
        p = p.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if p.startswith("•"):
            out.append(f'<p class="item">• {p[1:].strip()}</p>')
        else:
            out.append(f"<p>{p}</p>")
    return "\n".join(out)

epub_chaps = []

# 前言
front_text = "\n".join(front)
c0 = epub.EpubHtml(title="前言与各节简介", file_name="front.xhtml", lang="zh-CN")
c0.content = f"<h1>前言与各节简介</h1>\n{paras_to_html(reflow(front_text))}"
c0.add_item(nav_css)
book.add_item(c0)
epub_chaps.append(c0)

# 各章
for num in sorted(chapters):
    title = CHAPTER_TITLES[num]
    text = "\n".join(chapters[num])
    paras = reflow(text)
    c = epub.EpubHtml(title=f"{num}. {title}", file_name=f"ch{num:02d}.xhtml", lang="zh-CN")
    c.content = f"<h1>{num}. {title}</h1>\n{paras_to_html(paras)}"
    c.add_item(nav_css)
    book.add_item(c)
    epub_chaps.append(c)
    print(f"第{num:2d}章 {title}: {len(paras)} 段")

# 附录
if appendix:
    cA = epub.EpubHtml(title="附录", file_name="appendix.xhtml", lang="zh-CN")
    cA.content = f"<h1>附录</h1>\n{paras_to_html(reflow(chr(10).join(appendix)))}"
    cA.add_item(nav_css)
    book.add_item(cA)
    epub_chaps.append(cA)

book.toc = tuple(epub_chaps)
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())
book.spine = ["nav"] + epub_chaps

epub.write_epub(OUT, book, {})
print("已生成:", OUT)
