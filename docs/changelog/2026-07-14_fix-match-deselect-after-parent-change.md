# 2026-07-14 修复切换母音阶后 match 无法取消选中

## 变更
- `static/app.js`
  - `sendAnalysisMode()`: 删除 `selectedMatch = null`（不再主动清除选中态，允许跨母音阶保留）
  - `radio change handler`: 仅在切到 Chord 模式时清除 `selectedMatch`
  - `updateUI()`: 新增验证逻辑——若 `selectedMatch` 不在新返回的 matches 中则自动清除

## 原因
原代码在 `sendAnalysisMode()` 中将 `selectedMatch = null`，但无音符时后端返回相同数据，`updateUI()` 去重拦截导致 DOM 残留假选中态。用户期望选中态跨越母音阶切换保持不变。

## 影响
- Mode 分析模式下 match 选中交互
- 键盘高亮状态
