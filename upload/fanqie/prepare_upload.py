#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把九部小说导出为番茄作家网可直接导入的 TXT 章节（去掉 Markdown 标记）。"""

import os
import re

NOVELS = [
    ("task-01-wanjie-changsheng-tu", "万界长生图"),
    ("task-02-tangshuipu", "巷口的糖水铺"),
    ("task-03-xinghai-shihuangzhe", "星海拾荒者"),
    ("task-04-diqige-zhengwu", "第七个证物"),
    ("task-21-xianzupu", "仙族谱"),
    ("task-22-shenye-danganguan", "深夜档案馆"),
    ("task-23-xiaofanguan-1988", "1988小饭馆"),
    ("task-41-chunri-chichi", "春日迟迟"),
    ("task-42-moyu-system", "摸鱼系统"),
]

OUT_ROOT = os.path.join("upload", "fanqie")


def clean_md(text):
    """去掉 Markdown 标题/强调标记，保留正文段落。"""
    lines = text.splitlines()
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            out.append("")
            continue
        if re.match(r"^#{1,3}\s+", s):  # 章节标题（保留为标题行）
            s = re.sub(r"^#{1,3}\s+", "", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"\*(.+?)\*", r"\1", s)
        s = re.sub(r"`(.+?)`", r"\1", s)
        out.append(s)
    return "\n".join(out).strip()


def chapters(d):
    path = os.path.join(d, "chapters")
    if not os.path.isdir(path):
        return []
    files = []
    for f in os.listdir(path):
        m = re.search(r"(\d+)", f)
        if m and f.endswith(".md"):
            files.append((int(m.group(1)), f))
    files.sort()
    return files


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    for d, title in NOVELS:
        chs = chapters(d)
        out_dir = os.path.join(OUT_ROOT, d)
        os.makedirs(out_dir, exist_ok=True)
        combined = []
        n = 0
        for num, f in chs[:30]:
            with open(os.path.join(d, "chapters", f), encoding="utf-8") as fh:
                text = clean_md(fh.read())
            dst = os.path.join(out_dir, "ch%03d.txt" % num)
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
            combined.append(text)
            n += 1
        with open(os.path.join(OUT_ROOT, "%s_part1.txt" % title), "w", encoding="utf-8") as fh:
            fh.write("\n\n\n".join(combined))
        print("%s：导出 %d 章（前 30 章）" % (title, n))


if __name__ == "__main__":
    main()
