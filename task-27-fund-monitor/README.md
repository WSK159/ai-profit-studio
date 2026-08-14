# 基金净值监控提醒工具（任务 27）

## 功能

- 抓取天天基金实时估值接口，计算涨跌幅
- 阈值提醒（终端 + 可选 Webhook POST）
- 支持多基金代码 CSV、定时循环

## 用法

```bash
python fund_monitor.py --codes 005827,161725 --threshold 2.0
python fund_monitor.py --csv funds.csv --loop 60 --webhook https://example.com/hook
```

## 盈利路线

- 免费 CLI 引流 → 托管提醒服务（微信/钉钉推送）订阅
- 组合任务 26 做"净值+舆情"数据产品
