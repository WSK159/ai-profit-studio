#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小说连载引擎：调用 DeepSeek 按大纲逐章续写并维护上下文。"""

import argparse
import json
import os
import re
import sys
import urllib.request

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
PER_CALL = 2


def call_deepseek(system, user, max_tokens=8000, temperature=1.0):
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        raise SystemExit("缺少环境变量 DEEPSEEK_API_KEY")
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def load_state(novel_dir):
    path = os.path.join(novel_dir, "state.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"next": 1, "summary": "", "last_titles": []}


def save_state(novel_dir, state):
    with open(os.path.join(novel_dir, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def read_md(novel_dir, name):
    path = os.path.join(novel_dir, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def briefs_from_outline(outline):
    """从 outline.md 的"前 N 章细纲"里提取 {章号: 简述}。"""
    briefs = {}
    section = False
    for line in outline.splitlines():
        if "细纲" in line and ("章" in line or "前" in line):
            section = True
            continue
        if section and line.strip().startswith("##"):
            break
        if section:
            m = re.match(r"^(\d+)\.\s*(.*)$", line.strip())
            if m:
                briefs[int(m.group(1))] = m.group(2).strip()
    return briefs


def build_prompts(novel_dir, start, count, state):
    outline = read_md(novel_dir, "outline.md")
    bible = read_md(novel_dir, "world-bible.md")
    readme = read_md(novel_dir, "README.md")

    title = "未知作品"
    for line in readme.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    briefs = briefs_from_outline(outline)
    brief_lines = []
    for n in range(start, start + count):
        if n in briefs:
            brief_lines.append("第%d章：%s" % (n, briefs[n]))
        else:
            brief_lines.append("第%d章：根据卷纲与上下文自然推进，章末留钩子" % n)
    brief_text = "\n".join(brief_lines)

    system = (
        "你是一位拥有二十年经验的华语网文金牌作者，尤其擅长长篇连载。"
        "你的任务是把给定章节写成高质量的正文，而不是提纲。"
        "硬性要求：\n"
        "1. 每一章 1100-1400 个汉字，必须是完整的叙事章节；\n"
        "2. 章节第一行是标题，格式：`# 第N章 标题`；\n"
        "3. 正文用 Markdown 段落书写，禁止输出任何解说、前言、后记或提纲；\n"
        "4. 每章必须推进剧情：开头三行内进入场景/冲突，中段至少一次小高潮或转折，结尾留钩子；\n"
        "5. 保持人物性格、称呼、世界观设定前后一致，不得随意改名改设定；\n"
        "6. 语言流畅、画面感强、对话自然，避免重复用词和注水；\n"
        "7. 章节之间用单独一行 `=====` 分隔；\n"
        "8. 全部章节写完后，另起一行输出 `[STATE]` 开头的一句话章节摘要（200-260字），"
        "概括这几章发生的重大事件、人物关系变化、当前地点、所有未回收的伏笔与悬念，供下一批续写使用。"
    )

    user = (
        "作品：《%s》\n\n"
        "【全书大纲】\n%s\n\n"
        "【世界设定】\n%s\n\n"
        "【已写章节摘要】\n%s\n\n"
        "【本批要写的章节】\n%s\n\n"
        "请按上述要求写出第 %d 至第 %d 章。"
        % (title, outline, bible, state["summary"] or "（刚开始，尚未有前文）", brief_text, start, start + count - 1)
    )
    return system, user


CN_NUM = "[一二三四五六七八九十百千]+"
HEAD_RE = re.compile(r"^#?\s*第\s*(\d+|%s)\s*章[：:\.\s]*(.*)$" % CN_NUM)


def cn2int(s):
    if s.isdigit():
        return int(s)
    table = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
             "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
             "百": 100, "千": 1000}
    total, cur = 0, 0
    for ch in s:
        if ch in ("十", "百", "千"):
            cur = cur or 1
            total += cur * table[ch]
            cur = 0
        else:
            cur = table.get(ch, 0)
    return total + cur


def parse_batch(text):
    """把模型返回拆成 (title, body) 列表，并提取 [STATE] 摘要。兼容中文数字与代码围栏。"""
    state_text = ""
    m = re.search(r"\[STATE\]\s*(.+)", text, re.S)
    if m:
        state_text = m.group(1).strip()
        text = text[: m.start()].rstrip()

    text = re.sub(r"^```(?:markdown|md|text)?\s*$", "", text, flags=re.M)
    text = re.sub(r"^```\s*$", "", text, flags=re.M)
    text = re.sub(r"^[=—-]{3,}\s*$", "", text, flags=re.M)

    parts = re.split(r"(?=^#?\s*第\s*(?:\d+|%s)\s*章)" % CN_NUM, text, flags=re.M)
    chapters = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        lines = p.splitlines()
        tm = HEAD_RE.match(lines[0].strip())
        if not tm:
            continue
        n = cn2int(tm.group(1))
        title = "第%d章 %s" % (n, tm.group(2).strip())
        body = "\n".join(lines[1:]).strip()
        if body:
            chapters.append((n, title, body))
    return chapters, state_text


def chapter_path(novel_dir, n):
    return os.path.join(novel_dir, "chapters", "ch%03d.md" % n)


def main():
    ap = argparse.ArgumentParser(description="小说连载引擎")
    ap.add_argument("--novel", required=True, help="小说目录，如 task-01-wanjie-changsheng-tu")
    ap.add_argument("--chapters", type=int, default=6, help="本批要生成的章节数")
    ap.add_argument("--start", type=int, default=0, help="从第几章开始（0 表示接续 state.json）")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的章节文件")
    args = ap.parse_args()

    novel_dir = args.novel
    if not os.path.isdir(novel_dir):
        raise SystemExit("找不到小说目录：" + novel_dir)
    state = load_state(novel_dir)
    chapters_dir = os.path.join(novel_dir, "chapters")
    if not state.get("next") and os.path.isdir(chapters_dir):
        existing = []
        for f in os.listdir(chapters_dir):
            m = re.search(r"(\d+)", f)
            if m and f.endswith(".md"):
                existing.append(int(m.group(1)))
        if existing:
            state["next"] = max(existing) + 1
    start = args.start if args.start else state.get("next", 1)
    written = 0

    for batch_start in range(start, start + args.chapters, PER_CALL):
        batch_count = min(PER_CALL, start + args.chapters - batch_start)
        system, user = build_prompts(novel_dir, batch_start, batch_count, state)
        print("生成中：第 %d-%d 章…" % (batch_start, batch_start + batch_count - 1), flush=True)
        text = call_deepseek(system, user)
        chapters, state_text = parse_batch(text)
        if not chapters:
            dbg = os.path.join(novel_dir, "_raw_debug.txt")
            with open(dbg, "w", encoding="utf-8") as f:
                f.write(text)
            print("警告：本批没有解析到有效章节，原始内容已存 %s" % dbg, flush=True)
            continue
        chapters.sort(key=lambda x: x[0])
        for n, title, body in chapters:
            if n < batch_start or n >= batch_start + batch_count:
                continue
            path = chapter_path(novel_dir, n)
            if os.path.exists(path) and not args.force:
                print("  跳过已存在：%s" % os.path.relpath(path), flush=True)
                continue
            with open(path, "w", encoding="utf-8") as f:
                f.write("# %s\n\n%s\n" % (title, body))
            written += 1
            print("  已写入 %s" % os.path.relpath(path), flush=True)
        last = max(n for n, _, _ in chapters)
        state["next"] = last + 1
        state["last_titles"] = [t for _, t, _ in chapters]
        if state_text:
            state["summary"] = state_text
        save_state(novel_dir, state)

    print("完成：共写入 %d 章。当前进度：已写到第 %d 章。" % (written, state["next"] - 1), flush=True)


if __name__ == "__main__":
    sys.exit(main())
