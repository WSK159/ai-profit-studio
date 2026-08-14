# 播客转写/知识库 CLI（任务 44）

## 功能

- `srt2md`：把 SRT 字幕转成 Markdown 逐字稿（合并短句、按时间分段）
- `build`：把逐字稿整理成知识库笔记（章节、要点、标签），可接 DeepSeek 摘要
- `split`：按主题关键词切分长稿

## 用法

```bash
python podcast_tool.py srt2md --input sample.srt --out transcript.md
python podcast_tool.py build --input transcript.md --out notes.md [--api-key sk-...]
```

## 盈利路线

- 播客主/UP 主内容复用工具；与任务 39 播客联动
- Pro：AI 摘要 + 章节标题 + 短视频切片建议
