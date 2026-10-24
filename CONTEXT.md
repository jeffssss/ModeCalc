# ModeCalc — 领域词汇表

## 核心概念

- **MIDI Note Number**: 0–127 整数，如 60 = C4。MIDI 输入原始表示。
- **Debounce**: 前端重绘间隔 30ms，取最后状态。减少快速琶音时的无效重绘。
- **Pitch Class**: 0–11，MIDI note number mod 12。去掉八度信息的音高级。
- **Enharmonic Spelling（同音异名拼写）**: 同一音高不同音名表示（C# vs Db）。Phase 1 简化处理（优先降号少）；Phase 2 用户自选调号，在该调下选最少临时变音记号的拼写。
- **Chord（和弦）**: 3–4 个不同 pitch class 同时发声，匹配三和弦或七和弦结构。≥5 个音 → 最低音 n.c.。共 15 种模板：
  - 三和弦: Major [0,4,7], Minor [0,3,7], Diminished [0,3,6], Augmented [0,4,8], Sus4 [0,5,7], Sus2 [0,2,7]
  - 七和弦: Major 7th [0,4,7,11], Dominant 7th [0,4,7,10], Minor 7th [0,3,7,10], Minor Major 7th [0,3,7,11], Half-dim 7th [0,3,6,10], Dim 7th [0,3,6,9], Dom7sus4 [0,5,7,10]
- **Interval（音程）**: 恰好 2 个不同 pitch class 同时发声。严格从低音到高音计算。显示格式：低音音名 + 英文音程名（如 "C Perfect 5th"）。
  - 半音数映射: 0→Perfect Unison, 1→minor 2nd, 2→Major 2nd, 3→minor 3rd, 4→Major 3rd, 5→Perfect 4th, 6→Tritone, 7→Perfect 5th, 8→minor 6th, 9→Major 6th, 10→minor 7th, 11→Major 7th
- **Single Note（单音）**: 1 个音。显示音高名。
- **Chord Root（根音）**: 和弦的基础音，三度叠置的最低音。
- **Chord Inversion（转位）**: 根音不在最低声部。第一转位（三音在低音）、第二转位（五音在低音）、第三转位（七音在低音，仅七和弦）。显示格式：根音和弦名/低音（如 C/E）。
- **Chord Naming（和弦命名）**:
  - Major: C | Minor: C- | Dim: C° | Aug: C+ | Sus4: Csus4 | Sus2: Csus2
  - Maj7: C△7 | Dom7: C7 | Min7: C-7 | MinMaj7: C-△7 | Half-dim7: Cø | Dim7: C°7 | Dom7sus4: C7sus4 | Maj7sus4: C△7sus4
- **Chord Matching（和弦匹配策略）**:
  1. 精确匹配：pitch class set 完全等于某和弦模板 → 收集所有候选
  2. 子集匹配：输入是某和弦子集 → 收集所有候选，标记为不完整
  3. 多候选消歧：优先选原位和弦（低音=根音，无 slash），无原位时才选转位
  4. 超集匹配：输入包含某和弦全部音 + 额外音 → 仅容忍八度重复/五音重复，其余 → 最低音 n.c.
- **Key Signature（调号）**: 用户自选的调性上下文，决定默认升降号集合。Phase 2 引入，用于消除同音异名歧义。
- **Grand Staff（大谱表）**: 高音谱号 + 低音谱号两行谱表。以 Middle C (C4, MIDI 60) 为分界：≥C4 → 高音谱表，<C4 → 低音谱表。若一侧无音符，留空谱表。
- **Accidental（临时升降号）**: 五线谱上音符前的 ♯/♭/♮ 记号。VexFlow 5 不自动渲染，需通过 `factory.Accidental()` 手动附加到 StaveNote。
- **Mode（调式）**: 7 音音阶的一种转位。Phase 1 支持 3 母音阶 × 7 转位 = 21 个调式。
- **Parent Scale（母音阶）**: Ionian、Melodic Minor、Harmonic Minor。各母音阶的 7 个转位共享半音间隔模式。
- **Tonic（调中心）**: 调式的根音。当前实现要求最低音 = tonic（bass = tonic）。
- **Analysis Mode（分析模式）**: 双透镜切换 — `chord`（和弦视角）或 `mode`（调式视角）。

## GUI 架构

- **Embedded WebView**: 将 Web 前端嵌入原生桌面窗口的容器控件。Windows 上使用 Edge WebView2（系统自带），渲染 VexFlow + SVG 键盘。
- **Frameless Window**: 无标题栏、无系统边框的自绘窗口。背景纯白，用户无法拖拽标题栏移动（Phase 1 低优先级）。
- **Splash Device Selector**: 启动时弹出的 MIDI 设备选择器。Python 端枚举可用端口 → 注入前端 → 用户点击选择 → JS bridge 回传 Python → 打开端口 → 进入主界面。
- **JS Bridge**: pywebview 提供的 Python ↔ JavaScript 双向通信机制。Python 调用 `window.evaluate_js()` 执行 JS；前端通过 `window.pywebview.api` 调用 Python 暴露的函数。
- **Side Panel**: 主界面右侧预留区域，未来放置调号选择、设备切换等控制组件。
