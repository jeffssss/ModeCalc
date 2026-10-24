# v1.0.0 里程碑 — ModeCalc 正式发布

## 概述

ModeCalc v1.0.0 完成。实时 MIDI 和弦/调式识别桌面应用，pywebview + VexFlow 大谱表 + SVG 88键钢琴键盘。

## 功能清单

### MIDI
- [x] MIDI 设备枚举与选择（菜单栏 MIDI Input）
- [x] 实时音符采集，30ms 推送
- [x] 延音踏板支持
- [x] 虚拟 MIDI 端口兼容

### 和弦分析
- [x] 15 种和弦模板（6 三和弦 + 7 七和弦 + 2 sus）
- [x] 精确/子集/超集匹配
- [x] 转位识别（slash chord 表示）
- [x] 不完整匹配标记 ?

### 调式分析
- [x] 25+ 父音阶，6 分类折叠组
- [x] Chord / Mode 双透镜切换
- [x] 调式 Matches 面板，点击锁定时高亮键盘

### 五线谱
- [x] VexFlow 5 大谱表（高音 + 低音）
- [x] 调号渲染
- [x] 临时升降号

### UI
- [x] 菜单栏：Key（15 调）、MIDI Input、Help
- [x] Frameless 窗口
- [x] 帮助弹窗
- [x] 调试栏（MIDI/Font/Notes/Sustain 状态）
- [x] 整体 UI ×1.2 缩放

### 部署
- [x] 单 exe 打包（PyInstaller）
- [x] 内嵌字体（Quicksand/Bravura/Academico）

## 窗口尺寸

| 版本 | 宽 | 高 |
|---|---|---|
| 初始 | 1000 | 500 |
| v1.0.0 | **1200** | **600** |

## 项目结构

```
ModeCalc/
├── app.py               # pywebview 桌面入口
├── server.py            # aiohttp + WebSocket 服务端
├── chord_engine.py      # 和弦/调式分析引擎
├── mode_engine.py       # 调式匹配引擎
├── midi_handler.py      # MIDI 端口管理
├── static/
│   ├── index.html       # 主界面
│   ├── style.css        # 样式表
│   ├── app.js           # 前端主控
│   ├── keyboard.js      # SVG 88 键键盘
│   ├── staff.js         # VexFlow 大谱表
│   └── fonts/
│       └── Quicksand-Medium.ttf
└── docs/
    └── milestone-v1.0.0.md
```

## 后续方向

- 全局热键（琴键映射）
- 主题色切换
- 录音回放
- 导出 MIDI / MusicXML
