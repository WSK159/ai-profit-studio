# 小说连载引擎（Novel Serialization Engine）

用于把《万界长生图》《巷口的糖水铺》《星海拾荒者》《第七个证物》四部小说持续写到 500 章 / 50 万字以上。

## 原理

- 以每部小说的 `outline.md`（总纲+分卷+细纲+人物卡+写作规范）为骨架
- 调用 DeepSeek API 按章续写，每批 3 章
- 每批结尾让模型输出 `[STATE]` 上下文摘要，写入 `state.json`，下一批自动带上，保证前后文连贯
- 章节自动写入 `chapters/chXXX.md`，文件名数字自然排序

## 用法

```bash
$env:DEEPSEEK_API_KEY="sk-..."
python novel-engine/serialize.py --novel task-01-wanjie-changsheng-tu --chapters 6
```

## 质量保障

- 每章 1100-1400 字、章末留钩子、每 3 章一个小高潮
- 批次之间自动带入前文摘要与未回收伏笔
- 全部完成后统一执行"回头检查与修改"：逐章抽查、修 bug、补伏笔
