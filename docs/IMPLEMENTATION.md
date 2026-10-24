# ModeCalc 实现计划

## 技术栈

| 层 | 选型 |
|---|---|
| MIDI | mido + python-rtmidi |
| 后端 | Python + aiohttp + WebSocket (调试) / pywebview (桌面) |
| 前端 | Vanilla JS + VexFlow 5 (CDN) + SVG |
| 字体 | Quicksand Medium (和弦名) |
| 打包 | PyInstaller → 单 exe |
| 测试 | pytest |

## 当前状态

- [x] Step 1–9: Web 应用完成
- [x] Step 10: pywebview GUI 包装（完成）

---

## Step 1–8: Web 核心（已完成）

### chord_engine.py

15 种和弦模板（三和弦 6 + 七和弦 9）。

**模板：**
- 三和弦: Major [0,4,7], Minor [0,3,7], Dim [0,3,6], Aug [0,4,8], Sus4 [0,5,7], Sus2 [0,2,7]
- 七和弦: Maj7 [0,4,7,11], Dom7 [0,4,7,10], Min7 [0,3,7,10], MinMaj7 [0,3,7,11], Half-dim7 [0,3,6,10], Dim7 [0,3,6,9], Dom7sus4 [0,5,7,10]

**音程名（英文）：**
- 0: Perfect Unison, 1: minor 2nd, 2: Major 2nd, 3: minor 3rd, 4: Major 3rd, 5: Perfect 4th, 6: Tritone, 7: Perfect 5th, 8: minor 6th, 9: Major 6th, 10: minor 7th, 11: Major 7th
- 显示格式: `{低音音名} {音程名}`，如 "C Perfect 5th"

**和弦匹配策略：**
1. 精确匹配 + 子集匹配 → 收集所有候选
2. 优先选原位和弦（低音=根音，无 slash），无原位时选第一个转位
3. 转位显示: `根音和弦/低音`，如 "C/E"

### midi_handler.py

回调+Queue 双线程模型，5ms 轮询。自动过滤虚拟端口。

### server.py

aiohttp + WebSocket，端口 8765。`--list` 列出设备，`--port` 指定。

### app.js

WebSocket 客户端，30ms debounce。`updateUI(data)` 全局入口（pywebview 可直接调用）。

---

## Step 9: UI（已完成）

### 布局

```
┌──────────────────────────────────────┐
│ C△7                                 │ 和弦名 (Quicksand Medium, 左对齐, 固定高度)
├──────────────┬───────────────────────┤
│  staff 300px │  side-panel（留空）   │ 中间行
├──────────────┴───────────────────────┤
│         keyboard 全宽               │ 底部
└──────────────────────────────────────┘
```

- 背景: 纯白 `#ffffff`
- 最大宽度: 1000px，居中
- 和弦名: Quicksand Medium, 500 weight, `height: 3.2rem`（固定，防跳动）
- 键盘: 88 键 (A0–C8), 90px 高, 全宽, SVG 内部黑色边框

### 键盘

- 白键 `#ffffff`, 深灰描边 `#333333`
- 黑键 `#1a1a1a`
- 高亮: 白键 `#64b5f6`, 黑键 `#42a5f5`
- SVG 内部 `<rect>` 绘制 1.5px 黑色外框 + 3px 圆角

### 五线谱 (staff.js)

- VexFlow 5 Factory API
- 大谱表: 高音谱 (≥C4) + 低音谱 (<C4)
- 无小节线 (`rightBarline: 'none', leftBarline: 'none'`)
- 无 brace 连接器
- 画布 300×280px, System x=50, NS_SHIFT=100
- `clef` 参数显式传：高音 `'treble'`，低音 `'bass'`（VexFlow 默认 treble）
- `toVexKey()`: `{name: 'C#', octave: 4}` → `'c#/4'`（小写化即 VexFlow 格式）
- `NS_SHIFT=100` + 手动 format/draw：音符+升降号右移 100px，谱号与音符间留空
- 升降号: `factory.Accidental({ type })` + `addModifier()` 手动附加（VexFlow 5 不自动渲染）
- 正则 `^[a-g][#b]` 区分 B natural (`b/3`) 和 B-flat (`bb/3`)

---

## Step 10: pywebview GUI 包装（未开始）

详见 `docs/GUI_EXECUTION_PLAN.md`。

**待执行：**
- [x] `pip install pywebview pyinstaller`
- [x] 新建 `app.py`
- [x] `static/app.js` 条件化 WS / JS bridge
- [x] `static/vendor/` 本地化 vexflow-core.js + woff2 字体
- [x] `build.bat` PyInstaller 打包（Python 3.12）
- [x] 集成测试

## 文件清单（当前实际）

```
ModeCalc/
├── server.py
├── midi_handler.py
├── chord_engine.py
├── static/
│   ├── index.html
│   ├── app.js
│   ├── keyboard.js
│   ├── staff.js
│   ├── style.css
│   ├── icon.ico
│   └── fonts/
│       └── Quicksand-Medium.ttf
├── font/                          ← 原始字体文件（未使用）
│   └── Quicksand-Regular.ttf
├── tests/
│   ├── test_chord_engine.py
│   └── test_midi_handler.py
├── requirements.txt
├── docs/
│   ├── adr/
│   │   ├── 0001-web-architecture.md
│   │   ├── 0002-midi-threading.md
│   │   ├── 0003-chord-matching.md
│   │   └── 0004-pywebview-desktop-gui.md
│   ├── changelog/
│   │   └── 2026-07-10_fix-bass-clef-note-position.md
│   ├── IMPLEMENTATION.md
│   └── GUI_EXECUTION_PLAN.md
└── CONTEXT.md
```

## 验证

```bash
# 单元测试
pytest tests/ -v                          # 20 passed

# Web 模式
python server.py                          # 浏览器 → localhost:8765
python server.py --port "设备名"          # 有 MIDI 键盘

# 桌面模式（待实现）
python app.py                             # pywebview 窗口
```
