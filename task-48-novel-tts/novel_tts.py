#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小说朗读 TTS（MiniMax speech-02）。"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.request


def split_sentences(text, limit=120):
    parts = re.split(r"(?<=[。！？!?])", text)
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) > limit:
            if cur:
                out.append(cur)
            cur = p
        else:
            cur += p
    if cur:
        out.append(cur)
    return [s.strip() for s in out if s.strip()]


def tts(text, voice, out_path, key, group_id, base_url):
    body = json.dumps({
        "model": "speech-02-hd",
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": voice, "speed": 1.0, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1},
    }).encode()
    req = urllib.request.Request(
        base_url + "/v1/t2a_v2?GroupId=" + group_id, data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode())
    if data.get("base_resp", {}).get("status_code") != 0:
        raise RuntimeError(data.get("base_resp", {}).get("status_msg", "TTS 失败"))
    audio = data["data"]["audio"]
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(audio))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default="male-qn-qingse",
                    choices=["male-qn-qingse", "female-shaonv", "female-chengshu", "male-jianlang"])
    ap.add_argument("--max-sentences", type=int, default=0, help="0=整章")
    args = ap.parse_args()
    key = os.environ.get("MINIMAX_API_KEY", "")
    group = os.environ.get("MINIMAX_GROUP_ID", "")
    base = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com")
    if not key or not group:
        raise SystemExit("请设置 MINIMAX_API_KEY 与 MINIMAX_GROUP_ID（platform.minimaxi.com 生成）")
    with open(args.chapter, "r", encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^#.*$", "", text, flags=re.M)
    sents = split_sentences(text)
    if args.max_sentences:
        sents = sents[:args.max_sentences]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    for i, s in enumerate(sents):
        path = args.out if len(sents) == 1 else args.out.replace(".mp3", "-%02d.mp3" % (i + 1))
        print("合成 %d/%d …" % (i + 1, len(sents)), flush=True)
        tts(s, args.voice, path, key, group, base)
    print("完成：%s" % args.out)


if __name__ == "__main__":
    sys.exit(main())
