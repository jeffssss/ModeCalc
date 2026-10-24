# 2026-07-19 指板布局修复+品位定位点

## 变更

- `app.py` — 窗口高度 600→720，为指板腾出空间
- `static/index.html`
  - 移除 `#bottom-row` 双列包裹
  - 指板在上、键盘在下，各自独立全宽排列
- `static/style.css`
  - 删除 `#bottom-row` 样式
  - `#fretboard` 高度 135px，flex 居中，overflow hidden
  - `#keyboard` 恢复全宽 + 108px 高度
- `static/fretboard.js`
  - `createFretboard()` 新增 `addFretMarkers()` 在 SVG 中绘制品位圆点
  - 3/5/7/9/15/17 品：单点位于弦 3-4 之间
  - 12 品：双点分别位于弦 2-3 和 4-5 之间
  - 坐标计算与 traste 内部尺寸公式一致

## 原因

-  debug 栏遮挡指板底部 → 垂直排列 + 增高窗口解决
-  键盘被压缩 → 恢复全宽
-  需要真实吉他指板的品位定位感

## 影响

- 窗口从 1200×600 变为 1200×720
- 指板全宽居中（SVG 约 540px，两侧留白）
- 键盘恢复 108px 全宽
- middle-row 高度约 280px，与之前 290px 接近，影响不大
