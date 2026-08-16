#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动连载驱动：循环为九部未完结小说各续写10章，直到全部触发大结局，每轮自动提交推送。"""

import json
import os
import subprocess
import sys
import time

NOVELS = [
    "task-01-wanjie-changsheng-tu",
    "task-02-tangshuipu",
    "task-03-xinghai-shihuangzhe",
    "task-04-diqige-zhengwu",
    "task-21-xianzupu",
    "task-22-shenye-danganguan",
    "task-23-xiaofanguan-1988",
    "task-41-chunri-chichi",
    "task-42-moyu-system",
]


def ended(d):
    try:
        with open(os.path.join(d, "state.json"), encoding="utf-8") as f:
            return bool(json.load(f).get("ending"))
    except Exception:
        return False


def chapter_count(d):
    try:
        with open(os.path.join(d, "state.json"), encoding="utf-8") as f:
            return int(json.load(f).get("next", 1)) - 1
    except Exception:
        return 0


def safe_dir():
    return os.getcwd().replace("\\", "/")


def git(args):
    return subprocess.run(
        ["git", "-C", os.getcwd(), "-c", "safe.directory=" + safe_dir()] + args,
        capture_output=True, text=True,
    )


def push():
    for i in range(8):
        if i % 2 == 0:
            r = git(["push", "studio", "main"])
        else:
            r = git(["-c", "http.proxy=", "-c", "https.proxy=", "push", "studio", "main"])
        if r.returncode == 0:
            return True
        time.sleep(10)
    return False


def main():
    cycle = 0
    while not all(ended(d) for d in NOVELS):
        cycle += 1
        print("=== 第 %d 轮 ===" % cycle, flush=True)
        for d in NOVELS:
            if ended(d):
                print("%s 已完结，跳过" % d, flush=True)
                continue
            print("开始连载：%s" % d, flush=True)
            cmd = [sys.executable, "novel-engine/serialize.py", "--novel", d, "--chapters", "10"]
            if chapter_count(d) >= 600:
                print("%s 已超 600 章仍未完结，进入强制大结局模式" % d, flush=True)
                cmd = [sys.executable, "novel-engine/serialize.py", "--novel", d, "--chapters", "4", "--finale"]
            r = subprocess.run(cmd)
            if r.returncode != 0:
                print("警告：%s 本轮失败，下一轮重试" % d, flush=True)
        git(["add", "-A"])
        git(["-c", "user.name=WWSSK", "-c", "user.email=wangshike@example.com",
             "commit", "-m", "自动连载轮次 %d（全部完结后停）" % cycle])
        if push():
            print("已推送轮次 %d" % cycle, flush=True)
        else:
            print("推送失败，将在后续重试", flush=True)
        done = [d for d in NOVELS if ended(d)]
        print("当前已完结：%s" % (", ".join(done) if done else "无"), flush=True)
    print("全部九部小说已完结！", flush=True)


if __name__ == "__main__":
    main()
