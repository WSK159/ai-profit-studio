# AI 浏览器自动化 CLI（任务 25）

## 功能

- 纯 Python 标准库实现 Chrome DevTools Protocol（CDP）客户端，零依赖
- 命令：launch / navigate / title / text / eval / screenshot
- 可接 DeepSeek 做"看页面→写操作"的 AI Agent 流程

## 用法

```bash
python browser_cli.py launch --port 9222
python browser_cli.py navigate --url https://example.com
python browser_cli.py text
python browser_cli.py eval --js "document.title"
python browser_cli.py screenshot --out shot.png
```

## 说明

- 自带最小 WebSocket 客户端（RFC 6455），不依赖 websocket-client 等第三方库
- `python browser_cli.py selftest` 可无浏览器自测帧编解码

## 盈利路线

- 开源引流 → Pro：AI 自动操作（填表/巡检/截图报告）
- 作为"AI Agent 工具箱"的一部分订阅收费
