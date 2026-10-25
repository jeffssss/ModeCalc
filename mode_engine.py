"""调式识别核心 - 纯函数模块，无外部依赖"""

PITCH_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
PITCH_NAMES_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
_SHARP_KEYS = frozenset({"C", "G", "D", "A", "E", "B", "F#", "C#"})

# ── 音阶注册表 ────────────────────────────────────────
# 每条: id → {intervals, mode_names, category, category_priority, default_checked}
SCALE_REGISTRY = {
    # ── 七音阶 (diatonic, category_priority=0) ─────────
    "Ionian": {
        "intervals": [2, 2, 1, 2, 2, 2, 1],
        "mode_names": ["Ionian", "Dorian", "Phrygian", "Lydian",
                       "Mixolydian", "Aeolian", "Locrian"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": True,
    },
    "Melodic Minor": {
        "intervals": [2, 1, 2, 2, 2, 2, 1],
        "mode_names": ["Melodic Minor", "Dorian ♭2", "Lydian Augmented",
                       "Lydian Dominant", "Mixolydian ♭6", "Locrian ♮2",
                       "Altered"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": True,
    },
    "Harmonic Minor": {
        "intervals": [2, 1, 2, 2, 1, 3, 1],
        "mode_names": ["Harmonic Minor", "Locrian ♮6", "Ionian ♯5",
                       "Dorian ♯4", "Phrygian Dominant", "Lydian ♯2",
                       "Super Locrian ♭♭7"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": True,
    },
    "Harmonic Major": {
        "intervals": [2, 2, 1, 2, 1, 3, 1],
        "mode_names": ["Harmonic Major", "Dorian ♭5", "Phrygian ♭4",
                       "Lydian ♭3", "Mixolydian ♭2", "Lydian Augmented ♯2",
                       "Locrian ♭♭7"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": False,
    },
    "Double Harmonic Major": {
        "intervals": [1, 3, 1, 2, 1, 3, 1],
        "mode_names": ["Double Harmonic Major", "Lydian ♯2 ♯6", "Ultraphrygian",
                       "Hungarian Minor", "Oriental", "Ionian Augmented ♯2",
                       "Locrian ♭3 ♭♭7"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": False,
    },
    "Neapolitan Major": {
        "intervals": [1, 2, 2, 2, 2, 2, 1],
        "mode_names": ["Neapolitan Major", "Lydian Augmented ♯6",
                       "Lydian Dominant Augmented", "Major-Locrian",
                       "Locrian ♮2 ♮6", "Altered ♮5 ♮6", "Altered ♮♮3 ♮♮6"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": False,
    },
    "Neapolitan Minor": {
        "intervals": [1, 2, 2, 2, 1, 3, 1],
        "mode_names": ["Neapolitan Minor", "Lydian ♯6",
                       "Mixolydian Augmented", "Hungarian Gypsy",
                       "Locrian ♮6", "Altered ♮♮3", "Altered ♮"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": False,
    },
    "Hungarian Minor": {
        "intervals": [2, 1, 3, 1, 1, 3, 1],
        "mode_names": ["Hungarian Minor", "Oriental", "Ionian Augmented ♯2",
                       "Locrian ♭4 ♭♭7", "Lydian ♯2 ♯6",
                       "Phrygian Dominant ♮6", "Altered ♭♭7"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": False,
    },
    "Hungarian Major": {
        "intervals": [3, 1, 2, 1, 2, 1, 2],
        "mode_names": ["Hungarian Major", "Altered ♮",
                       "Harmonic Minor ♯4", "Superlocrian ♮♮7",
                       "Lydian Augmented ♯3", "Lydian Dominant ♯2",
                       "Locrian ♮6"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": False,
    },
    "Enigmatic": {
        "intervals": [1, 3, 2, 2, 2, 1, 1],
        "mode_names": ["Enigmatic", "Enigmatic ♭2", "Enigmatic ♯2",
                       "Enigmatic ♯3", "Enigmatic ♯4", "Enigmatic ♯5",
                       "Enigmatic ♯6"],
        "category": "diatonic",
        "category_label": "七音阶",
        "category_priority": 0,
        "default_checked": False,
    },
    # ── 对称音阶 (symmetric, category_priority=1) ──────
    "Whole Tone": {
        "intervals": [2, 2, 2, 2, 2, 2],
        "mode_names": ["Whole Tone"],
        "category": "symmetric",
        "category_label": "对称音阶",
        "category_priority": 1,
        "default_checked": False,
    },
    "Diminished WH": {
        "intervals": [2, 1, 2, 1, 2, 1, 2, 1],
        "mode_names": ["Diminished (WH)"],
        "category": "symmetric",
        "category_label": "对称音阶",
        "category_priority": 1,
        "default_checked": False,
    },
    "Diminished HW": {
        "intervals": [1, 2, 1, 2, 1, 2, 1, 2],
        "mode_names": ["Diminished (HW)"],
        "category": "symmetric",
        "category_label": "对称音阶",
        "category_priority": 1,
        "default_checked": False,
    },
    "Augmented": {
        "intervals": [3, 1, 3, 1, 3, 1],
        "mode_names": ["Augmented", "Augmented (inv)"],
        "category": "symmetric",
        "category_label": "有限移位调式",
        "category_priority": 1,
        "default_checked": False,
    },
    "Messiaen": {
        # 名称 = 最小循环音程单元（半音数），在八度内循环到 12
        "intervals": [2, 1, 1, 2, 1, 1, 2, 1, 1],  # 211 (默认, 用于 PARENT_SCALES 兼容)
        "mode_names": ["Messiaen 211", "Messiaen 1131", "Messiaen 141",
                       "Messiaen 2211", "Messiaen 11121"],
        "sub_scales": [
            [2, 1, 1, 2, 1, 1, 2, 1, 1],      # Messiaen 第 3 调式: 211 ×3
            [1, 1, 3, 1, 1, 1, 3, 1],         # Messiaen 第 4 调式: 1131 ×2
            [1, 4, 1, 1, 4, 1],               # Messiaen 第 5 调式: 141 ×2
            [2, 2, 1, 1, 2, 2, 1, 1],         # Messiaen 第 6 调式: 2211 ×2
            [1, 1, 1, 2, 1, 1, 1, 1, 2, 1],   # Messiaen 第 7 调式: 11121 ×2
        ],
        "hide_rotation_suffix": True,
        "category": "symmetric",
        "category_label": "有限移位调式",
        "category_priority": 1,
        "default_checked": False,
    },
    # ── 五声/Blues (pentatonic_blues, category_priority=2) ─
    "Major Pentatonic": {
        "intervals": [2, 2, 3, 2, 3],
        "mode_names": ["Major Pentatonic", "Suspended", "Man Gong",
                       "Ritusen", "Minor Pentatonic"],
        "category": "pentatonic_blues",
        "category_label": "五声&Blues",
        "category_priority": 2,
        "default_checked": False,
    },
    "Blues": {
        "intervals": [3, 2, 1, 1, 3, 2],
        "mode_names": ["Blues"],
        "category": "pentatonic_blues",
        "category_label": "五声&Blues",
        "category_priority": 2,
        "default_checked": False,
    },
    "Major Blues": {
        "intervals": [2, 1, 1, 3, 2, 2],
        "mode_names": ["Major Blues"],
        "category": "pentatonic_blues",
        "category_label": "五声&Blues",
        "category_priority": 2,
        "default_checked": False,
    },
    # ── Bebop (bebop, category_priority=3) ──────────────
    "Bebop Dominant": {
        "intervals": [2, 2, 1, 2, 2, 1, 1, 1],
        "mode_names": ["Bebop Dominant"],
        "category": "bebop",
        "category_label": "Bebop",
        "category_priority": 3,
        "default_checked": False,
    },
    "Bebop Major": {
        "intervals": [2, 2, 1, 2, 1, 1, 2, 1],
        "mode_names": ["Bebop Major"],
        "category": "bebop",
        "category_label": "Bebop",
        "category_priority": 3,
        "default_checked": False,
    },
    "Bebop Dorian": {
        "intervals": [2, 1, 2, 2, 2, 1, 1, 1],
        "mode_names": ["Bebop Dorian"],
        "category": "bebop",
        "category_label": "Bebop",
        "category_priority": 3,
        "default_checked": False,
    },
    # ── 世界民族调式 (world, category_priority=4) ────────
    "Japanese": {
        "intervals": [2, 1, 4, 1, 4],
        "mode_names": ["Hirajoshi", "Kumoijoshi", "Iwato", "In Sen"],
        "sub_scales": [
            [2, 1, 4, 1, 4],
            [2, 1, 4, 2, 3],
            [1, 4, 1, 4, 2],
            [1, 4, 2, 2, 3],
        ],
        "category": "world",
        "category_label": "世界民族调式",
        "category_priority": 4,
        "default_checked": False,
    },
    "Indian": {
        "intervals": [1, 3, 2, 2, 2, 1, 1],
        "mode_names": ["Bhairav", "Purvi", "Todi", "Marwa", "Kafi"],
        "sub_scales": [
            [1, 3, 2, 2, 2, 1, 1],
            [1, 3, 1, 2, 1, 3, 1],
            [1, 2, 3, 1, 1, 3, 1],
            [1, 3, 2, 1, 2, 2, 1],
            [2, 1, 2, 2, 1, 3, 1],
        ],
        "category": "world",
        "category_label": "世界民族调式",
        "category_priority": 4,
        "default_checked": False,
    },
    "Arabic": {
        "intervals": [2, 2, 1, 2, 1, 2, 2],
        "mode_names": ["Rast", "Bayati", "Saba", "Nawa Athar", "Hijaz Kar"],
        "sub_scales": [
            [2, 2, 1, 2, 1, 2, 2],
            [2, 1, 2, 2, 1, 2, 2],
            [2, 1, 3, 1, 1, 2, 2],
            [1, 3, 1, 2, 2, 2, 1],
            [2, 1, 3, 1, 2, 2, 1],
        ],
        "category": "world",
        "category_label": "世界民族调式",
        "category_priority": 4,
        "default_checked": False,
    },
    "Persian": {
        "intervals": [2, 1, 2, 2, 2, 1, 2],
        "mode_names": ["Shur", "Homayun", "Chahargah", "Segah", "Esfahan"],
        "sub_scales": [
            [2, 1, 2, 2, 2, 1, 2],
            [1, 3, 1, 2, 2, 1, 2],
            [1, 3, 2, 1, 2, 2, 1],
            [2, 1, 3, 1, 2, 1, 2],
            [2, 1, 3, 2, 2, 1, 1],
        ],
        "category": "world",
        "category_label": "世界民族调式",
        "category_priority": 4,
        "default_checked": False,
    },
    "Ethiopian": {
        "intervals": [2, 1, 2, 2, 2, 1, 2],
        "mode_names": ["Tizita", "Bati", "Ambassel", "Anchihoye"],
        "sub_scales": [
            [2, 1, 2, 2, 2, 1, 2],
            [1, 2, 2, 2, 2, 2, 1],
            [2, 1, 3, 1, 2, 1, 2],
            [2, 1, 2, 1, 2, 2, 2],
        ],
        "category": "world",
        "category_label": "世界民族调式",
        "category_priority": 4,
        "default_checked": False,
    },
    "Jewish": {
        "intervals": [2, 1, 3, 1, 2, 2, 1],
        "mode_names": ["Mi Shebeirach", "Ahava Rabbah"],
        "sub_scales": [
            [2, 1, 3, 1, 2, 2, 1],
            [1, 3, 1, 2, 2, 2, 1],
        ],
        "category": "world",
        "category_label": "世界民族调式",
        "category_priority": 4,
        "default_checked": False,
    },
    "Spanish": {
        "intervals": [1, 3, 1, 2, 1, 2, 2],
        "mode_names": ["Spanish Phrygian"],
        "category": "world",
        "category_label": "世界民族调式",
        "category_priority": 4,
        "default_checked": False,
    },
}

# 向后兼容导出
PARENT_SCALES = {k: v["intervals"] for k, v in SCALE_REGISTRY.items()}
MODE_NAMES = {k: v["mode_names"] for k, v in SCALE_REGISTRY.items()
              if v["mode_names"]}
ALL_PARENTS = frozenset(SCALE_REGISTRY.keys())


# ── 辅助函数 ───────────────────────────────────────────

def _distinct_rotations(intervals: list[int]) -> int:
    """计算一个音阶间隔序列有多少个不重复的转位。

    全音阶 (2,2,1,2,2,2,1) → 7（无对称性）
    全音音阶 (2,2,2,2,2,2) → 1（完全对称）
    减音阶 (2,1,2,1,2,1,2,1) → 2（周期 2）
    """
    n = len(intervals)
    for k in range(1, n + 1):
        if intervals == intervals[k:] + intervals[:k]:
            return k
    return n


def build_mode_pcs(tonic_pc: int, parent_intervals: list[int], rotation: int) -> set[int]:
    """从 tonic 出发，按母音阶转位后的间隔构建 pitch class set。"""
    rotated = parent_intervals[rotation:] + parent_intervals[:rotation]
    pcs = {tonic_pc}
    cur = tonic_pc
    for step in rotated[:-1]:
        cur = (cur + step) % 12
        pcs.add(cur)
    return pcs


def format_mode_display(tonic: str, scale_id: str, rotation: int, entry: dict) -> str:
    """统一显示格式：{tonic} {mode_name} ({scale_id} #{rotation+1})

    条目设置 hide_rotation_suffix=True 时省略后缀。Messiaen 采用音程命名，
    名称本身已唯一标识调式，后缀只会造成 "(Messiaen #1)" 这类冗余。
    """
    mode_names = entry["mode_names"]
    if mode_names and rotation < len(mode_names):
        mode_name = mode_names[rotation]
    else:
        mode_name = scale_id
    if entry.get("hide_rotation_suffix"):
        return f"{tonic} {mode_name}"
    return f"{tonic} {mode_name} ({scale_id} #{rotation + 1})"


# ── 调式检测 ───────────────────────────────────────────

def detect_modes(
    notes: set[int],
    active_parents: set[str] | None = None,
    key_sig: str = "C",
    tonic_pc: int | None = None,
    scales: list[dict] | None = None,
) -> list[dict]:
    """
    识别匹配的调式。

    匹配条件:
      1. 输入 pitch class ⊆ 调式 pitch class set
      2. 调中心 = tonic_pc；未指定时取 min(notes) % 12（最低音 = 调中心）

    排序: missing ASC → category_priority ASC → parent ASC

    参数:
      notes: MIDI note numbers (非空)
      active_parents: 旧版母音阶过滤集合；scales 为 None 时生效
      key_sig: 调号，用于确定 #/b 命名
      tonic_pc: 强制指定调中心（0–11）；固定音阶后按同一调中心找新音阶时使用
      scales: 用户音阶库的启用行；提供时优先于 active_parents

    返回: 匹配列表，每项含 name, tonic, tonic_pc, mode, rotation, parent, pcs
    """
    if scales is not None:
        return _detect_from_scales(notes, scales, key_sig, tonic_pc)

    if not notes:
        return []

    input_pcs = {n % 12 for n in notes}
    if tonic_pc is None:
        tonic_pc = min(notes) % 12
    tonic_pc %= 12
    names = PITCH_NAMES if key_sig in _SHARP_KEYS else PITCH_NAMES_FLAT
    tonic_name = names[tonic_pc]

    parents = active_parents if active_parents is not None else ALL_PARENTS
    parents = parents & ALL_PARENTS

    raw = []

    for scale_id in sorted(parents):
        entry = SCALE_REGISTRY[scale_id]
        intervals = entry["intervals"]
        mode_names = entry["mode_names"]
        n_rot = len(mode_names) if mode_names else 1

        for rotation in range(n_rot):
            if "sub_scales" in entry:
                mode_pcs = build_mode_pcs(tonic_pc, entry["sub_scales"][rotation], 0)
            else:
                mode_pcs = build_mode_pcs(tonic_pc, intervals, rotation)
            if not input_pcs.issubset(mode_pcs):
                continue

            missing = len(mode_pcs) - len(input_pcs)
            mode_name = (mode_names[rotation] if mode_names
                         and rotation < len(mode_names) else scale_id)

            raw.append({
                "name": format_mode_display(tonic_name, scale_id, rotation, entry),
                "tonic": tonic_name,
                "tonic_pc": tonic_pc,
                "mode": mode_name,
                "rotation": rotation,
                "parent": scale_id,
                "_missing": missing,
                "_category_priority": entry["category_priority"],
                "_pcs": frozenset(mode_pcs),
            })

    # 排序: missing ASC → category_priority ASC → parent ASC
    # 必须在去重前排序，确保匹配度更高的优先
    raw.sort(key=lambda m: (m["_missing"], m["_category_priority"], m["parent"]))

    # 去重: (frozenset(mode_pcs), tonic_pc) — 处理减音阶重叠
    seen = set()
    deduped = []
    for m in raw:
        key = (m["_pcs"], tonic_pc)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(m)

    # 清理内部字段，保留 pcs
    result = []
    for m in deduped:
        entry = {k: v for k, v in m.items() if not k.startswith("_")}
        entry["pcs"] = sorted(m["_pcs"])
        result.append(entry)

    return result


def _detect_from_scales(notes: set[int], scales: list[dict],
                        key_sig: str = "C",
                        tonic_pc: int | None = None) -> list[dict]:
    """基于用户音阶库（enabled 行）的检测。"""
    if not notes:
        return []

    input_pcs = {n % 12 for n in notes}
    if tonic_pc is None:
        tonic_pc = min(notes) % 12
    tonic_pc %= 12
    names = PITCH_NAMES if key_sig in _SHARP_KEYS else PITCH_NAMES_FLAT
    tonic_name = names[tonic_pc]

    raw = []
    for scale in scales:
        if not scale.get("enabled", True):
            continue
        pcs = sorted({int(p) % 12 for p in (scale.get("pcs") or [])})
        if not pcs or 0 not in pcs:
            continue

        priority = scale.get("category_priority", 5)
        parent = scale.get("parent_id") or scale.get("group_label") or scale.get("id") or ""
        scale_id = scale.get("id") or ""
        row_order = scale.get("order", 0)

        if scale.get("kind") == "parent":
            intervals = [pcs[i + 1] - pcs[i] for i in range(len(pcs) - 1)]
            intervals.append(12 - pcs[-1])
            mode_names = list(scale.get("mode_names") or [scale.get("name") or ""])
            n_rot = min(len(mode_names), len(pcs))

            for rotation in range(n_rot):
                mode_pcs = build_mode_pcs(tonic_pc, intervals, rotation)
                if not input_pcs.issubset(mode_pcs):
                    continue

                if rotation == 0:
                    mode_name = scale.get("name") or mode_names[0]
                elif rotation < len(mode_names):
                    mode_name = mode_names[rotation]
                else:
                    mode_name = f"{scale.get('name') or ''} #{rotation + 1}"

                label = scale.get("label") or scale.get("name") or ""
                raw.append({
                    "name": f"{tonic_name} {mode_name} ({label} #{rotation + 1})",
                    "tonic": tonic_name,
                    "tonic_pc": tonic_pc,
                    "mode": mode_name,
                    "rotation": rotation,
                    "parent": parent,
                    "scale_id": scale_id,
                    "_missing": len(mode_pcs) - len(input_pcs),
                    "_category_priority": priority,
                    "_order": row_order,
                    "_pcs": frozenset(mode_pcs),
                })
        else:
            mode_pcs = {(tonic_pc + p) % 12 for p in pcs}
            if not input_pcs.issubset(mode_pcs):
                continue

            mode_name = scale.get("name") or ""
            rotation = int(scale.get("rotation") or 0)
            raw.append({
                "name": f"{tonic_name} {mode_name}",
                "tonic": tonic_name,
                "tonic_pc": tonic_pc,
                "mode": mode_name,
                "rotation": rotation,
                "parent": parent,
                "scale_id": scale_id,
                "_missing": len(mode_pcs) - len(input_pcs),
                "_category_priority": priority,
                "_order": row_order,
                "_pcs": frozenset(mode_pcs),
            })

    raw.sort(key=lambda m: (m["_missing"], m["_category_priority"],
                            m["_order"]))

    result = []
    for m in raw:
        entry = {k: v for k, v in m.items() if not k.startswith("_")}
        entry["pcs"] = sorted(m["_pcs"])
        result.append(entry)

    return result
