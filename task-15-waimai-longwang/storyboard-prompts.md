# 《外卖龙王》生图/生视频提示词包

## 一、角色形象提示词（MiniMax image-01 / 海螺）

### 陆沉（男主）
```
Chinese action drama hero, 28 years old man, short black hair, calm piercing eyes, yellow delivery uniform with black helmet, muscular build under uniform, city street background, cinematic lighting, realistic style, 4k
```

### 苏晚（女主）
```
Chinese businesswoman, 26 years old, elegant black business suit, high ponytail, sharp intelligent eyes, standing in modern office lobby, cinematic lighting, realistic style, 4k
```

### 潮汐（反派首领）
```
Chinese mysterious man in black trench coat, 35 years old, cold expression, half face in shadow, red glowing dot on chest (implant), dark lab background, cinematic thriller style, 4k
```

### 夜枭（杀手）
```
Chinese female assassin, black leather jacket, short silver hair, face mask, night rooftop city background, neon lights, cinematic action style, 4k
```

## 二、场景提示词

- 云城街头：`Chinese modern city street at dusk, traffic, neon signs, delivery riders on electric bikes, cinematic wide shot`
- 盛天大厦 47 层走廊：`dark corporate corridor, heavy metal door, red security light, futuristic surveillance, thriller atmosphere`
- 地下实验室：`underground laboratory, rows of sleep pods with glowing blue liquid, scientists in hazmat suits, dystopian sci-fi`
- 出租屋：`small cramped rental room at night, single desk, old metal box, warm lamp, melancholic mood`

## 三、分镜模板（每集 12-14 镜）

| 镜头 | 景别 | 画面 | 台词/字幕 | 音效 | 视频提示词要点 |
|---|---|---|---|---|---|
| 1 | 全景 | 主角出场 | 旁白钩子 | 城市环境音 | wide establishing shot, main character center |
| 2 | 特写 | 关键道具 | 悬念句 | 心跳声 | extreme close-up on object, shallow depth of field |
| 3-6 | 中景/快切 | 冲突升级 | 台词交锋 | 配乐渐强 | medium shots, fast cuts, increasing tension |
| 7-9 | 动作 | 高潮打脸 | 金句 | 打击音效 | dynamic action sequence, impact frames |
| 10-12 | 近景 | 反转/伏笔 | 钩子台词 | 留白 | close-up on reaction, slow zoom |
| 13-14 | 特写/黑场 | 下集预告钩子 | 字幕 | 悬疑音效 | end card, dramatic pause |

## 四、使用说明

- 所有提示词可直接作为 MiniMax `image-01` / `video-01` 的 prompt 使用
- 每集先出 3 张关键帧（开场钩子/高潮打脸/结尾悬念），再生成视频片段
- 角色一致性：固定角色提示词前缀 + 场景后缀；参考图用"分镜角色引用归一化"（见 my-first-project 流水线）
- 台词字幕使用任务 7 脚本工作台生成的 SRT 进行压制
