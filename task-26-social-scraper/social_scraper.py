#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用礼貌采集框架（纯标准库）。"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error


def fetch(url, headers=None, timeout=30):
    h = {"User-Agent": "polite-scraper/1.0 (+research)"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def run(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    name = cfg["name"]
    urls = cfg["urls"]
    headers = cfg.get("headers", {})
    rps = cfg.get("rate_limit_per_min", 30)
    interval = 60.0 / rps
    retries = cfg.get("retries", 3)
    out_path = cfg.get("output", name + ".jsonl")
    mode = cfg.get("mode", "raw")  # raw | json | jsonpath-simple

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    total = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for url in urls:
            for attempt in range(1, retries + 1):
                try:
                    status, body = fetch(url, headers)
                    if status >= 400:
                        raise urllib.error.HTTPError(url, status, "HTTP %d" % status, None, None)
                    record = {"url": url, "status": status}
                    if mode == "json":
                        record["data"] = json.loads(body.decode("utf-8", errors="replace"))
                    else:
                        record["text"] = body.decode("utf-8", errors="replace")
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    total += 1
                    print("OK  %s" % url, flush=True)
                    break
                except Exception as e:
                    print("RETRY %d/%-2d %s : %s" % (attempt, retries, url, e), flush=True)
                    time.sleep(2 ** attempt)
            time.sleep(interval)
    print("完成：%s 共写入 %d 条 → %s" % (name, total, out_path))


def main():
    ap = argparse.ArgumentParser(description="礼貌采集框架")
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    run(args.config)


if __name__ == "__main__":
    sys.exit(main())
