# 2026-07-11 MIDI 管道重构 + 五线谱修复 + 调试设施

## 变更

### MIDI 采集 (app.py + midi_handler.py + server.py)

- `midi_handler.poll()` — 移除 `changed` 标志，永远返回当前 `_active_notes` 快照。去重逻辑从下层移除。
- `app.py.AppState` → `MidiState`。`poll_and_recognize()` → `get_state()`。去掉 `_previous` 去重。
- `midi_loop()` 改为固定 30ms 推送当前状态，不再依赖"是否有变化"决定是否推送。
- `server.py` 同步修改：`poll_and_recognize()` → `get_state()`，去掉 `_previous`，`midi_loop` 固定 30ms 推送。

### 前端 (app.js + staff.js + index.html + style.css)

- `updateUI()` 加入 `JSON.stringify` 去重。Python 端不再负责去重判断。
- `index.html` 脚本加载顺序调整：`keyboard.js` + `staff.js` 移到 `app.js` 之前。
- `staff.js` IIFE 末尾主动调用 `window.renderStaff([])` 初始化空谱表。
- `staff.js` 字体加载改为 CSS `@font-face` + `document.fonts.load()`（绕过 VexFlow 的 FontFace API，避免 `file://` 协议阻塞）。
- 底部调试栏：显示 MIDI 连接状态、字体加载状态、当前音符。
- 本地化 VexFlow 字体文件：`static/vendor/fonts/bravura/bravura.woff2` + `academico/academico.woff2`。

### 构建 (app.py + build.bat + requirements.txt)

- `build.bat` 改为显式指定 Python 3.12 的 pyinstaller（python-rtmidi 需要预编译 wheel）。
- 追加 `--hidden-import mido.backends.rtmidi --hidden-import rtmidi`，防止 PyInstaller 漏绑 C 扩展后端。
- `webview.start(debug=False)` — 关闭 DevTools 自动弹出。
- 追加文件日志 `%TEMP%\ModeCalc_debug.log`。
- `requirements.txt` 移回 `mido` + `python-rtmidi`。

### 移除

- `winmidi.py`（ctypes 纯 Python MIDI 方案，已不需要）。
- `app.py` 中的心跳修正代码（不再需要，30ms 固定推送兜底）。

## 原因

- MIDI 消息批量到达时，`changed` 标志 + `_previous` 两层去重耦合导致 note_off 被跳过（最后一个音符不消失）。
- 柱式和弦输入时，部分消息在批处理中改变被 `_previous` 屏蔽（和弦丢音）。
- 根因是"是否推送"的判断逻辑分散在 poll / poll_and_recognize / midi_loop 三层，状态不一致。
- 解决方案：Python 端无状态拉取 + 固定间隔推送，JS 端 `JSON.stringify` 单点去重。

## 影响

- 两个问题：最后一个音符残留 + 和弦丢音，一并解决。
- `server.py`（浏览器调试模式）数据模型与 `app.py`（exe 模式）一致。
- 日志文件在 `%TEMP%\ModeCalc_debug.log`。
- exe 构建使用 Python 3.12。
