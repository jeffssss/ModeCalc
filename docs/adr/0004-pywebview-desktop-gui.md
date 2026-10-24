# ADR 0004: pywebview 桌面 GUI 包装

## 背景

ModeCalc 当前是 Web 应用（Python aiohttp + 浏览器前端）。需要分发为独立桌面应用，用户双击 exe 运行，无需安装 Python 或浏览器。

## 决策

使用 **pywebview** 将现有 Web 前端嵌入原生桌面窗口。

## 替代方案评估

### 方案 A: 保持 Web 服务器模式（不做 GUI）
- 优点：零额外工作
- 缺点：用户需手动打开浏览器、输入 URL；无法作为桌面应用分发

### 方案 B: Electron
- 优点：原生 Web 渲染，跨平台
- 缺点：~150 MB 打包体积；需维护 Node.js 进程；MidiHandler 仍需独立 Python 进程或绑定

### 方案 C: Python GUI 全重写（PySide/Qt）
- 优点：纯原生，启动快
- 缺点：VexFlow 不可用——五线谱渲染需换 music21/LilyPond，工程量巨大；SVG 键盘需重写

### 方案 D: pywebview（选中）
- 优点：前端代码（VexFlow + SVG 键盘 + app.js + staff.js）零改动；系统自带 WebView2（Windows 10+/Edge），零依赖；打包 ~15 MB
- 缺点：本质仍是 Web 引擎；离线需处理 CDN 字体加载

## 影响

- 入口从 `server.py` 变为新的 `app.py`（pywebview 窗口 + MIDI 线程 + WS 删去）
- WebSocket 层移除：pywebview 通过 JS bridge 直接通信，无需网络层
- MIDI 自动连接所有物理端口（免设备选择）
- `static/index.html` 的 VexFlow CDN 引用改为本地 `static/vendor/vexflow-core.js`
- 窗口尺寸 1000×480（适配五线谱渲染高度）
- 打包使用 PyInstaller，输出 18 MB exe

## 日期

2026-07-10
