"""和弦识别核心 - 纯函数模块，无外部依赖"""

from mode_engine import detect_modes

PITCH_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
PITCH_NAMES_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
_SHARP_KEYS = frozenset({"C", "G", "D", "A", "E", "B", "F#", "C#"})

def _accidental_from_name(name: str) -> str | None:
    """从音符名中提取升降号类型"""
    if len(name) == 1:
        return None
    suf = name[1:]
    if suf == '#':
        return 'sharp'
    if suf == 'b':
        return 'flat'
    if suf == 'x' or suf == '##':
        return 'double sharp'
    if suf == 'bb':
        return 'double flat'
    return None

INTERVAL_NAMES = {
    0: "Perfect Unison",
    1: "minor 2nd",
    2: "Major 2nd",
    3: "minor 3rd",
    4: "Major 3rd",
    5: "Perfect 4th",
    6: "Tritone",
    7: "Perfect 5th",
    8: "minor 6th",
    9: "Major 6th",
    10: "minor 7th",
    11: "Major 7th",
}

# 和弦模板库 (~60 种)
# 格式: (sorted_intervals, suffix) — 子集匹配 + 三级排序消歧
CHORD_TEMPLATES = [
    # ── 3.1 三和弦 (6) ─────────────────────────────
    ((0, 4, 7), ""),           # Major
    ((0, 3, 7), "-"),          # Minor
    ((0, 3, 6), "°"),          # Diminished
    ((0, 4, 8), "+"),          # Augmented
    ((0, 2, 7), "sus2"),       # Sus2
    ((0, 5, 7), "sus4"),       # Sus4
    # ── 3.2 七和弦 (11) ─────────────────────────────
    ((0, 4, 7, 11), "△7"),     # Major 7th
    ((0, 4, 7, 10), "7"),      # Dominant 7th
    ((0, 3, 7, 10), "-7"),     # Minor 7th
    ((0, 3, 7, 11), "-△7"),    # Minor Major 7th
    ((0, 3, 6, 10), "ø"),      # Half-dim 7th
    ((0, 3, 6, 9), "°7"),      # Dim 7th
    ((0, 5, 7, 10), "7sus4"),  # Dom 7 sus4
    ((0, 4, 7, 9), "6"),       # Major 6th
    ((0, 3, 7, 9), "-6"),      # Minor 6th
    ((0, 4, 6, 10), "7b5"),    # Dom 7 b5
    ((0, 4, 8, 10), "7#5"),    # Dom 7 #5
    # ── 3.3 九和弦 (13) ─────────────────────────────
    ((0, 2, 4, 7, 10), "9"),        # Dom 9
    ((0, 2, 4, 7, 11), "△9"),       # Major 9
    ((0, 2, 3, 7, 10), "-9"),       # Minor 9
    ((0, 2, 3, 6, 10), "ø9"),       # Half-dim 9
    ((0, 2, 5, 7, 10), "9sus4"),    # Dom 9 sus4
    ((0, 1, 4, 7, 10), "7b9"),      # Dom 7 b9
    ((0, 3, 4, 7, 10), "7#9"),      # Dom 7 #9
    ((0, 4, 6, 7, 10), "7#11"),     # Dom 7 #11
    ((0, 4, 7, 8, 10), "7b13"),     # Dom 7 b13
    ((0, 1, 4, 8, 10), "7#5b9"),    # Dom 7 #5 b9
    ((0, 3, 4, 8, 10), "7#5#9"),    # Dom 7 #5 #9
    ((0, 1, 4, 6, 10), "7b5b9"),    # Dom 7 b5 b9
    ((0, 3, 4, 6, 10), "7b5#9"),    # Dom 7 b5 #9
    # ── 3.4 十一和弦 (3) ─────────────────────────────
    ((0, 2, 4, 5, 7, 10), "11"),        # Dom 11
    ((0, 2, 3, 5, 7, 10), "-11"),       # Minor 11
    ((0, 2, 5, 7, 10), "11sus4"),       # Dom 11 sus4
    # ── 3.5 十三和弦 (5) ─────────────────────────────
    ((0, 2, 4, 5, 7, 9, 10), "13"),        # Dom 13
    ((0, 2, 3, 5, 7, 9, 10), "-13"),       # Minor 13
    ((0, 2, 4, 6, 7, 9, 10), "13#11"),     # Dom 13 #11
    ((0, 1, 4, 5, 7, 9, 10), "13b9"),      # Dom 13 b9
    ((0, 3, 4, 5, 7, 9, 10), "13#9"),      # Dom 13 #9
    # ── 3.6 Add 和弦 (4) ─────────────────────────────
    ((0, 2, 4, 7), "add9"),        # Add 9
    ((0, 2, 3, 7), "-add9"),       # Min add 9
    ((0, 4, 5, 7), "add11"),       # Add 11
    ((0, 2, 4, 7, 9), "69"),       # 6/9
    # ── 3.7 扩展 Altered (13) ────────────────────────
    ((0, 1, 4, 6, 7, 10), "7b9#11"),     # Dom 7 b9 #11
    ((0, 3, 4, 6, 7, 10), "7#9#11"),     # Dom 7 #9 #11
    ((0, 1, 4, 7, 8, 10), "7b9b13"),     # Dom 7 b9 b13
    ((0, 3, 4, 7, 8, 10), "7#9b13"),     # Dom 7 #9 b13
    ((0, 4, 8, 11), "△7#5"),             # Maj 7 #5
    ((0, 4, 6, 11), "△7b5"),             # Maj 7 b5
    ((0, 2, 3, 6, 7, 10), "-9#11"),      # Min 9 #11
    ((0, 2, 3, 7, 11), "-△9"),           # Min Maj 9
    ((0, 1, 3, 4, 7, 10), "7b9#9"),      # Dom 7 b9 #9
    ((0, 2, 4, 7, 8, 10), "9b13"),       # Dom 9 b13
    ((0, 2, 4, 6, 7, 10), "9#11"),       # Dom 9 #11
    ((0, 2, 4, 6, 7, 11), "△7#11"),      # Maj 7 #11
    ((0, 1, 5, 7, 10), "7sus4b9"),       # Dom 7 sus4 b9
    # ── 3.8 特殊和弦 (5) ─────────────────────────────
    ((0, 3, 6, 11), "°△7"),              # Dim Maj 7
    ((0, 4, 8, 11), "+△7"),              # Aug Maj 7
    ((0, 3, 5, 7, 10), "-11"),           # Min 11 (voicing omit 9)
    ((0, 2, 4, 5, 7), "add9add11"),      # Add 9 add 11
]


def _names_for_key(key_sig: str) -> list[str]:
    """根据调号返回音名数组（升号调用 # 名，降号调用 b 名）"""
    return PITCH_NAMES if key_sig in _SHARP_KEYS else PITCH_NAMES_FLAT


def note_info(midi: int, key_sig: str = "C") -> dict:
    """MIDI 音符 → {midi, name, octave, accidental}"""
    pc = midi % 12
    octave = (midi // 12) - 1
    names = _names_for_key(key_sig)
    name = names[pc]
    return {
        "midi": midi,
        "name": name,
        "octave": octave,
        "accidental": _accidental_from_name(name),
    }


def recognize(notes: set[int], key_sig: str = "C") -> dict:
    """
    识别和弦/音程。

    输入: MIDI note numbers 的集合
    返回: {result_type: str, result: dict|None}
    """
    if not notes:
        return {"result_type": "none", "result": None}

    names = _names_for_key(key_sig)

    # 去重到 pitch class
    pcs = sorted({n % 12 for n in notes})
    pcs_set = set(pcs)

    if len(pcs) == 1:
        pc = pcs[0]
        return {
            "result_type": "single",
            "result": {"name": names[pc]},
        }

    if len(pcs) == 2:
        lower_midi = min(notes)
        upper_midi = max(notes)
        half = (upper_midi - lower_midi) % 12
        interval_name = INTERVAL_NAMES.get(half, f"{half} semitones")
        lower = note_info(lower_midi, key_sig)
        return {
            "result_type": "interval",
            "result": {
                "name": f"{lower['name']} {interval_name}",
                "half_steps": half,
            },
        }

    # 3+ pitch class → 模板匹配 + 三级排序消歧
    result = _match_all(notes, pcs_set, key_sig)
    if result:
        return result

    # 无匹配 → 最低音 + n.c.
    bass_note = note_info(min(notes), key_sig)
    return {"result_type": "unknown", "result": {"name": f"{bass_note['name']} n.c."}}


def analyze(
    notes: set[int],
    analysis_mode: str = "chord",
    active_parents: set[str] | None = None,
    key_sig: str = "C",
    pinned_pcs: set[int] | frozenset[int] | None = None,
    pinned_tonic: int | None = None,
) -> dict:
    """双透镜入口：和弦识别 + 调式检测。

    始终调用 recognize(notes) 作为和弦透镜；
    analysis_mode='mode' 且有音符时，额外填充 mode_matches。
    固定音阶（pinned_pcs / pinned_tonic）后，若按下音含音阶外音，
    再以该调中心为锚点找包含全部按下音的调式，填入 derived_matches。
    """
    chord_result = recognize(notes, key_sig)
    result = {
        "result_type": chord_result["result_type"],
        "result": chord_result["result"],
        "analysis_mode": analysis_mode,
        "mode_matches": [],
        "derived_matches": [],
        "key_sig": key_sig,
    }

    if analysis_mode == "mode" and notes:
        result["mode_matches"] = detect_modes(notes, active_parents, key_sig)
        result["derived_matches"] = _derived_matches(
            notes, active_parents, key_sig, pinned_pcs, pinned_tonic
        )

    return result


def _derived_matches(
    notes: set[int],
    active_parents: set[str] | None,
    key_sig: str,
    pinned_pcs: set[int] | frozenset[int] | None,
    pinned_tonic: int | None,
) -> list[dict]:
    """红音触发：以固定音阶的调中心为锚，找包含全部按下音的调式。

    条件：已固定音阶、至少 2 个不同音高、且至少 1 个音在固定音阶外。
    """
    if pinned_tonic is None:
        return []
    input_pcs = {n % 12 for n in notes}
    if len(input_pcs) < 2:
        return []
    pinned = frozenset(pinned_pcs or ())
    if not any(pc not in pinned for pc in input_pcs):
        return []
    derived = detect_modes(notes, active_parents, key_sig, tonic_pc=pinned_tonic)
    return [m for m in derived if frozenset(m["pcs"]) != pinned]


def _match_all(notes: set[int], pcs_set: set[int], key_sig: str = "C") -> dict | None:
    """统一模板匹配 + 三级排序消歧。

    遍历 12 根音 × 60 模板，筛选输入 pcs ⊆ 模板 pcs。
    过滤: 缺失音 >= 现有音 则跳过（防止随机 3 音匹配超大和弦）
    排序: missing ASC → inversion_binary (0=原位) ASC → template_size ASC
    """
    bass_pc = min(notes) % 12
    candidates = []
    n_pcs = len(pcs_set)
    names = _names_for_key(key_sig)

    for root_pc in range(12):
        for intervals, suffix in CHORD_TEMPLATES:
            shifted = {(root_pc + i) % 12 for i in intervals}
            if not pcs_set.issubset(shifted):
                continue

            missing = len(intervals) - n_pcs
            if missing >= n_pcs:   # 缺失 ≥ 现有 → 过于牵强
                continue
            inversion_binary = 0 if bass_pc == root_pc else 1

            # 精准 inversion：bass 在输入间隔序列中的位置
            input_intervals = sorted((pc - root_pc) % 12 for pc in pcs_set)
            bass_interval = (bass_pc - root_pc) % 12
            try:
                inv = input_intervals.index(bass_interval)
            except ValueError:
                inv = 0

            root_name = names[root_pc]
            chord_name = root_name + suffix
            if bass_pc != root_pc:
                chord_name += f"/{names[bass_pc]}"

            candidates.append({
                "result_type": "chord",
                "result": {
                    "name": chord_name,
                    "inversion": inv,
                    "is_incomplete": missing > 0,
                },
                "_sort_key": (missing, inversion_binary, len(intervals)),
            })

    if not candidates:
        return None

    candidates.sort(key=lambda x: x["_sort_key"])
    best = candidates[0]
    return {k: v for k, v in best.items() if not k.startswith("_")}
