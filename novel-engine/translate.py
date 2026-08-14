#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调用 DeepSeek 将中文章节翻译为英文（出海试译）。"""

import argparse
import json
import os
import re
import sys
import urllib.request


def call(prompt, max_tokens=8000):
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="中文章节目录")
    ap.add_argument("--out", required=True, help="英文输出目录")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=3)
    ap.add_argument("--glossary", default="", help="术语表文件路径（可选）")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    glossary = ""
    if args.glossary and os.path.exists(args.glossary):
        with open(args.glossary, "r", encoding="utf-8") as f:
            glossary = f.read()
    for n in range(args.start, args.end + 1):
        src = os.path.join(args.source, "ch%03d.md" % n)
        if not os.path.exists(src):
            print("跳过缺失：%s" % src)
            continue
        with open(src, "r", encoding="utf-8") as f:
            text = f.read()
        prompt = (
            "You are a professional translator for Chinese xianxia/fantasy web novels.\n"
            "Translate the following Chinese chapter into natural, vivid English suitable for "
            "Western readers of translated cultivation novels. Keep names as pinyin "
            "(e.g., Shen Yanzhi), keep cultivation terms consistent, and preserve the tone, "
            "pacing and cliffhangers. Output only the translated chapter, starting with the "
            "same markdown heading style (# Chapter N ...).\n\n"
            "Glossary/notes (use when relevant):\n%s\n\n"
            "Chinese chapter:\n%s" % (glossary, text)
        )
        print("翻译第 %d 章…" % n, flush=True)
        en = call(prompt)
        en = re.sub(r"^```(?:markdown|text)?\s*", "", en, flags=re.M).strip()
        out_path = os.path.join(args.out, "ch%03d-en.md" % n)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(en + "\n")
        print("  已写入 %s" % out_path, flush=True)
    print("完成", flush=True)


if __name__ == "__main__":
    sys.exit(main())
