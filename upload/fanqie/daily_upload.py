#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日上传辅助：每天把每部小说未上传的 5-10 章导出到 daily 目录，并打开番茄作家网供导入。

说明：番茄作家网登录/上传需要浏览器会话（密码登录还可能要求短信/滑块验证），
本脚本负责每日自动准备好下一批章节；用户在已登录的浏览器中把 daily 目录的 TXT 导入即可。
"""

import datetime
import json
import os
import re
import sys
import webbrowser

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

ROOT = os.path.join("upload", "fanqie")
STATE = os.path.join(ROOT, "progress.json")
DAILY = 5


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(st):
    os.makedirs(ROOT, exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


def chapter_files(d):
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


def clean_md(text):
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^#{1,3}\s+", s):
            s = re.sub(r"^#{1,3}\s+", "", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"\*(.+?)\*", r"\1", s)
        s = re.sub(r"`(.+?)`", r"\1", s)
        lines.append(s)
    return "\n".join(lines).strip()


def main():
    st = load_state()
    date = datetime.date.today().isoformat()
    out_day = os.path.join(ROOT, "daily", date)
    os.makedirs(out_day, exist_ok=True)
    total = 0
    for d, title in NOVELS:
        chs = chapter_files(d)
        if not chs:
            continue
        done = st.get(d, 0)
        batch = [c for c in chs if c[0] > done][:DAILY]
        if not batch:
            print("%s：已全部导出" % title)
            continue
        sub = os.path.join(out_day, d)
        os.makedirs(sub, exist_ok=True)
        for num, f in batch:
            with open(os.path.join(d, "chapters", f), encoding="utf-8") as fh:
                text = clean_md(fh.read())
            with open(os.path.join(sub, "ch%03d.txt" % num), "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
            st[d] = num
            total += 1
        print("%s：本日导出 %d 章（第 %d-%d 章）" % (title, len(batch), batch[0][0], batch[-1][0]))
    save_state(st)
    print("本日共导出 %d 章 → %s" % (total, out_day))
    if "--open" in sys.argv:
        webbrowser.open("https://fanqienovel.com/")


if __name__ == "__main__":
    main()
