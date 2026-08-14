# 小说自动朗读 TTS 工具（任务 48）

## 功能

- 读取 Markdown 章节，按句切分，调用 MiniMax speech-02 合成音频
- 支持男/女声、语速、采样率配置；按章输出 mp3

## 说明（重要）

- 需要有效的 MiniMax API Key（`MINIMAX_API_KEY`）与 `MINIMAX_GROUP_ID`
- 2026-08-15 实测：用户提供的 Key 无法通过 TTS 接口认证（1004 login fail，疑似网页会话令牌或已过期），请在 [platform.minimaxi.com](https://platform.minimaxi.com) 生成有效 API Key 后使用

## 用法

```bash
python novel_tts.py --chapter chapters/ch001.md --out audio/ch001.mp3 --voice female-shaonv
```
