# 2026-07-11 pywebview 桌面 GUI 封装

## 变更

- `app.py` — **新建** pywebview 主入口，替代 server.py 作为桌面启动入口
  - `AppState`: 持有 MidiHandler，提供 `poll_and_recognize()` 轮询+识别+去重
  - `Api`: JS bridge 类，暴露 `select_port()` / `quit_app()` 给前端
  - `midi_loop()`: 后台线程 5ms 轮询 MIDI，30ms 去重推送 JS
  - `_startup()`: 窗口就绪回调，显示设备列表，启动 MIDI 线程
- `static/index.html` — 修改：新增 `#device-picker` overlay（设备选择弹窗）
- `static/app.js` — 修改：`connect()` 增加 pywebview 检测（跳过 WS），新增 `window.showDeviceList()` 暴露给 Python 调用
- `static/style.css` — 修改：新增 device-picker 弹窗样式
- `build.bat` — **新建** PyInstaller 打包脚本
- `requirements.txt` — 修改：追加 pywebview, pyinstaller

## 原因

将 ModeCalc Web 应用封装为独立 Windows exe，双击运行。详见 ADR 0004。

## 架构说明

- 桌面模式：`app.py`（pywebview + WebView2）→ JS bridge 直接传数据
- Web 调试模式：`server.py`（aiohttp + WebSocket）仍保留可用
- 前端代码复用，`window.updateUI()` 为统一入口

## 影响

- 入口文件增加，`server.py` 不变
- exe 大小 18 MB（目标 < 30 MB）
- 离线运行需要 WebView2 Runtime（Win10+ 自带 Edge WebView2）
- VexFlow CDN 字体离线时降级（空谱表 + console 警告）
