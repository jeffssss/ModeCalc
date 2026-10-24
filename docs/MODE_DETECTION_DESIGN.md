# ModeCalc — 调式识别扩展设计文档

## 1. 目的

ModeCalc 名称中的 "Mode" 指音乐理论中的**调式（Mode）**。当前 V1 仅支持和弦识别（3-4 音匹配 15 种三/七和弦）。V2 需扩展为双透镜架构：用户可在"和弦视角"和"调式视角"之间切换，同一组音符从两个维度得出不同结论。

**典型场景：**

| 输入音符 | 和弦视角 | 调式视角 |
|----------|----------|----------|
| C E G | C Major | C Ionian, G Ionian subset, ... |
| E F# A C D G | unknown (≥5 PC) | E Dorian, G Ionian, D Mixolydian, ... |
| C Eb G Bb | C-7 | C Dorian, Bb Ionian, ... |

## 2. 调研结果

### 2.1 调式理论背景

**教会调式（7 Church Modes）：** 即 Ionian 母音阶（Major scale: 1 2 3 4 5 6 7）的 7 个转位：

| 转位 | 调式名 | 特征 |
|------|--------|------|
| 0 | Ionian | Major scale |
| 1 | Dorian | ♮6 |
| 2 | Phrygian | ♭2 |
| 3 | Lydian | ♯4 |
| 4 | Mixolydian | ♭7 |
| 5 | Aeolian | Natural minor |
| 6 | Locrian | ♭5 |

**旋律小调调式（7 Melodic Minor Modes）：** 母音阶 = Melodic Minor (1 2 ♭3 4 5 6 7)，jazz 即兴核心材料。

| 转位 | 调式名 | 典型用途 |
|------|--------|----------|
| 0 | Melodic Minor | 旋律小调 |
| 1 | Dorian ♭2 (Phrygian ♮6) | Phrygian 替代 |
| 2 | Lydian Augmented | ♯5 和弦上使用 |
| 3 | Lydian Dominant | 属七♯11 和弦 |
| 4 | Mixolydian ♭6 (Hindu) | 属七♭13 |
| 5 | Locrian ♮2 (Half-diminished) | ø 和弦 |
| 6 | Altered (Super Locrian) | 属七alt 和弦 |

**和声小调调式（7 Harmonic Minor Modes）：**

| 转位 | 调式名 | 典型用途 |
|------|--------|----------|
| 0 | Harmonic Minor | 和声小调 |
| 1 | Locrian ♮6 | ø 和弦 |
| 2 | Ionian ♯5 | Maj7♯5 |
| 3 | Dorian ♯4 (Ukrainian Dorian) | -7♯11 |
| 4 | Phrygian Dominant | 属七♭9♭13 |
| 5 | Lydian ♯2 | Maj7♯9 |
| 6 | Super Locrian ♭♭7 | Dim7 替代 |

**总计 21 个基础调式（V2 Phase 1）。**

### 2.2 相关开源项目调研

| 仓库 | 核心贡献 | 适用性 |
|------|----------|--------|
| [musicpy](https://github.com/Rainbow-Dreamer/musicpy) | `detect_scale()`：遍历音阶→计算匹配率→过滤阈值→排序。支持大小调+教会调式+自定义音阶。中文文档 | 算法模式直接借鉴 |
| [musy](https://github.com/CarloLepelaars/musy) | 轻量 Scale/Chord 对象模型，Dorian/Phrygian/Lydian 等内置 | 数据结构参考 |
| [music21](http://github.com/cuthbertLab/music21) | 学术级音乐理论库，全调式覆盖 | 太重，不引入 |
| [pcsets](https://github.com/Perlence/pcsets) | Pitch Class Set 理论（Forte 编号） | 无调性分析备用 |

### 2.3 核心算法（借鉴 musicpy 的 `detect_scale`）

```
输入: 一组 MIDI note numbers + 用户勾选的母音阶列表
输出: 完全匹配的调式列表

算法:
1. 提取 pitch class set = {n % 12 for n in notes}
2. bass_pc = min(notes) % 12  (最低音作为调中心)
3. for 每个用户勾选的母音阶:
     for 转位 0..6:
       从 bass_pc 出发，按母音阶的半音间隔构建音阶 pitch class set
       if 输入 PC set ⊆ 音阶 PC set:
         记录: {调式名, tonic, 母音阶}
4. 返回所有匹配
```

复杂度：3 母音阶 × 7 转位 = 21 次匹配，O(1) 完成。实时 MIDI 输入无性能压力。

**为什么要求 bass = tonic？** 用户明确要求"最低音作为调中心音"。这与和弦识别逻辑一致（根音 vs 低音的区分）。

## 3. 架构设计

### 3.1 双透镜架构

```
MIDI 输入 → get_state() → recognize(notes, mode, active_parents)
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            mode == 'chord'                  mode == 'mode'
            _match_chord()                  mode_engine.detect_modes()
            返回和弦名                       返回调式列表
```

### 3.2 新增模块：`mode_engine.py`

独立的纯函数模块，无 I/O，无外部依赖。与 `chord_engine.py` 并列。

**数据定义：**

```python
PITCH_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

# 母音阶：半音间隔序列
PARENT_SCALES = {
    "Ionian":         [2, 2, 1, 2, 2, 2, 1],
    "Melodic Minor":  [2, 1, 2, 2, 2, 2, 1],
    "Harmonic Minor": [2, 1, 2, 2, 1, 3, 1],
}

# 每个母音阶的 7 个转位名称
MODE_NAMES = {
    "Ionian": [
        "Ionian", "Dorian", "Phrygian", "Lydian",
        "Mixolydian", "Aeolian", "Locrian"
    ],
    "Melodic Minor": [
        "Melodic Minor", "Dorian ♭2", "Lydian Augmented",
        "Lydian Dominant", "Mixolydian ♭6", "Locrian ♮2",
        "Altered"
    ],
    "Harmonic Minor": [
        "Harmonic Minor", "Locrian ♮6", "Ionian ♯5",
        "Dorian ♯4", "Phrygian Dominant", "Lydian ♯2",
        "Super Locrian ♭♭7"
    ],
}
```

**公开函数：**

```python
def detect_modes(
    notes: set[int],
    active_parents: set[str] | None = None,
) -> list[dict]:
    """
    参数:
      notes: MIDI note numbers (非空)
      active_parents: 用户勾选的母音阶，None = 全部启用
    
    返回: 匹配的调式列表（可能为空），每项:
      {
        "name": "E Dorian",
        "tonic": "E",
        "parent": "Ionian",
      }
    
    匹配条件:
      1. 所有输入 pitch class ⊆ 调式 pitch class set
      2. min(notes) % 12 == tonic pitch class
    """
```

### 3.3 修改 `chord_engine.py`

`recognize()` 保持纯和弦识别。新增 `analyze()` 双透镜入口：

```python
def analyze(
    notes: set[int],
    analysis_mode: str = "chord",
    active_parents: set[str] | None = None,
) -> dict:
```

- 始终调用 `recognize(notes)` → `result_type` / `result` 为和弦透镜
- `analysis_mode == 'mode'` 且有音符时，额外填充 `mode_matches`
- 无音符时 `mode_matches = []`

### 3.4 前端 UI 设计

**Chord 模式（默认）：** 侧栏空白或折叠，与原版行为一致。

**Mode 模式：** 侧栏展开，显示：

```
┌─────────────────────────┐
│ ◉ Chord  ○ Mode        │  ← 单选框切换
├─────────────────────────┤
│ ☑ Ionian (7 modes)     │  ← 母音阶复选框
│ ☑ Melodic Minor (7)    │     仅在 Mode 模式可见
│ ☑ Harmonic Minor (7)   │
├─────────────────────────┤
│ Matches:                │  ← 匹配结果显示
│ E Dorian                │
│ G Ionian                │
└─────────────────────────┘
```

**交互流程：**
```
用户切换 Mode → JS 调用 pywebview.api.set_analysis_mode('mode', parents)
→ Python 更新状态 → 下次 get_state() 用 mode='mode' 调 recognize()
→ 返回和弦结果 + mode_matches → updateUI() 和弦名区始终显示和弦，侧栏 Matches 显示调式
```

### 3.5 双透镜显示策略

**`#chord-name`（顶部）**：无论 Chord / Mode 分析模式，始终显示和弦透镜结果（C、C-7、N/A 等）。

**`#mode-matches-list`（侧栏 Matches）**：
- 仅当分析模式为 Mode **且** 有活跃音符时显示调式匹配列表
- 无音符时清空，不显示任何内容
- 显示格式：`{调中心} {调式名} ({母音阶} #{转位})`，转位为 1–7（如 `E Dorian (Ionian #2)`）
- 例外：Messiaen 条目采用音程命名（最小循环单元，如 `C Messiaen 211`），省略母音阶与转位后缀

## 4. 实现步骤

### Step 1: `mode_engine.py` + 测试

- [x] 新建 `mode_engine.py`
- [x] 实现 `detect_modes(notes, active_parents)`
- [x] 新建 `tests/test_mode_engine.py`
- [ ] 测试 cases：

| 输入 (MIDI) | 勾选 | 预期 |
|-------------|------|------|
| `{64,66,69,71,72,74,76}` (E F# A C D G 从低到高) | Ionian | E Dorian |
| `{60,64,67}` (C E G) | Ionian | C Ionian |
| `{60,62,67}` (C D G) | 全部 | C Ionian, G Mixolydian |
| `{60,63,67}` (C Eb G) | Ionian | (无，Eb 不在任何 C tonic Ionian 转位中? 需要验证) |
| `{60,62,63,65,67,69,70}` (C D Eb F G A Bb) | Ionian+Melodic Minor+Harmonic Minor | 多个匹配 |

### Step 2: `chord_engine.py` 集成

- [x] `recognize()` 加 `mode` 和 `active_parents` 参数
- [x] `mode == 'chord'` 走原逻辑
- [x] `mode == 'mode'` 委托 `mode_engine.detect_modes()`
- [x] 更新已有 tests，确认向后兼容

### Step 3: `app.py` + `server.py` 状态管理

- [x] `Api` 加 `set_analysis_mode(mode, parents)` 方法
- [x] `MidiState` / `State` 加 `_mode` 和 `_active_parents` 字段
- [x] `get_state()` 传入 `mode` + `parents` 给 `recognize()`

### Step 4: 前端 UI（`index.html` + `style.css` + `app.js`）

- [x] `#side-panel` 加 toggle 单选框 + 母音阶复选框 + 匹配结果区域
- [x] 样式：侧栏固定宽度，Mode 面板仅在 mode 模式显示
- [x] `updateUI()` 处理 `result_type: 'mode'`
- [x] toggle/checkbox 事件绑定 → `pywebview.api` / WebSocket

### Step 5: 集成测试

- [ ] Chord 模式：原有和弦功能不受影响
- [ ] Mode 模式：弹 6-7 音 → 显示正确调式
- [ ] 勾选/取消母音阶 → 结果变化
- [ ] 切换回 Chord → 侧栏折叠
- [ ] exe 模式 UI 一致

## 5. 未来扩展（Phase 2+）

- [ ] Jazz 音阶: Whole Tone, Diminished (WH/HW), Pentatonic, Blues, Bebop
- [ ] 自定义音阶（用户输入半音间隔）
- [ ] 非完全匹配模式（阈值可调，显示覆盖度百分比）
- [ ] 调式内和弦自动推导（音阶 → 三和弦 → 七和弦 → 扩展音）
- [ ] 移调（选择调式后，显示该调式所有可用和弦）

## 6. 文件清单

```
ModeCalc/
├── mode_engine.py              ← 新建
├── chord_engine.py             ← 修改（加 mode/parents 参数）
├── app.py                      ← 修改（Api 加 set_analysis_mode）
├── server.py                   ← 修改（State 加 mode/parents）
├── static/
│   ├── index.html              ← 修改（#side-panel 加 UI）
│   ├── style.css               ← 修改（侧栏样式）
│   └── app.js                  ← 修改（mode 结果渲染 + 事件绑定）
└── tests/
    ├── test_chord_engine.py    ← 修改（加 mode 参数测试）
    └── test_mode_engine.py     ← 新建
```
