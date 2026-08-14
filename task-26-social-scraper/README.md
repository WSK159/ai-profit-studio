# 社媒数据采集工具（任务 26）

## 功能

- 通用"礼貌采集"框架：配置化 URL/请求头/限速/重试/输出 JSONL
- 内置示例：GitHub 公共 API 采集（用户仓库列表）
- 遵守 robots 精神：默认限速 + 指数退避重试 + 记录 UA

## 用法

```bash
python social_scraper.py --config examples/github.json
```

## 盈利路线

- 开源引流；企业定制版（合规采集 + 报告）收费
- 与任务 25（浏览器自动化）组合成数据产品

## 合规提醒

- 仅采集公开数据、遵守目标站 ToS 与 robots.txt、不采集个人信息
- 商业使用前确认授权
