#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 字幕翻译（SRT 保留时间轴）。"""

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
        blocks.append({"idx": idx, "time": time_line, "text": "\n".join(content)})
    return blocks


def translate_batch(texts, lang, key):
    joined = "\n---\n".join(texts)
    target = "English" if lang == "en" else "简体中文"
    prompt = (
        "Translate each numbered subtitle line into %s. Keep it natural and concise, "
        "suitable for subtitles (<=30 words per line). Preserve line breaks within each block. "
        "Output each block separated by the same '---' separator, in the same order.\n\n%s"
        % (target, joined)
    )
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3, "max_tokens": 4000,
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())["choices"][0]["message"]["content"]
    return [s.strip() for s in out.split("---")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", default="en", choices=["en", "zh"])
    ap.add_argument("--api-key", required=True)
    ap.add_argument("--batch", type=int, default=20)
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        blocks = parse_srt(f.read())
    if not blocks:
        raise SystemExit("没有解析到字幕块")

    translated = []
    for i in range(0, len(blocks), args.batch):
        chunk = blocks[i:i + args.batch]
        texts = [b["text"] for b in chunk]
        print("翻译 %d-%d / %d …" % (i + 1, i + len(chunk), len(blocks)), flush=True)
        out = translate_batch(texts, args.lang, args.api_key)
        if len(out) != len(chunk):
            out = out + [t for t in texts[len(out):]]
        translated.extend(out)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for b, t in zip(blocks, translated):
            f.write("%s\n%s\n%s\n\n" % (b["idx"], b["time"], t))
    print("完成：%s" % args.out)


if __name__ == "__main__":
    sys.exit(main())
