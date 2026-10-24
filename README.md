# ModeCalc

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![tests](https://github.com/lewihuang/ModeCalc/actions/workflows/tests.yml/badge.svg)](https://github.com/lewihuang/ModeCalc/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](#环境要求)

简体中文 | [English](README.en.md)

ModeCalc 是一款 Windows 桌面端的 MIDI 实时和弦 / 调式识别工具。连接 MIDI 键盘后，它会实时显示当前和弦、匹配的调式、五线谱、88 键钢琴与吉他指板，适合练习、扒带与和声分析。

![ModeCalc 界面](docs/images/modecalc.png)

- [下载](#下载)
- [功能](#功能)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [打包](#打包)
- [测试](#测试)
- [项目结构](#项目结构)
- [架构](#架构)
- [使用提示](#使用提示)
- [常见问题](#常见问题)
- [贡献](#贡献)
- [许可证与第三方](#许可证与第三方)

## 下载

前往 [Releases](https://github.com/lewihuang/ModeCalc/releases) 下载最新的 Windows 包：

- `ModeCalc-v1.0.1-win64.zip`：免安装，解压后运行 `ModeCalc.exe`；
- 单文件 exe，无需安装 Python。

> exe 未做代码签名，Windows SmartScreen 可能提示“已保护你的电脑”。选择“更多信息 → 仍要运行”即可；也可以在 Release 页面核对 SHA256。

## 功能

- **双视角分析**：`Chord`（和弦）与 `Mode`（调式）随时切换，同一组音符给出两个维度的结果。
- **和弦识别**：约 60 个和弦模板，覆盖三和弦、七和弦、九/十一/十三和弦、add、altered 等；支持转位与不完整匹配提示。
- **调式识别**：约 25 个父音阶，分为七声调式、有限移位调式、五声 & Blues、Bebop、世界民族调式；显示调中心、转位与缺音数量。
- **Messiaen 有限移位调式**：以最小循环音程单元命名（如 `Messiaen 211`、`Messiaen 1131`），直观反映对称结构。
- **固定调式**：点击 `Matches` 中的结果即可固定该音阶；固定后，按下的音若在音阶外，会在键盘上以红色 `#FF5768` 标出。
- **派生调式**：固定调式后，若同时按下多个音且包含音阶外音，会自动以固定音阶的调中心为锚，列出包含全部按下音的调式；点击即可切换固定。
- **可视化**：五线谱（VexFlow）、88 键钢琴（SVG）、吉他指板。
- **调号**：15 个调号，影响升降号拼写与五线谱显示。
- **MIDI**：设备选择（含“全部输入”）、延音踏板支持。
- **勾选记忆**：母音阶勾选状态保存在本地，下次启动自动恢复。

## 环境要求

- **Windows 10 / 11**（依赖 WebView2 Runtime，Windows 11 自带）
- **Python 3.12**（仅源码运行与打包需要）
- 一个 MIDI 输入设备（可选；没有设备时界面仍可打开，只是没有输入）

## 快速开始

```powershell
git clone https://github.com/lewihuang/ModeCalc.git
cd ModeCalc

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

启动后通过菜单栏 `MIDI Input` 选择设备，然后在右侧切换 `Chord` / `Mode`。

## 打包

```powershell
pip install -r requirements.txt
build.bat
```

输出为 `dist\ModeCalc.exe`（单文件，自带 `static` 资源）。打包使用 PyInstaller，版本信息在 `version_info.txt` 中维护。

## 测试

```powershell
pytest -q
```

CI 会在每次 push / PR 时于 Windows runner 上运行全部测试（见 `.github/workflows/tests.yml`）。

## 项目结构

```
app.py                pywebview 桌面入口（MIDI 轮询 + 前端桥接）
server.py             aiohttp + WebSocket 浏览器调试入口
chord_engine.py       和弦识别（模板匹配 / 转位 / 不完整匹配）
mode_engine.py        调式注册表与识别（父音阶、转位、sub_scales）
midi_handler.py       MIDI 采集（回调 + 队列，延音踏板逻辑）
settings_store.py     用户设置持久化
static/               前端：HTML / CSS / JS、VexFlow、字体、指板库
tests/                pytest 单元测试
docs/                 设计文档、ADR 与变更记录
.github/              CI、Issue / PR 模板
version_info.txt      Windows 可执行文件版本信息
build.bat             PyInstaller 打包脚本
```

## 架构

```mermaid
flowchart LR
    MIDI[MIDI 键盘] --> MH[midi_handler.py<br/>MIDI 采集]
    MH --> CE[chord_engine.py<br/>和弦识别]
    MH --> ME[mode_engine.py<br/>调式识别]
    CE --> APP[app.py / server.py]
    ME --> APP
    APP --> UI[static/<br/>HTML / CSS / JS]
    UI --> K[88 键钢琴]
    UI --> S[五线谱 VexFlow]
    UI --> F[吉他指板]
```

桌面模式由 `app.py` 通过 pywebview 内嵌 WebView2 运行；调试模式由 `server.py` 提供 HTTP + WebSocket 服务。

## 使用提示

- **固定调式**：在 `Matches` 面板点击任意结果即可固定/取消固定；固定后键盘会高亮该音阶。
- **红色音符**：固定调式后，音阶外的按下音会显示为红色；红色只是提示，不影响和弦识别。
- **派生调式**：红色音符出现时会自动给出候选音阶（`↳` 前缀、红色左边框），点击即切换固定。
- **本地设置**：勾选状态保存在 `%APPDATA%\ModeCalc\settings.json`，删除该文件即可恢复默认。
- **浏览器调试**：`python server.py` 后访问 `http://localhost:8765`（WebSocket 模式，功能与桌面版基本一致）。

## 常见问题

**没有 MIDI 设备能用吗？**
可以打开界面查看用法，但没有输入就不会有识别结果。连接任意 MIDI 键盘后，在 `MIDI Input` 菜单选择设备即可。

**为什么 exe 启动时被 SmartScreen 拦截？**
exe 未做代码签名，Windows 会对新发布的程序给出提示。选择“更多信息 → 仍要运行”，或自行校验 Release 中提供的 SHA256。

**为什么按下的音会变红，Matches 里出现带 `↳` 的项？**
红色表示该音不在你固定的调式内；`↳` 项是以固定调中心为锚、包含当前全部按下音的候选调式，点击即可切换固定。详见上方“使用提示”。

**设置保存在哪里？如何重置？**
`%APPDATA%\ModeCalc\settings.json`。删除该文件后重启即恢复默认。

**支持 macOS / Linux 吗？**
桌面版目前仅支持 Windows（pywebview + WebView2）。`server.py` 的浏览器模式理论上可跨平台运行，但 MIDI 依赖 python-rtmidi，需自行配置。

**为什么 Messiaen 调式叫 `211`、`1131`？**
名称是最小循环音程单元的半音数，例如 `211` = 大二度-小二度-小二度，在八度内重复 3 次。详见 [调式设计文档](docs/MODE_DETECTION_DESIGN.md)。

## 贡献

欢迎提交 Issue 和 Pull Request，开发与测试约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证与第三方

本项目使用 [MIT License](LICENSE)。

第三方组件（VexFlow、traste、Bravura / Academico、Quicksand 等）的版权与许可证见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)，字体许可证全文见 [LICENSES/OFL-1.1.txt](LICENSES/OFL-1.1.txt)。

## 反馈

欢迎在 [GitHub Issues](https://github.com/lewihuang/ModeCalc/issues) 提交问题或建议。
