# 小说分卷排版/质检 CLI（任务 10）

## 功能

- `stats`：统计每章字数、总字数、平均字数、目标达成度（如 500 章 / 50 万字）
- `check`：质检章节连续性（缺章/重号/乱序）、标题格式、疑似重复段落、结尾钩子
- `toc`：生成 Markdown 目录（章号 + 标题 + 字数）
- 纯 Python 标准库，零依赖

## 用法

```bash
python novel_tool.py stats --dir ../task-01-wanjie-changsheng-tu/chapters --goal 500:500000
python novel_tool.py check --dir ../task-01-wanjie-changsheng-tu/chapters
python novel_tool.py toc --dir ../task-01-wanjie-changsheng-tu/chapters
```

## 盈利路线

- 与任务 6（EPUB 打包）合并为"写作者发布工具链"付费工具
- 提供在线版（上传章节 → 出质检报告），按次收费
