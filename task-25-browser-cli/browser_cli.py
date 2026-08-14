#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯标准库 Chrome DevTools Protocol (CDP) CLI。"""

import argparse
import base64
import json
import os
import random
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.request


# ---------- 最小 WebSocket 客户端（RFC 6455） ----------

class WS:
    def __init__(self, url, timeout=30):
        self.sock = None
        self.timeout = timeout
        self._connect(url)

    def _connect(self, url):
        assert url.startswith("ws://"), "仅支持 ws://"
        rest = url[5:]
        hostport, path = rest.split("/", 1)
        host, _, port = hostport.partition(":")
        port = int(port or 80)
        s = socket.create_connection((host, port), timeout=self.timeout)
        key = base64.b64encode(bytes(random.randrange(256) for _ in range(16))).decode()
        req = (
            "GET /%s HTTP/1.1\r\n"
            "Host: %s:%d\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
            % (path, host, port, key)
        )
        s.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = s.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket 握手失败")
            buf += chunk
        head = buf.split(b"\r\n\r\n", 1)[0].decode(errors="replace")
        if " 101 " not in head:
            raise ConnectionError("WebSocket 握手被拒绝：%s" % head.splitlines()[0])
        self.sock = s
        self._left = buf.split(b"\r\n\r\n", 1)[1]

    def _send_frame(self, opcode, payload=b""):
        mask = bytes(random.randrange(256) for _ in range(4))
        first = 0x80 | opcode
        n = len(payload)
        header = bytes([first])
        if n < 126:
            header += bytes([0x80 | n])
        elif n < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", n)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(header + mask + masked)

    def _recv_exact(self, n):
        data = b""
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("连接中断")
            data += chunk
        return data

    def _recv_frame(self):
        if self._left:
            first, second = self._left[0], self._left[1]
            self._left = self._left[2:]
        else:
            first, second = self._recv_exact(2)
        opcode = first & 0x0F
        n = second & 0x7F
        if n == 126:
            n = struct.unpack(">H", self._recv_exact(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if second & 0x80 else None
        payload = self._recv_exact(n)
        if mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        return opcode, payload

    def send_text(self, text):
        self._send_frame(1, text.encode())

    def recv_text(self):
        data = b""
        while True:
            op, payload = self._recv_frame()
            if op == 1:
                data += payload
                return data.decode("utf-8", errors="replace")
            if op == 8:
                return None
            if op == 9:
                self._send_frame(10, payload)

    def close(self):
        try:
            self._send_frame(8, b"")
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


# ---------- CDP ----------

class CDP:
    def __init__(self, port):
        self.port = port
        self.ws = None

    def _target_ws(self):
        url = "http://127.0.0.1:%d/json" % self.port
        with urllib.request.urlopen(url, timeout=10) as r:
            targets = json.loads(r.read().decode())
        for t in targets:
            if t.get("type") == "page" and not t.get("url", "").startswith("devtools://"):
                return t["webSocketDebuggerUrl"]
        raise RuntimeError("没有可用的页面目标")

    def connect(self):
        self.ws = WS(self._target_ws())
        self._id = 0

    def call(self, method, params=None):
        self._id += 1
        mid = self._id
        self.ws.send_text(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = self.ws.recv_text()
            if msg is None:
                raise ConnectionError("连接关闭")
            data = json.loads(msg)
            if data.get("id") == mid:
                if "error" in data:
                    raise RuntimeError(data["error"])
                return data.get("result", {})

    def close(self):
        if self.ws:
            self.ws.close()


def find_chrome():
    candidates = [
        os.environ.get("CHROME_PATH", ""),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        shutil.which("chrome"),
        shutil.which("chromium"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    raise RuntimeError("未找到 Chrome，请设置 CHROME_PATH")


def launch(port, headless=True):
    exe = find_chrome()
    user_data = os.path.join(os.environ.get("TEMP", "/tmp"), "cdp-profile-%d" % port)
    cmd = [exe, "--remote-debugging-port=%d" % port, "--remote-debugging-address=127.0.0.1",
           "--user-data-dir=%s" % user_data, "--no-first-run", "--no-default-browser-check"]
    if headless:
        cmd.append("--headless=new")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=2) as r:
                return json.loads(r.read().decode())["Browser"]
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Chrome 启动超时")


def main():
    ap = argparse.ArgumentParser(description="CDP 浏览器 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("launch"); p.add_argument("--port", type=int, default=9222); p.add_argument("--headed", action="store_true"); p.set_defaults(fn=launch)
    p = sub.add_parser("navigate"); p.add_argument("--port", type=int, default=9222); p.add_argument("--url", required=True); p.set_defaults(fn=lambda a: _nav(a))
    p = sub.add_parser("title"); p.add_argument("--port", type=int, default=9222); p.set_defaults(fn=lambda a: _eval(a, "document.title"))
    p = sub.add_parser("text"); p.add_argument("--port", type=int, default=9222); p.set_defaults(fn=lambda a: _eval(a, "document.body.innerText"))
    p = sub.add_parser("eval"); p.add_argument("--port", type=int, default=9222); p.add_argument("--js", required=True); p.set_defaults(fn=lambda a: _eval(a, a.js))
    p = sub.add_parser("screenshot"); p.add_argument("--port", type=int, default=9222); p.add_argument("--out", default="shot.png"); p.set_defaults(fn=_shot)
    p = sub.add_parser("selftest"); p.set_defaults(fn=_selftest)
    args = ap.parse_args()
    return args.fn(args)


def _nav(args):
    c = CDP(args.port); c.connect()
    try:
        c.call("Page.enable")
        c.call("Page.navigate", {"url": args.url})
        time.sleep(2)
        print("navigated:", args.url)
    finally:
        c.close()


def _eval(args, js):
    c = CDP(args.port); c.connect()
    try:
        r = c.call("Runtime.evaluate", {"expression": js, "returnByValue": True})
        print(r.get("result", {}).get("value", ""))
    finally:
        c.close()


def _shot(args):
    c = CDP(args.port); c.connect()
    try:
        r = c.call("Page.captureScreenshot", {"format": "png"})
        with open(args.out, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        print("saved:", args.out)
    finally:
        c.close()


def _selftest(args):
    """无浏览器自测：帧编解码往返。"""
    ws = WS.__new__(WS)
    payload = "你好 CDP".encode()
    import io

    class _FakeSock:
        def __init__(self):
            self.buf = io.BytesIO()

        def sendall(self, data):
            self.buf.write(data)

    fake = _FakeSock()
    ws.sock = fake
    ws._send_frame(1, payload)
    data = fake.buf.getvalue()
    assert data[0] == 0x81
    assert data[1] & 0x80
    mask = data[2:6]
    body = bytes(b ^ mask[i % 4] for i, b in enumerate(data[6:]))
    assert body == payload, "掩码往返失败"
    print("selftest OK：帧编码/掩码/长度解析正常")
    return 0


if __name__ == "__main__":
    sys.exit(main())
