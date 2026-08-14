# Markdown → EPUB 打包工具（任务 6）

## 功能

- 把一整个目录的 Markdown 章节批量打包成标准 EPUB 电子书
- 纯 Python 标准库实现，零依赖，Windows/macOS/Linux 通用
- 自动从文件名排序章节、从 `# 标题` 提取章名、生成目录（NCX + NAV）
- 输出可直接上传到微信读书 / 番茄 / Apple Books / Kindle（epub 转 mobi 后）

## 用法

```bash
python md2epub.py --title "万界长生图" --author "XX" \
  --out 输出.epub 章节目录/*.md
```

可选参数：`--lang zh-CN`、`--sort natural|lexical`、`--css 自定义样式文件`

## 盈利路线

- 免费开源引流 → 赞助/打赏
- 作为"小说发布工作流"的一部分卖给写作者（配合任务 10 排版工具打包成 Pro 工具）
- 接"代排版"服务：帮作者把稿子排版成平台要求的格式
