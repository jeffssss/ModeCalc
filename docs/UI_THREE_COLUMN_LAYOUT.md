# ModeCalc — 三栏 UI 布局设计

## 目标

将 `#side-panel` 拆分为独立的 Matches 栏和 Controls 栏，提升信息层级清晰度。

## 布局（窗口 1000×480）

```
┌──────────────────────────────────────────────────────────┐ y: 12 (body padding)
│  C△7                                                     │ chord-name, h: 3.2rem
├─────────────┬──────────────────┬─────────────────────────┤
│             │                  │  ○ Chord  ● Mode       │ toggle
│   Staff     │    Matches       │  ☑ Ionian              │ checks
│   300px     │    1fr           │  ☑ Melodic Minor        │ 180px
│             │                  │  ☑ Harmonic Minor      │
│             │  E Dorian        │                         │
│             │  G Ionian        │                         │
│             │                  │                         │
├─────────────┴──────────────────┴─────────────────────────┤
│  Sustain ▢                                              │ sustain-bar
├──────────────────────────────────────────────────────────┤
│                    Keyboard (全宽, h: 90px)               │
└──────────────────────────────────────────────────────────┘
```

## 三栏定义

| 栏 | 元素 ID | 宽度 | 内容 |
|----|---------|------|------|
| 左 | `#staff` | 300px (fixed) | VexFlow 五线谱 |
| 中 | `#matches-panel` | 1fr (弹性) | 匹配结果列表（Chord 模式显示和弦备选，Mode 模式显示调式匹配） |
| 右 | `#control-panel` | 180px (fixed) | Chord/Mode toggle + 母音阶复选框 |

## 行为

### Chord 模式
- 右侧 Controls 可见（toggle 在 "Chord"）
- 母音阶复选框隐藏
- 中间 Matches 显示和弦识别备选结果（如有多个匹配）

### Mode 模式
- 右侧 Controls 可见（toggle 在 "Mode"）
- 母音阶复选框显示
- 中间 Matches 显示调式匹配列表

### 两者都
- Matches 为空时显示占位文字或空白
- 单匹配时只显示一行
- 多匹配时列表显示

## HTML 结构变更

```html
<div id="middle-row">
  <div id="staff"></div>
  <div id="matches-panel">
    <div class="panel-title">Matches</div>
    <ul id="matches-list"></ul>
  </div>
  <div id="control-panel">
    <div id="analysis-toggle">…</div>
    <div id="mode-panel" class="hidden">
      <div id="parent-checks">…</div>
    </div>
  </div>
</div>
```

### 移除
- `#side-panel` 容器
- `#mode-matches` 从 control 区移出（matches 现在独立在 `#matches-panel`）

## CSS 变更

```css
#middle-row {
  flex: 1 1 auto;
  display: flex;
  gap: 8px;           /* 新增：三栏间距 */
  min-height: 0;
}

#staff {
  flex: 0 0 300px;    /* 不变 */
}

#matches-panel {
  flex: 1 1 auto;     /* 弹性占满中间 */
  min-width: 100px;
  font-size: 0.85rem;
}

#control-panel {
  flex: 0 0 180px;    /* 固定右侧宽度 */
  font-size: 0.85rem;
}
```

移除旧 `#side-panel` 样式，拆分到 `#matches-panel` 和 `#control-panel`。

## JS 变更 (`app.js`)

- `updateUI()` 中 mode_matches 渲染目标从 `#mode-matches-list` 改为 `#matches-list`
- Chord 模式的备选和弦也渲染到 `#matches-list`
- `#mode-panel.hidden` toggle 逻辑不变，但需确认 class 绑定

## 不涉及变更

- `#chord-name` — 顶部和弦名保持不变
- `#keyboard` — 键盘布局不变
- `#sustain-bar` — 延音踏板指示不变
- `#debug-bar` — 调试栏不变
- `staff.js`, `keyboard.js` — 无需修改
