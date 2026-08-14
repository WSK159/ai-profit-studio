#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基金净值监控（东财历史净值 + 日涨跌阈值提醒）。"""

import argparse
import csv
import json
import re
import sys
import time
import urllib.request

URL = "https://fund.eastmoney.com/pingzhongdata/{code}.js"


def fetch_fund(code):
    req = urllib.request.Request(URL.format(code=code),
                                 headers={"User-Agent": "Mozilla/5.0",
                                          "Referer": "https://fund.eastmoney.com/"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8", errors="replace")
    m = re.search(r"var Data_netWorthTrend = (\[.*?\]);", text, re.S)
    if not m:
        return None
    series = json.loads(m.group(1))
    if len(series) < 2:
        return None
    last, prev = series[-1], series[-2]
    return {"name": "基金%s" % code, "last_nav": last["y"], "prev_nav": prev["y"],
            "date": last.get("x")}


def parse_change(data):
    last = float(data["last_nav"])
    prev = float(data["prev_nav"])
    change = (last - prev) / prev * 100 if prev else 0.0
    return last, prev, change


def notify_webhook(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status


def monitor(codes, threshold, loop, webhook):
    while True:
        for code in codes:
            try:
                data = fetch_fund(code)
                if not data:
                    print("[%s] 解析失败" % code, flush=True)
                    continue
                last, prev, change = parse_change(data)
                flag = "▲" if change > 0 else "▼"
                line = "[%s] %s 最新净值 %s 前日 %s 日涨跌 %s%.2f%%" % (
                    code, data.get("name", ""), last, prev, flag, abs(change))
                print(line, flush=True)
                if abs(change) >= threshold:
                    alert = "%s：%s%.2f%%（净值 %s）" % (data.get("name", code), flag, abs(change), last)
                    print("!! 触发阈值：" + alert, flush=True)
                    if webhook:
                        try:
                            notify_webhook(webhook, {"text": alert})
                            print("  已推送 Webhook", flush=True)
                        except Exception as e:
                            print("  Webhook 推送失败：%s" % e, flush=True)
            except Exception as e:
                print("[%s] 请求失败：%s" % (code, e), flush=True)
            time.sleep(3)
        if not loop:
            break
        time.sleep(loop)


def main():
    ap = argparse.ArgumentParser(description="基金净值监控")
    ap.add_argument("--codes", default="", help="逗号分隔基金代码")
    ap.add_argument("--csv", default="", help="CSV 文件（每行一个代码）")
    ap.add_argument("--threshold", type=float, default=2.0, help="涨跌幅阈值（%%）")
    ap.add_argument("--loop", type=int, default=0, help="循环间隔秒数（0=只跑一次）")
    ap.add_argument("--webhook", default="", help="提醒 Webhook URL")
    args = ap.parse_args()

    codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    if args.csv:
        with open(args.csv, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                codes.append(row[0].strip())
    if not codes:
        raise SystemExit("请提供 --codes 或 --csv")
    monitor(codes, args.threshold, args.loop, args.webhook)


if __name__ == "__main__":
    sys.exit(main())
