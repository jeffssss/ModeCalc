# Web 架构（Python 后端 + 浏览器前端）

选型：aiohttp + WebSocket 作为后端，Vanilla JS + VexFlow 5 作为前端，用户通过浏览器打开。

**为何不用 Qt (PySide6) 桌面应用？** 五线谱渲染是核心复杂度。Qt 路线需要自绘或集成 music21/abjad，实时更新性能与维护成本远高于复用成熟 JS 库。VexFlow 5 的 Grand Staff、变音记号、符干方向、谱号等功能开箱即用。

**为何不用 Electron？** Phase 1-2 不需要桌面打包。浏览器直接打开，零安装门槛。后续需要分发时再加壳。

**被认为但放弃的方案：**
- PySide6 + music21 渲染：music21 偏向静态分析，实时重绘性能不明，且与 Qt 集成需额外适配
- 纯终端 (CLI)：无法显示五线谱和钢琴键盘，不能满足需求
