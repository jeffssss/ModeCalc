"""用户音阶库 v2。

每一行都是**独立音阶**（一个八度音集 + 名称），不再有“父音阶/子音阶”的
不可编辑关系。分类（section）与分组（group）只用于 UI 折叠与信息展示：

- Natural Mode：7 个调式独立行
- Harmonic Major / Harmonic Minor / Melodic Minor：各 7 行
- Jazz：Blues 1 / Blues 2 / Bebop ×3
- Modes of limited transposition：全音阶、减音阶 ×2、Messiaen 3–7、增音阶 ×2
- World Music：Chinese（五声 + 七声）、Japanese、Gypsy、Flamenco、Hungarian、Neapolitan、Indian、Arabic

跨分类重复的音列保留为“别名行”（默认关闭使用），信息列显示“同于 …”。
默认音阶不可直接修改/删除：改名或改音集会复制成 Custom 中的新音阶。
用户改动保存为 overrides / custom；不迁移 v1.1.0 的旧结构。
"""

import copy
import threading
import uuid

from mode_engine import PITCH_NAMES_FLAT, SCALE_REGISTRY
from settings_store import load_scale_library, save_scale_library

STATE_VERSION = 2

SECTION_ORDER = [
    ("natural", "Natural Mode", 0),
    ("harmonic_major", "Harmonic Major", 1),
    ("harmonic_minor", "Harmonic Minor", 2),
    ("melodic_minor", "Melodic Minor", 3),
    ("jazz", "Jazz", 4),
    ("limited", "Modes of limited transposition", 5),
    ("world", "World Music", 6),
    ("custom", "Custom", 7),
]
SECTION_LABELS = {key: label for key, label, _ in SECTION_ORDER}
SECTION_INDEX = {key: index for key, _, index in SECTION_ORDER}
SECTION_PRIORITY = {
    "natural": 0,
    "harmonic_major": 0,
    "harmonic_minor": 0,
    "melodic_minor": 0,
    "limited": 1,
    "jazz": 2,
    "world": 3,
    "custom": 5,
}

CUSTOM_SECTION = "custom"
CUSTOM_GROUP = "Custom"
DEFAULT_PCS = [0, 2, 4, 5, 7, 9, 11]
MAX_NAME_LEN = 40
MIN_NOTES = 3
MAX_NOTES = 12

GROUP_ORDER = {
    "Natural Mode": 0,
    "Harmonic Major": 0,
    "Harmonic Minor": 0,
    "Melodic Minor": 0,
    "Jazz": 0,
    "Modes of limited transposition": 0,
    "Chinese": 0,
    "Japanese": 1,
    "Gypsy": 2,
    "Flamenco": 3,
    "Hungarian": 4,
    "Neapolitan": 5,
    "Indian": 6,
    "Arabic": 7,
    "Custom": 0,
}


def pcs_from_intervals(intervals) -> list[int]:
    pcs = [0]
    cur = 0
    for step in intervals[:-1]:
        cur = (cur + step) % 12
        pcs.append(cur)
    return sorted(set(pcs))


def _rotated(seq, index):
    return seq[index:] + seq[:index]


def _row(section, group, name, pcs, rotation, enabled, order,
         alias_of=None):
    return {
        "id": f"builtin:{section}:{name}",
        "kind": "single",
        "name": name,
        "pcs": sorted(set(int(p) % 12 for p in pcs)),
        "section": section,
        "section_label": SECTION_LABELS[section],
        "section_order": SECTION_INDEX[section],
        "group": group,
        "group_label": group,
        "group_order": GROUP_ORDER.get(group, 0),
        "rotation": rotation,
        "enabled": bool(enabled),
        "builtin": True,
        "alias_of": alias_of,
        "order": order,
        "category_priority": SECTION_PRIORITY.get(section, 5),
        "info": "",
    }


def _add_single(rows, section, group, name, intervals=None, pcs=None,
                enabled=False):
    if pcs is None:
        pcs = pcs_from_intervals(intervals)
    rows.append(_row(section, group, name, pcs, 0, enabled, len(rows)))


def _add_rotations(rows, section, group, names, intervals, enabled=False):
    base = len(rows)
    for i, name in enumerate(names):
        pcs = pcs_from_intervals(_rotated(intervals, i))
        rows.append(_row(section, group, name, pcs, i, enabled, base + i))


def _family(rows, section, group, entry, enabled=False):
    _add_rotations(rows, section, group, entry["mode_names"],
                   entry["intervals"], enabled=enabled)


def default_rows() -> list[dict]:
    rows: list[dict] = []

    # ── 五个七声家族 ───────────────────────────────
    _family(rows, "natural", "Natural Mode",
            SCALE_REGISTRY["Ionian"], enabled=True)
    _family(rows, "harmonic_major", "Harmonic Major",
            SCALE_REGISTRY["Harmonic Major"])
    _family(rows, "harmonic_minor", "Harmonic Minor",
            SCALE_REGISTRY["Harmonic Minor"])
    _family(rows, "melodic_minor", "Melodic Minor",
            SCALE_REGISTRY["Melodic Minor"])

    # ── Jazz ──────────────────────────────────────
    _add_single(rows, "jazz", "Jazz", "Blues 1",
                intervals=SCALE_REGISTRY["Blues"]["intervals"])
    _add_single(rows, "jazz", "Jazz", "Blues 2",
                intervals=SCALE_REGISTRY["Major Blues"]["intervals"])
    for name, sid in (
        ("Bebop Dominant", "Bebop Dominant"),
        ("Bebop Major", "Bebop Major"),
        ("Bebop Dorian", "Bebop Dorian"),
    ):
        _add_single(rows, "jazz", "Jazz", name,
                    intervals=SCALE_REGISTRY[sid]["intervals"])

    # ── 有限移位调式 ───────────────────────────────
    _add_single(rows, "limited", "Modes of limited transposition", "Whole Tone",
                intervals=SCALE_REGISTRY["Whole Tone"]["intervals"])
    _add_single(rows, "limited", "Modes of limited transposition", "Diminished WH",
                intervals=SCALE_REGISTRY["Diminished WH"]["intervals"])
    _add_single(rows, "limited", "Modes of limited transposition", "Diminished HW",
                intervals=SCALE_REGISTRY["Diminished HW"]["intervals"])
    messiaen = SCALE_REGISTRY["Messiaen"]
    for i, sub in enumerate(messiaen["sub_scales"]):
        _add_single(rows, "limited", "Modes of limited transposition",
                    messiaen["mode_names"][i], intervals=sub)
    aug = SCALE_REGISTRY["Augmented"]
    for i, name in enumerate(aug["mode_names"]):
        _add_single(rows, "limited", "Modes of limited transposition", name,
                    pcs=pcs_from_intervals(_rotated(aug["intervals"], i)))

    # ── 世界音乐 ──────────────────────────────────
    pent = [2, 2, 3, 2, 3]
    _add_rotations(rows, "world", "Chinese",
                   ["Gong", "Shang", "Jue", "Zhi", "Yu"], pent)
    _add_single(rows, "world", "Chinese", "Yayue", [2, 2, 2, 1, 2, 2, 1])
    _add_single(rows, "world", "Chinese", "Qingyue", [2, 2, 1, 2, 2, 2, 1])
    _add_single(rows, "world", "Chinese", "Yanyue", [2, 2, 1, 2, 2, 1, 2])

    for name, intervals in (
        ("Hirajoshi", [2, 1, 4, 1, 4]),
        ("Kumoijoshi", [2, 1, 4, 2, 3]),
        ("Iwato", [1, 4, 1, 4, 2]),
        ("In Sen", [1, 4, 2, 2, 3]),
    ):
        _add_single(rows, "world", "Japanese", name, intervals=intervals)

    _add_single(rows, "world", "Gypsy", "Gypsy", [1, 3, 1, 2, 1, 3, 1])
    _add_single(rows, "world", "Flamenco", "Flamenco", [1, 3, 1, 2, 1, 2, 2])
    _add_single(rows, "world", "Hungarian", "Hungarian Minor",
                [2, 1, 3, 1, 1, 3, 1])
    _add_single(rows, "world", "Hungarian", "Hungarian Major",
                [3, 1, 2, 1, 2, 1, 2])
    _add_single(rows, "world", "Neapolitan", "Neapolitan Major",
                [1, 2, 2, 2, 2, 2, 1])
    _add_single(rows, "world", "Neapolitan", "Neapolitan Minor",
                [1, 2, 2, 2, 1, 3, 1])
    for name, intervals in (
        ("Bhairav", [1, 3, 2, 2, 2, 1, 1]),
        ("Purvi", [1, 3, 1, 2, 1, 3, 1]),
        ("Todi", [1, 2, 3, 1, 1, 3, 1]),
        ("Marwa", [1, 3, 2, 1, 2, 2, 1]),
        ("Kafi", [2, 1, 2, 2, 1, 3, 1]),
    ):
        _add_single(rows, "world", "Indian", name, intervals=intervals)
    for name, intervals in (
        ("Rast", [2, 2, 1, 2, 1, 2, 2]),
        ("Bayati", [2, 1, 2, 2, 1, 2, 2]),
        ("Saba", [2, 1, 3, 1, 1, 2, 2]),
        ("Nawa Athar", [1, 3, 1, 2, 2, 2, 1]),
        ("Hijaz Kar", [2, 1, 3, 1, 2, 2, 1]),
    ):
        _add_single(rows, "world", "Arabic", name, intervals=intervals)

    # 世界音乐中的重复音列标记为别名行（默认关闭）
    seen = {}
    for row in rows:
        if row["section"] != "world":
            seen.setdefault(tuple(row["pcs"]), row["id"])
    for row in rows:
        if row["section"] != "world":
            continue
        key = tuple(row["pcs"])
        if key in seen:
            row["alias_of"] = seen[key]
        else:
            seen[key] = row["id"]

    _build_info(rows)
    return rows


def _build_info(rows: list[dict]) -> None:
    by_id = {row["id"]: row for row in rows}
    aliases = {}
    for row in rows:
        if row["alias_of"]:
            aliases.setdefault(row["alias_of"], []).append(row["name"])

    for row in rows:
        target = set(row["pcs"])
        candidates = []
        for other in rows:
            if other["id"] == row["id"] or other["alias_of"]:
                continue
            for tonic in range(12):
                shifted = {(tonic + p) % 12 for p in other["pcs"]}
                if shifted == target:
                    candidates.append((other["name"], tonic, other["group"]))
        candidates = sorted(set(candidates), key=lambda item: (item[0], item[1]))

        parts = []
        for name, tonic, group in candidates[:2]:
            label = f"{PITCH_NAMES_FLAT[tonic]} {name}"
            if group != row["group"]:
                label += f" ({group})"
            parts.append(label)

        text = f"C {row['name']}"
        if row["alias_of"]:
            canonical = by_id.get(row["alias_of"])
            if canonical:
                text = f"同于 {canonical['name']} · {text}"
        if parts:
            text += " ≡ " + " / ".join(parts)
        if aliases.get(row["id"]):
            text += " · 别名 " + "、".join(aliases[row["id"]])
        row["info"] = text


def _normalize_state(raw) -> dict:
    state = {"version": STATE_VERSION, "overrides": {}, "deleted": [], "custom": []}
    if not isinstance(raw, dict) or raw.get("version") != STATE_VERSION:
        return state

    overrides = raw.get("overrides")
    if isinstance(overrides, dict):
        for rid, value in overrides.items():
            if not isinstance(rid, str) or not isinstance(value, dict):
                continue
            item = {}
            if isinstance(value.get("name"), str):
                item["name"] = value["name"].strip()
            if "pcs" in value:
                pcs = _clean_pcs(value.get("pcs"))
                if pcs is not None:
                    item["pcs"] = pcs
            if isinstance(value.get("enabled"), bool):
                item["enabled"] = value["enabled"]
            if item:
                state["overrides"][rid] = item

    deleted = raw.get("deleted")
    if isinstance(deleted, list):
        state["deleted"] = [v for v in deleted if isinstance(v, str)]

    custom = raw.get("custom")
    if isinstance(custom, list):
        for value in custom:
            if not isinstance(value, dict):
                continue
            rid = value.get("id")
            name = value.get("name")
            pcs = _clean_pcs(value.get("pcs"))
            if not (isinstance(rid, str) and isinstance(name, str) and pcs is not None):
                continue
            order = value.get("order", 0)
            if not isinstance(order, int):
                order = 0
            state["custom"].append({
                "id": rid,
                "name": name.strip(),
                "pcs": pcs,
                "enabled": bool(value.get("enabled", True)),
                "order": order,
            })
    return state


def _clean_pcs(value) -> list[int] | None:
    if not isinstance(value, (list, tuple)):
        return None
    try:
        pcs = sorted(set(int(v) % 12 for v in value))
    except (TypeError, ValueError):
        return None
    if 0 not in pcs or not (MIN_NOTES <= len(pcs) <= MAX_NOTES):
        return None
    return pcs


class ScaleLibrary:
    def __init__(self, state=None, path=None):
        self._lock = threading.RLock()
        self._path = path
        self._state = _normalize_state(state)
        self._rows: list[dict] = []
        self._rebuild()

    @classmethod
    def load(cls, path=None) -> "ScaleLibrary":
        return cls(load_scale_library(path), path=path)

    # ── 重建 / 持久化 ─────────────────────────────

    def _rebuild(self) -> None:
        rows = default_rows()
        by_id = {row["id"]: row for row in rows}

        for rid, override in self._state["overrides"].items():
            row = by_id.get(rid)
            if row is None:
                continue
            if "enabled" in override:
                row["enabled"] = bool(override["enabled"])

        deleted = set(self._state["deleted"])
        # 内置音阶不可删除；deleted 仅用于兼容旧状态，不作用于默认行
        rows = [row for row in rows if not (row["id"] in deleted and not row["builtin"])]

        used = {row["id"] for row in rows}
        max_order = max((row["order"] for row in rows), default=-1)
        for i, item in enumerate(self._state["custom"]):
            if item["id"] in used:
                continue
            used.add(item["id"])
            rows.append({
                "id": item["id"],
                "kind": "single",
                "name": item["name"],
                "pcs": list(item["pcs"]),
                "section": CUSTOM_SECTION,
                "section_label": SECTION_LABELS[CUSTOM_SECTION],
                "section_order": SECTION_INDEX[CUSTOM_SECTION],
                "group": CUSTOM_GROUP,
                "group_label": CUSTOM_GROUP,
                "group_order": GROUP_ORDER[CUSTOM_GROUP],
                "rotation": 0,
                "enabled": bool(item["enabled"]),
                "builtin": False,
                "alias_of": None,
                "order": item.get("order", max_order + 1 + i),
                "category_priority": SECTION_PRIORITY[CUSTOM_SECTION],
                "info": "",
            })

        rows.sort(key=lambda row: (row["section_order"], row["group_order"],
                                   row["order"], row["name"]))
        _build_info(rows)
        self._rows = rows

    def to_state(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._state)

    def save(self) -> bool:
        with self._lock:
            return save_scale_library(self.to_state(), self._path)

    # ── 读取 ──────────────────────────────────────

    def rows(self) -> list[dict]:
        with self._lock:
            return copy.deepcopy(self._rows)

    def detection_rows(self) -> list[dict]:
        fields = ("id", "kind", "name", "pcs", "section", "section_label",
                  "group", "group_label", "order", "rotation",
                  "category_priority", "builtin")
        with self._lock:
            return [
                copy.deepcopy({key: row.get(key) for key in fields})
                for row in self._rows
                if row["enabled"]
            ]

    def payload(self) -> dict:
        with self._lock:
            rows = copy.deepcopy(self._rows)
        for row in rows:
            row["is_alias"] = bool(row.get("alias_of"))
            row["alias_of_name"] = ""
            if row.get("alias_of"):
                for other in rows:
                    if other["id"] == row["alias_of"]:
                        row["alias_of_name"] = other["name"]
                        break
        enabled = sum(1 for row in rows if row["enabled"])
        return {"rows": rows, "enabled": enabled, "total": len(rows)}

    # ── 校验 / 修改 ───────────────────────────────

    def _find(self, scale_id):
        for row in self._rows:
            if row["id"] == scale_id:
                return row
        return None

    def _custom(self, scale_id):
        for item in self._state["custom"]:
            if item["id"] == scale_id:
                return item
        return None

    def _validate(self, name, pcs, exclude_id=None):
        name = (name or "").strip()
        if not name:
            return "名称不能为空", None
        if len(name) > MAX_NAME_LEN:
            return f"名称不能超过 {MAX_NAME_LEN} 个字符", None
        cleaned = _clean_pcs(pcs)
        if cleaned is None:
            return "音阶必须包含根音，且至少 3 个、最多 12 个音", None
        folded = name.casefold()
        with self._lock:
            for row in self._rows:
                if row["id"] == exclude_id:
                    continue
                if row["name"].casefold() == folded:
                    return "名称已存在", None
        return None, cleaned

    def _result(self, **extra) -> dict:
        payload = self.payload()
        payload["ok"] = True
        payload.update(extra)
        return payload

    def _unique_name(self, base: str) -> str:
        base = (base or "自定义音阶").strip()[:MAX_NAME_LEN]
        names = {row["name"].casefold() for row in self._rows}
        if base.casefold() not in names:
            return base
        for index in range(2, 1000):
            suffix = f" {index}"
            candidate = base[:MAX_NAME_LEN - len(suffix)] + suffix
            if candidate.casefold() not in names:
                return candidate
        return base

    def _commit(self, snapshot) -> dict | None:
        if self.save():
            return None
        self._state = snapshot
        self._rebuild()
        return {"ok": False, "error": "设置写入失败，请检查文件权限"}

    def set_enabled(self, scale_id, enabled) -> dict:
        with self._lock:
            row = self._find(scale_id)
            if row is None:
                return {"ok": False, "error": "音阶不存在"}
            snapshot = copy.deepcopy(self._state)
            if row["builtin"]:
                self._state["overrides"].setdefault(scale_id, {})["enabled"] = bool(enabled)
            else:
                item = self._custom(scale_id)
                if item is None:
                    return {"ok": False, "error": "音阶不存在"}
                item["enabled"] = bool(enabled)
            self._rebuild()
            return self._commit(snapshot) or self._result()

    def set_group_enabled(self, section, group, enabled) -> dict:
        with self._lock:
            snapshot = copy.deepcopy(self._state)
            found = False
            for row in self._rows:
                if row["section"] != section or row["group"] != group:
                    continue
                found = True
                if row["builtin"]:
                    self._state["overrides"].setdefault(row["id"], {})["enabled"] = bool(enabled)
                else:
                    item = self._custom(row["id"])
                    if item is not None:
                        item["enabled"] = bool(enabled)
            if not found:
                return {"ok": False, "error": "分组不存在"}
            self._rebuild()
            return self._commit(snapshot) or self._result()

    def update(self, scale_id, name=None, pcs=None) -> dict:
        with self._lock:
            row = self._find(scale_id)
            if row is None:
                return {"ok": False, "error": "音阶不存在"}

            new_name = row["name"] if name is None else name
            new_pcs = row["pcs"] if pcs is None else pcs
            error, cleaned = self._validate(new_name, new_pcs, exclude_id=scale_id)
            if error:
                return {"ok": False, "error": error}

            pcs_changed = pcs is not None and set(cleaned) != set(row["pcs"])
            name_changed = name is not None and new_name.strip() != row["name"]

            if row["builtin"]:
                # 默认音阶本身不可改：复制出一条自定义音阶，原默认行保留并关闭
                if not name_changed and not pcs_changed:
                    return self._result()
                copy_base = (new_name.strip() if name_changed
                             else f"{row['name']} (自定义)")
                copy_name = self._unique_name(copy_base)
                new_id = f"user:{uuid.uuid4().hex}"
                max_order = max((r["order"] for r in self._rows), default=-1)
                snapshot = copy.deepcopy(self._state)
                self._state["custom"].append({
                    "id": new_id,
                    "name": copy_name,
                    "pcs": cleaned,
                    "enabled": row["enabled"],
                    "order": max_order + 1,
                })
                self._state["overrides"].setdefault(scale_id, {})["enabled"] = False
                self._rebuild()
                error = self._commit(snapshot)
                if error:
                    return error
                return self._result(new_id=new_id, copied=True)

            item = self._custom(scale_id)
            if item is None:
                return {"ok": False, "error": "音阶不存在"}
            snapshot = copy.deepcopy(self._state)
            if name_changed:
                item["name"] = new_name.strip()
            if pcs_changed:
                item["pcs"] = cleaned
            self._rebuild()
            return self._commit(snapshot) or self._result()

    def add(self, name=None, pcs=None) -> dict:
        with self._lock:
            if name is None:
                existing = {row["name"].casefold() for row in self._rows}
                index = 1
                candidate = "新音阶"
                while candidate.casefold() in existing:
                    index += 1
                    candidate = f"新音阶 {index}"
                name = candidate
            error, cleaned = self._validate(name, DEFAULT_PCS if pcs is None else pcs)
            if error:
                return {"ok": False, "error": error}

            snapshot = copy.deepcopy(self._state)
            scale_id = f"user:{uuid.uuid4().hex}"
            max_order = max((row["order"] for row in self._rows), default=-1)
            self._state["custom"].append({
                "id": scale_id,
                "name": name.strip(),
                "pcs": cleaned,
                "enabled": True,
                "order": max_order + 1,
            })
            self._rebuild()
            error = self._commit(snapshot)
            if error:
                return error
            return self._result(new_id=scale_id)

    def delete(self, scale_id) -> dict:
        with self._lock:
            row = self._find(scale_id)
            if row is None:
                return {"ok": False, "error": "音阶不存在"}
            if row["builtin"]:
                return {"ok": False, "error": "默认音阶不可删除，可用「使用」关闭"}
            snapshot = copy.deepcopy(self._state)
            self._state["custom"] = [
                item for item in self._state["custom"] if item["id"] != scale_id
            ]
            self._rebuild()
            return self._commit(snapshot) or self._result()

    def reset(self) -> dict:
        with self._lock:
            snapshot = copy.deepcopy(self._state)
            self._state["overrides"] = {}
            self._state["deleted"] = []
            self._rebuild()
            return self._commit(snapshot) or self._result()
