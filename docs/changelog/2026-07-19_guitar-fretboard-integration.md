# 2026-07-19 吉他指板集成

## 变更

- `static/vendor/traste.min.js` — 新增，traste 吉他指板 SVG 渲染库 v1.0.0
- `static/fretboard.js` — 新增，指板创建/高亮封装（对标 keyboard.js 模式）
- `static/index.html`
  - 底部改为 `<div id="bottom-row">` 水平双列布局（键盘 + 指板并列）
  - 新增 `<script>` 引入 traste + fretboard.js
  - 初始化调用 `createFretboard('fretboard')`
- `static/style.css`
  - 新增 `#bottom-row` flex 布局（height: 120px, gap: 8px）
  - `#keyboard` 改为 `flex: 1 1 0`
  - 新增 `#fretboard` 样式 + SVG 响应式设置
- `static/app.js`
  - `updateKeyboardHighlight()` 内新增指板高亮逻辑，合并 active + scale 音名

## 原因

用户需要在吉他指板上显示 MIDI 输入的音符位置，增强调式/和弦学习的直观性。

## 影响

- 底部区域高度从 108px（键盘独占）变为 120px（键盘+指板并列）
- middle-row 减少约 12px 空间，不影响核心功能
- 键盘宽度减半（1172px → ~580px），白键宽度从 ~22.5px 缩至 ~11px
- 指板展示标准调弦 6弦×15品，使用 traste 默认音高颜色编码
- 选中调式后指板同步高亮音阶音（与键盘行为一致）
