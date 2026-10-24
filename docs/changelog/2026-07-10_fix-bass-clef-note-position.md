# 2026-07-10 修复大谱表低音谱号音符位置错误

## 变更
- `static/staff.js`
  - 高音谱表 `StaveNote` 显式传 `clef: 'treble'`
  - 低音谱表 `StaveNote` 显式传 `clef: 'bass'`
  - `toVexKey()` 去除死代码 `replace('#', '#')`，小写化即 VexFlow 格式
  - 声部创建提取到 System 组装之前，调用 `VexFlow.Accidental.applyAccidentals()`
  - 代码结构重构：创建声部 → 应用升降号 → 组装 System → draw

## 原因

### Bug 1: 低音谱号音符位置错误
VexFlow 5 `StaveNote` 构造函数的 `clef` 参数默认 `'treble'`，不会从所在 Stave 的 `.addClef()` 自动推断。低音谱表音符未传 `clef: 'bass'`，导致按高音谱号坐标系计算 line 值。

`Tables.keyProperties()` 中：
- treble `lineShift=0` → A3 → line=-1（高音下加一线以下）
- bass `lineShift=6` → A3 → line=5（低音第五线，正确）

line=-1 渲染到低音谱表上映射为下加二线（≈C2），而非应有位置。

### Bug 2: 临时升降号不渲染
VexFlow 5 的 `keyProperties()` 只从 key string（如 `c#/4`）提取 intVal 计算音高，**不会自动创建 Accidental modifier**。必须显式调用 `Accidental.applyAccidentals(voices, keySignature)` 扫描所有 StaveNote，检测 key string 中的 `#`/`b`，匹配调号后添加 Accidental 修饰符。

## 影响
- 大谱表低音谱号区域所有 `<C4` 音符渲染位置
- 所有带升降号 (C#, Eb 等) 的音符渲染
