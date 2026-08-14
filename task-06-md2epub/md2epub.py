#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown -> EPUB 打包工具（纯标准库，零依赖）。"""

import argparse
import glob
import os
import re
import sys
import zipfile
import html
from datetime import datetime


def natural_key(name):
    """把 ch10.md 排到 ch2.md 后面的自然排序 key。"""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def read_markdown_files(paths, sort_mode):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files.extend(glob.glob(os.path.join(p, "*.md")))
        else:
            files.append(p)
    files = [f for f in files if os.path.isfile(f)]
    if sort_mode == "natural":
        files.sort(key=lambda f: natural_key(os.path.basename(f)))
    else:
        files.sort()
    return files


def parse_markdown(text):
    """极简 markdown 转 xhtml 段落。支持 # 标题、普通段落、引用、分隔线。"""
    lines = text.splitlines()
    title = None
    body_parts = []
    buf = []

    def flush():
        if buf:
            para = " ".join(x.strip() for x in buf if x.strip())
            if para:
                body_parts.append("<p>" + inline(para) + "</p>")
            buf.clear()

    for line in lines:
        s = line.strip()
        if not s:
            flush()
            continue
        m = re.match(r"^#\s+(.+)$", s)
        if m:
            flush()
            if title is None:
                title = m.group(1)
            else:
                body_parts.append('<h2 class="chapter-title">' + inline(m.group(1)) + "</h2>")
            continue
        if s == "---" or s == "***":
            flush()
            body_parts.append('<hr/>')
            continue
        if s.startswith(">"):
            flush()
            body_parts.append('<blockquote>' + inline(s.lstrip(">").strip()) + "</blockquote>")
            continue
        buf.append(s)
    flush()
    return title, "".join(body_parts)


def inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return s


def make_epub(chapters, meta, out_path, custom_css=None):
    """chapters: [(title, html_body), ...]"""
    uid = "urn:uuid:" + re.sub(r"[^0-9a-fA-F]", "", os.urandom(16).hex())
    date = datetime.now().strftime("%Y-%m-%d")
    title = meta["title"]
    author = meta["author"]
    lang = meta.get("lang", "zh-CN")

    default_css = (
        "body{font-family:serif;line-height:1.8;margin:5% 6%}"
        "h1{text-align:center;font-size:1.6em;margin:2em 0}"
        "h2.chapter-title{text-align:center;margin:2em 0 1em}"
        "p{text-indent:2em;margin:0.6em 0}"
        "blockquote{color:#555;border-left:3px solid #ccc;padding-left:1em;margin:1em 0}"
        "hr{margin:2em auto;width:40%}"
    )
    css = custom_css if custom_css else default_css

    chapter_files = []
    for i, (ctitle, body) in enumerate(chapters, 1):
        name = "ch%04d.xhtml" % i
        content = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="%s">\n<head>\n'
            '<meta charset="utf-8"/>\n'
            '<link rel="stylesheet" type="text/css" href="style.css"/>\n'
            '<title>%s</title>\n</head>\n<body>\n'
            "<h1>%s</h1>\n%s\n</body>\n</html>"
            % (lang, html.escape(ctitle), html.escape(ctitle), body)
        )
        chapter_files.append((name, ctitle, content.encode("utf-8")))

    manifest_items = [
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="css" href="style.css" media-type="text/css"/>',
    ]
    spine_items = ['<itemref idref="nav"/>']
    for name, ctitle, _ in chapter_files:
        fid = "ch" + name[2:6]
        manifest_items.append(
            '<item id="%s" href="%s" media-type="application/xhtml+xml"/>' % (fid, name)
        )
        spine_items.append('<itemref idref="%s"/>' % fid)

    opf = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="BookId">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">\n'
        '<dc:title>%s</dc:title>\n'
        '<dc:creator opf:role="aut">%s</dc:creator>\n'
        '<dc:language>%s</dc:language>\n'
        '<dc:identifier id="BookId">%s</dc:identifier>\n'
        '<dc:date>%s</dc:date>\n'
        "</metadata>\n"
        '<manifest>\n%s\n</manifest>\n'
        '<spine toc="ncx">\n%s\n</spine>\n'
        '<guide><reference type="toc" title="目录" href="nav.xhtml"/></guide>\n'
        "</package>"
        % (html.escape(title), html.escape(author), lang, uid, date, "\n".join(manifest_items), "\n".join(spine_items))
    ).encode("utf-8")

    nav_li = "".join(
        '<li><a href="%s">%s</a></li>' % (name, html.escape(ctitle)) for name, ctitle, _ in chapter_files
    )
    nav = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="%s">\n<head>\n'
        '<meta charset="utf-8"/>\n<title>目录</title>\n</head>\n<body>\n'
        "<h1>目录</h1>\n<nav epub:type=\"toc\" xmlns:epub=\"http://www.idpf.org/2007/ops\">\n"
        "<ol>%s</ol>\n</nav>\n</body>\n</html>" % (lang, nav_li)
    ).encode("utf-8")

    ncx_li = "".join(
        '<navPoint id="nav%d" playOrder="%d"><navLabel><text>%s</text></navLabel>'
        '<content src="%s"/></navPoint>'
        % (i, i, html.escape(ctitle), name)
        for i, (name, ctitle, _) in enumerate(chapter_files, 1)
    )
    ncx = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
        "<head><meta name=\"dtb:uid\" content=\"%s\"/></head>\n"
        "<docTitle><text>%s</text></docTitle>\n"
        "<navMap>%s</navMap>\n</ncx>" % (uid, html.escape(title), ncx_li)
    ).encode("utf-8")

    container = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>\n'
        "</container>"
    ).encode("utf-8")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container)
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/nav.xhtml", nav)
        z.writestr("OEBPS/toc.ncx", ncx)
        z.writestr("OEBPS/style.css", css.encode("utf-8"))
        for name, _, content in chapter_files:
            z.writestr("OEBPS/" + name, content)
    return len(chapter_files)


def main():
    ap = argparse.ArgumentParser(description="Markdown 章节打包为 EPUB")
    ap.add_argument("paths", nargs="+", help="章节 .md 文件或目录")
    ap.add_argument("--title", required=True, help="书名")
    ap.add_argument("--author", default="佚名", help="作者")
    ap.add_argument("--out", required=True, help="输出 .epub 路径")
    ap.add_argument("--lang", default="zh-CN")
    ap.add_argument("--sort", choices=["natural", "lexical"], default="natural")
    ap.add_argument("--css", default=None, help="自定义 CSS 文件")
    args = ap.parse_args()

    files = read_markdown_files(args.paths, args.sort)
    if not files:
        print("错误：没有找到任何 .md 文件", file=sys.stderr)
        return 1

    custom_css = None
    if args.css:
        with open(args.css, "r", encoding="utf-8") as f:
            custom_css = f.read()

    chapters = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            title, body = parse_markdown(fh.read())
        if not body and not title:
            continue
        chapters.append((title or os.path.splitext(os.path.basename(f))[0], body))

    n = make_epub(chapters, {"title": args.title, "author": args.author, "lang": args.lang}, args.out, custom_css)
    print("完成：%s（%d 章）→ %s" % (args.title, n, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
