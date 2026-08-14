#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小说分卷排版/质检 CLI（纯标准库）。"""

import argparse
import os
import re
import sys


def load_chapters(dirpath):
    files = [f for f in os.listdir(dirpath) if f.endswith(".md")]
    chs = []
    for f in sorted(files):
        m = re.search(r"(\d+)", f)
        if not m:
            continue
        n = int(m.group(1))
        with open(os.path.join(dirpath, f), "r", encoding="utf-8") as fh:
            text = fh.read()
        title = ""
        for line in text.splitlines()[:5]:
            t = re.match(r"^#\s+(.+)$", line.strip())
            if t:
                title = t.group(1).strip()
                break
        chs.append({"n": n, "file": f, "title": title, "text": text})
    chs.sort(key=lambda x: x["n"])
    return chs


def cmd_stats(args):
    chs = load_chapters(args.dir)
    if not chs:
        print("没有找到章节文件")
        return 1
    total = sum(len(c["text"]) for c in chs)
    avg = total // len(chs)
    print("章节数：%d" % len(chs))
    print("总字数：%d" % total)
    print("平均每章：%d 字" % avg)
    print("最短章：%d 字（第%d章 %s）" % (min(len(c["text"]) for c in chs), min(chs, key=lambda c: len(c["text"]))["n"], min(chs, key=lambda c: len(c["text"]))["title"]))
    print("最长章：%d 字（第%d章 %s）" % (max(len(c["text"]) for c in chs), max(chs, key=lambda c: len(c["text"]))["n"], max(chs, key=lambda c: len(c["text"]))["title"]))
    if args.goal:
        parts = args.goal.split(":")
        goal_n, goal_chars = int(parts[0]), int(parts[1])
        print("目标：%d 章 / %d 字" % (goal_n, goal_chars))
        print("达成：%.1f%% / %.1f%%" % (len(chs) / goal_n * 100, total / goal_chars * 100))
        missing = [i for i in range(1, chs[-1]["n"] + 1) if i not in {c["n"] for c in chs}]
        if missing:
            print("缺章：%s" % ", ".join(str(i) for i in missing))
    return 0


def cmd_check(args):
    chs = load_chapters(args.dir)
    problems = []
    nums = [c["n"] for c in chs]
    for i in range(1, max(nums) + 1):
        if i not in nums:
            problems.append("缺章：第 %d 章" % i)
    seen = set()
    for c in chs:
        if c["n"] in seen:
            problems.append("重号：第 %d 章（%s）" % (c["n"], c["file"]))
        seen.add(c["n"])
        if not c["title"]:
            problems.append("缺少标题：%s" % c["file"])
        body = re.sub(r"^#.*$", "", c["text"], flags=re.M)
        body = re.sub(r"\s", "", body)
        if len(body) < 800:
            problems.append("篇幅过短（<%d字）：第%d章 %s（%d字）" % (800, c["n"], c["title"], len(body)))
        if len(body) > 3000:
            problems.append("篇幅过长（>3000字）：第%d章 %s（%d字）" % (c["n"], c["title"], len(body)))
        # 结尾钩子检测：最后一句以对话/问句/省略号/悬念词结尾
        tail = body[-60:]
        if not re.search(r"[？?!！…]|说[道]|忽然|竟然|没想到|怎么回事|到底|是谁|什么$", tail):
            problems.append("疑似缺钩子：第%d章 %s 结尾：…%s" % (c["n"], c["title"], tail[-20:]))
        # 重复段落检测
        paras = [re.sub(r"\s", "", p) for p in re.split(r"\n\s*\n", body) if len(re.sub(r"\s", "", p)) > 40]
        dup = {p for p in paras if paras.count(p) > 1}
        if dup:
            problems.append("疑似重复段落：第%d章 %s（%d 段）" % (c["n"], c["title"], len(dup)))
    if problems:
        print("发现问题 %d 条：" % len(problems))
        for p in problems:
            print(" - " + p)
    else:
        print("检查通过：无缺章、无重号、篇幅与钩子正常。")
    return 0


def cmd_toc(args):
    chs = load_chapters(args.dir)
    lines = ["| 章号 | 标题 | 字数 |", "|---|---|---|"]
    for c in chs:
        lines.append("| %d | %s | %d |" % (c["n"], c["title"] or c["file"], len(c["text"])))
    out = "\n".join(lines)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out + "\n")
        print("已写入 " + args.out)
    else:
        print(out)
    return 0


def main():
    ap = argparse.ArgumentParser(description="小说分卷排版/质检工具")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("stats")
    p1.add_argument("--dir", required=True)
    p1.add_argument("--goal", default="", help="目标格式：章数:字数，如 500:500000")
    p1.set_defaults(fn=cmd_stats)
    p2 = sub.add_parser("check")
    p2.add_argument("--dir", required=True)
    p2.set_defaults(fn=cmd_check)
    p3 = sub.add_parser("toc")
    p3.add_argument("--dir", required=True)
    p3.add_argument("--out", default="")
    p3.set_defaults(fn=cmd_toc)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
