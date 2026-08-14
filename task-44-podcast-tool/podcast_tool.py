#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""播客转写/知识库工具（纯标准库 + 可选 DeepSeek）。"""

import argparse
import json
import os
import re
import sys
import urllib.request


def parse_srt(text):
    blocks = []
    for raw in re.split(r"\n\s*\n", text.strip()):
        lines = raw.splitlines()
        if len(lines) < 2:
            continue
        idx = lines[0].strip()
        time_line = next((l for l in lines if "-->" in l), "")
        content = [l for l in lines[1:] if "-->" not in l]
        if not time_line:
            continue
        start, end = time_line.replace(",", ".").split("-->")[:2]
        blocks.append({"idx": idx, "start": start.strip(), "end": end.strip(),
                       "text": " ".join(content).strip()})
    return blocks


def ts2sec(ts):
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def srt2md(input_path, out_path, merge_sec=3.0):
    with open(input_path, "r", encoding="utf-8") as f:
        blocks = parse_srt(f.read())
    merged = []
    for b in blocks:
        if merged and ts2sec(b["start"]) - ts2sec(merged[-1]["end"]) <= merge_sec:
            merged[-1]["text"] += " " + b["text"]
            merged[-1]["end"] = b["end"]
        else:
            merged.append(dict(b))
    lines = ["# 播客逐字稿", ""]
    for b in merged:
        t = b["start"][:8]
        lines.append("**[%s]** %s" % (t, b["text"]))
        lines.append("")
    out = "\n".join(lines)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
    print("已生成 %s（%d 段）" % (out_path, len(merged)))


def call_llm(prompt, key):
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4, "max_tokens": 2000,
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())["choices"][0]["message"]["content"]


def build(input_path, out_path, api_key=""):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    lines = [l for l in text.splitlines() if l.strip()]
    lines = lines[1:] if lines and lines[0].startswith("#") else lines
    body = "\n".join(lines)
    words = len(re.sub(r"\s", "", body))
    out = ["# 播客知识库笔记", "", "总字数：%d" % words, ""]
    if api_key:
        try:
            summary = call_llm(
                "你是播客主编。根据以下逐字稿生成：1）3-5 个章节标题及时间段；"
                "2）核心要点 5 条；3）5 个标签。输出 Markdown。\n\n逐字稿：\n%s" % body[:6000], api_key)
            out.append(summary)
        except Exception as e:
            out.append("（AI 摘要失败：%s）" % e)
    else:
        # 规则版：按话题词切分
        topics = ["副业", "AI", "赚钱", "工具", "案例", "风险", "行动"]
        out.append("## 关键词索引")
        out.append("")
        for t in topics:
            n = body.count(t)
            if n:
                out.append("- %s：出现 %d 次" % (t, n))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("知识库已生成 %s" % out_path)


def split(input_path, out_dir, keywords):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    os.makedirs(out_dir, exist_ok=True)
    paras = re.split(r"\n\s*\n", text)
    buckets = {k: [] for k in keywords}
    bucket_other = []
    for p in paras:
        hit = next((k for k in keywords if k in p), None)
        if hit:
            buckets[hit].append(p)
        else:
            bucket_other.append(p)
    for k, ps in buckets.items():
        if ps:
            with open(os.path.join(out_dir, k + ".md"), "w", encoding="utf-8") as f:
                f.write("# %s\n\n%s\n" % (k, "\n\n".join(ps)))
    if bucket_other:
        with open(os.path.join(out_dir, "其他.md"), "w", encoding="utf-8") as f:
            f.write("# 其他\n\n%s\n" % "\n\n".join(bucket_other))
    print("已切分为 %d 个主题文件 → %s" % (len(buckets) + 1, out_dir))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("srt2md"); p.add_argument("--input", required=True); p.add_argument("--out", required=True); p.set_defaults(fn=lambda a: srt2md(a.input, a.out))
    p = sub.add_parser("build"); p.add_argument("--input", required=True); p.add_argument("--out", required=True); p.add_argument("--api-key", default=""); p.set_defaults(fn=lambda a: build(a.input, a.out, a.api_key))
    p = sub.add_parser("split"); p.add_argument("--input", required=True); p.add_argument("--out", required=True); p.add_argument("--keywords", default="副业,AI,赚钱"); p.set_defaults(fn=lambda a: split(a.input, a.out, [k.strip() for k in a.keywords.split(",")]))
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
