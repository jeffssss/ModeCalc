# ModeCalc GUI 打包 — 执行计划

## 进度

| 阶段 | 状态 |
|------|------|
| 阶段 | 状态 |
|------|------|
| 文档 & 设计 | ✅ 完成 |
| UI 打磨 (Step 9) | ✅ 完成 |
| All MIDI inputs | ✅ 完成（免设备选择） |
| app.py 开发 | ✅ 完成 |
| JS Bridge 适配 | ✅ 完成 |
| 字体处理 | ✅ 完成（本地 vexflow-core.js + woff2） |
| MIDI 管道重构 | ✅ 完成（去重移至 JS，固定 30ms 推送） |
| PyInstaller 打包 | ✅ 完成（Python 3.12） |
| 集成测试 | ✅ 完成 |

## 目标

将 ModeCalc Web 应用包装为 Windows 桌面 exe，双击运行，无需浏览器/命令行。

## 当前 UI 参数

| 参数 | 值 |
|------|-----|
| 窗口尺寸 | **1000×480** |
| 背景 | 纯白 #ffffff |
| 字体 | Quicksand Medium（和弦名） |
| 五线谱 | 300×280px, x=50, 无 brace/小节线, 音符 xShift=100 |
| 键盘 | 88 键, 90px 高, 全宽, SVG 内黑框 |
| MIDI 输入 | **自动打开所有物理端口 (handler.open(None))** |

## 前置条件

- [x] chord_engine.py — 和弦识别（15 模板，原位优先）
- [x] midi_handler.py — MIDI 采集（回调+Queue 双线程）
- [x] static/ — 前端完整（VexFlow 大谱表 + SVG 键盘 + 英文音程）
- [ ] pywebview 安装
- [ ] PyInstaller 安装

## 执行步骤

### Step 1: 环境准备

- [ ] `pip install pywebview pyinstaller`
- [ ] 更新 `requirements.txt`：追加 `pywebview`, `pyinstaller`
- [ ] 验证：`python -c "import webview; print(webview.__version__)"`

### Step 2: app.py — pywebview 主入口

新建 `app.py`，替代 `server.py` 作为桌面启动入口。`server.py` 保留不动（Web 调试模式仍可用）。

**核心流程：**

```
┌─ pywebview.create_window() ─────┐
│  1000×480, 纯白背景              │
│  加载 static/index.html          │
└──────────────┬───────────────────┘
               ▼
┌─ _startup() ────────────────────┐
│  handler.open(None)              │
│  → 自动打开所有物理 MIDI 端口     │
│  无设备则静默跳过                 │
└──────────────┬───────────────────┘
               ▼
┌─ 启动 MIDI 轮询线程 ────────────┐
│  5ms poll → recognize → 30ms    │
│  debounce → evaluate_js         │
└──────────────┬───────────────────┘
               ▼
┌─ UI 更新循环 ───────────────────┐
│  window.evaluate_js(updateUI)    │
│  → chord_name, keyboard, staff   │
└──────────────┬───────────────────┘
               ▼
┌─ 窗口关闭 → finally ───────────┐
│  handler.close() → 进程退出     │
└──────────────────────────────────┘
```

**类与函数：**

| 符号 | 职责 |
|------|------|
| `class AppState` | 持有 midi_handler, active_notes |
| `class Api` | JS bridge，暴露 `quit_app()` 给前端 |
| `midi_loop()` | 后台线程，5ms 轮询 MIDI → recognize → 30ms debounce → `evaluate_js(updateUI)` |
| `_startup()` | 窗口就绪回调：自动 `handler.open(None)` 所有物理端口，启动 midi_loop 线程 |
| `main()` | 创建窗口 → `webview.start()` |

**JS Bridge 接口定义：**

```
Python → JS:
  window.updateUI(data)              # 推和弦数据（复用现有 app.js 逻辑）

JS → Python:
  pywebview.api.quit_app()          # 退出
```

### Step 3: static/index.html — 设备选择弹窗（已废弃）

**实际实现**：免设备选择，`_startup()` 自动调用 `handler.open(None)` 打开所有物理 MIDI 端口。
无端口则静默跳过。前端无需设备选择器，`window.pywebview` 检测仅用于跳过 WebSocket 连接。

### Step 4: static/app.js — 适配 JS Bridge

当前 `app.js` 通过 WebSocket `ws://${location.host}/ws` 接收数据。需改为 JS Bridge 模式。

**方案：** 添加 `window.updateUI` 作为统一入口，pywebview 直接调用它（绕过 WebSocket）。

现有 `updateUI(data)` 函数已在全局作用域（通过 `window.updateUI = updateUI` 暴露），参数格式兼容 WebSocket 消息体。无需修改——只要 Python 推过来的 data 结构不变即可。

**需移除/条件化：**
- WebSocket 连接代码 → 用 `if (window.pywebview)` 判断环境
- 存在 `pywebview` → 跳过 WS 连接，等待 `window.updateUI()` 被 Python 调用
- 不存在 `pywebview` → 走原 WS 路径（浏览器调试）

### Step 5: 字体处理

VexFlow 通过 CDN 加载 Bravura/Academico 字体：
```html
<script src="https://cdn.jsdelivr.net/npm/vexflow@5.0.0/build/cjs/vexflow-core.js"></script>
```

**问题：** Web 模式下浏览器可正常访问 CDN，所以五线谱显示正常；打包为 exe 后，pywebview/WebView2 通过 `file://` 加载本地页面，外部 CDN 脚本或字体更容易被网络、离线环境或 `FontFace` 加载策略阻断。结果是钢琴键盘仍能显示（纯 SVG/JS），但依赖 VexFlow 音乐字体的五线谱不渲染。

**方案：** 将 vexflow-core.js 下载到 `static/vendor/vexflow-core.js`，`<script>` 改为本地引用。
下载命令：
```
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/vexflow@5.0.0/build/cjs/vexflow-core.js" -OutFile "static/vendor/vexflow-core.js"
```

同时需要把 VexFlow 使用的字体也本地化。当前 `static/staff.js` 已设置：
```js
VexFlow.Font.HOST_URL = 'vendor/fonts/';
```

因此 exe 必须包含以下文件，否则 `VexFlow.loadFonts('Bravura', 'Academico')` 会找不到字体，五线谱可能空白：
```
static/vendor/fonts/bravura/bravura.woff2
static/vendor/fonts/academico/academico.woff2
```

下载命令：
```powershell
New-Item -ItemType Directory -Force static/vendor/fonts/bravura, static/vendor/fonts/academico
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/@vexflow-fonts/bravura/bravura.woff2" -OutFile "static/vendor/fonts/bravura/bravura.woff2"
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/@vexflow-fonts/academico/academico.woff2" -OutFile "static/vendor/fonts/academico/academico.woff2"
```

PyInstaller 使用 `--add-data "static;static"` 时会把 `static/` 整体打入 exe；确认字体文件存在后重新运行 `build.bat`。

**故障记录：exe 五线谱空白**

- 症状：Web 运行时五线谱正常，打包 exe 后钢琴键盘正常显示，但五线谱区域空白。
- 排查证据：`static/index.html` 已改为本地 `vendor/vexflow-core.js`；`static/staff.js` 又将 `VexFlow.Font.HOST_URL` 改为 `vendor/fonts/`；但项目中没有 `static/vendor/fonts/` 和 `.woff2` 字体文件。
- 根因：只本地化了 VexFlow JS，没有本地化 Bravura/Academico 字体；exe 内 `file://` 页面无法从预期路径加载音乐字体，导致 VexFlow 字体初始化失败或渲染失败。
- 修复：补齐 `bravura.woff2`、`academico.woff2` 到 `static/vendor/fonts/`，再重新打包。
- 验证：无 MIDI 设备时启动 exe 应显示空谱表；有 MIDI 输入时，和弦名、键盘高亮、五线谱三者同步更新。

### 下一步修改入口：初始化空白五线谱

目标：应用启动后立即显示一个空白大谱表；后续 MIDI 输入只更新这个谱表上的音符。

当前问题：
- 浏览器模式：初始化没有五线谱，首次输入音符后出现，之后不消失。
- exe 模式：任何条件下五线谱都不出现。
- 键盘能初始化显示，是因为 `index.html` 主动调用了 `createKeyboard('keyboard')`。
- 五线谱没有初始化显示，是因为 `renderStaff()` 只在 `updateUI(data)` 收到 MIDI 数据后才被调用。

修改点 1：调整脚本加载顺序

文件：`static/index.html`

当前顺序：
```
vexflow-core.js → app.js → keyboard.js → staff.js → createKeyboard()
```
建议改为先加载渲染模块，再加载主控逻辑：
```
vexflow-core.js → keyboard.js → staff.js → app.js → createKeyboard() + renderStaff([])
```
原因：app.js 可能在 staff.js 定义 `renderStaff` 之前收到 pywebview 推送（字体加载完成后补画 pending 数据），导致第一次更新被跳过。

修改点 2：staff.js 启动时自动绘制空谱表

文件：`static/staff.js`

在 `renderStaff` 定义完成之后，主动调用一次：
```js
window.renderStaff([]);
```
当前 `renderStaff()` 已有字体未就绪保护（存入 `_pendingStaffData`，字体加载完成后补画），
所以启动时调用 `renderStaff([])` 是安全的。字体加载完成后自动补画 pending 的空谱表。

修改点 3：确认字体文件

文件：
- `static/vendor/fonts/bravura/bravura.woff2`
- `static/vendor/fonts/academico/academico.woff2`

当前使用 CSS `@font-face`（`static/style.css`）+ `document.fonts.load()`（`static/staff.js`），
不再使用 `VexFlow.Font.HOST_URL`。确认字体文件存在且路径正确。

修改后验证：
1. 启动空 MIDI → 空白五线谱可见（谱线 + 谱号）
2. 按任意 MIDI 键 → 音符显示在已有谱表上
3. 松键 → 谱表保留，音符清空
4. exe 和浏览器行为一致

### Step 6: PyInstaller 打包

**命令：**
```cmd
pyinstaller ^
  --name "Mode Calculation" ^
  --icon static/icon.ico ^
  --noconsole ^
  --onefile ^
  --add-data "static;static" ^
  --hidden-import webview.platforms.edgechromium ^
  app.py
```

**build.bat：**
```bat
@echo off
pyinstaller --name "Mode Calculation" --icon static/icon.ico --noconsole --onefile --add-data "static;static" --hidden-import webview.platforms.edgechromium app.py
echo Done. Output: dist\Mode Calculation.exe
pause
```

**验证：**
- [x] `dist/ModeCalc.exe` 双击启动，无控制台窗口
- [x] 自动连接 MIDI（无选择弹窗）
- [x] 五线谱字体正常加载（本地 vexflow-core.js）
- [x] 键盘 SVG 正常渲染
- [x] exe 大小 18 MB（< 30 MB）

### Step 7: 集成测试

- [x] 无 MIDI 设备 → 启动后空谱表正常显示
- [x] 有 MIDI 设备 → 自动连接 → 按键 → 三区同步更新
- [x] 松键 → 所有音符从谱表消失
- [x] 柱式和弦 → 全部音符正确显示，不丢音
- [x] 拔掉设备 → 谱表清空，无崩溃
- [x] 窗口关闭 → 进程退出，任务管理器无残留
- [x] 双击 exe 冷启动时间 < 3 秒

## 变更文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app.py` | 重写 | pywebview 主入口。`MidiState.get_state()` 无状态拉取，固定 30ms 推送。文件日志 |
| `midi_handler.py` | 修改 | `poll()` 移除 `changed` 标志，永远返回当前 `set[int]` |
| `server.py` | 修改 | `poll_and_recognize()` → `get_state()`，去掉 `_previous` |
| `static/index.html` | 修改 | 脚本顺序：vexflow → keyboard → staff → app。vexflow CDN → 本地 |
| `static/app.js` | 修改 | `updateUI` 加 `JSON.stringify` 去重。`file://` 协议检测。调试栏 |
| `static/staff.js` | 修改 | CSS @font-face + `document.fonts.load()`。启动时 `renderStaff([])` |
| `static/style.css` | 修改 | @font-face Bravura/Academico。调试栏样式 |
| `static/vendor/vexflow-core.js` | **新建** | VexFlow 5.0.0 CJS 包，本地化 |
| `static/vendor/fonts/` | **新建** | Bravura + Academico `.woff2` 字体 |
| `static/icon.ico` | 已完成 | 钢琴键盘图标 |
| `build.bat` | 修改 | 显式 Python 3.12 pyinstaller。追加 `--hidden-import mido.backends.rtmidi --hidden-import rtmidi` |
| `requirements.txt` | 修改 | `mido` + `python-rtmidi` + `pywebview` + `pyinstaller` |
| `winmidi.py` | 删除 | ctypes 方案不再需要 |
| `docs/GUI_EXECUTION_PLAN.md` | 修改 | 窗口尺寸 410→480。进度追加 MIDI 管道重构。集成测试清单更新 |

## 架构决策记录

| 决策 | 说明 |
|------|------|
| Python 3.12 构建 | python-rtmidi 仅在 3.12 有预编译 wheel。build.bat 显式指定 3.12 pyinstaller |
| 去重放 JS 层 | `JSON.stringify` 比对，避免两层去重耦合导致状态不一致 |
| 固定 30ms 推送 | 不再检查"是否有变化"，每次 midi_loop 迭代都推当前状态 |
| CSS @font-face | 绕过 VexFlow 内部 FontFace API（`file://` 协议下 Chromium 静默阻塞） |
| 文件日志 | `%TEMP%\ModeCalc_debug.log`，调试时查看 MIDI 数据流 |

## 风险

| 风险 | 缓解 |
|------|------|
| WebView2 未安装（Win10 LTSC/旧版） | 启动时检测，提示安装 Edge WebView2 Runtime |
| exe 中缺少 VexFlow 字体导致五线谱空白 | 将 Bravura/Academico `.woff2` 放入 `static/vendor/fonts/`，并随 `static/` 一起打包 |
| VexFlow `factory.Accidental()` CDN 版不存在 | 已有 `typeof` 守卫，无升降号但不崩溃 |
| MIDI 设备热插拔 | 当前只处理启动选择；Phase 2 加侧栏重选 |
