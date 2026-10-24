# 2026-07-19 指板八度精确映射

## 变更

- `static/fretboard.js`
  - 新增常量 `OPEN_MIDI` / `FRET_COUNT`
  - 新增 `highlightFretboardFromMidi(midiNumbers)` — 按 MIDI number 精确映射到 (弦, 品) 位置
  - 去重机制：同一 (弦, 品) 只画一次
- `static/app.js`
  - `updateKeyboardHighlight()` 指板部分改用 `highlightFretboardFromMidi` 替代按音名泛化匹配

## 原因

`drawNotes(['C','E','G'])` 只匹配 pitch class，C2/C3/C4 全亮。用户要求：弹 C4 只显示 C4 的正确八度位置。

## 影响

- 音符在指板上只出现在正确八度的位置（通过 MIDI number - 开放弦MIDI = 品数计算）
- 等音不同弦仍可显示（同一 MIDI 数在不同弦上找到不同品）
- 超出 15 品范围的音符自动过滤
- scale 选中时，音阶音也在正确八度上叠加显示
