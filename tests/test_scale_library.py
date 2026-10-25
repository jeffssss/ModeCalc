"""用户音阶库 v2 测试。"""

import json

from mode_engine import detect_modes
from scale_library import ScaleLibrary, default_rows


def _by_name(rows, name):
    return next(row for row in rows if row["name"] == name)


def test_default_structure():
    rows = default_rows()
    assert len(rows) == 71
    assert sum(1 for row in rows if row["enabled"]) == 7
    assert sum(1 for row in rows if row["section"] == "natural") == 7
    assert sum(1 for row in rows if row["section"] == "limited") == 10
    assert sum(1 for row in rows if row["section"] == "world") == 28
    assert sum(1 for row in rows if row["group"] == "Chinese") == 8
    assert sum(1 for row in rows if row["section"] == "custom") == 0


def test_default_enabled_only_natural():
    payload = ScaleLibrary().payload()
    enabled = [row["name"] for row in payload["rows"] if row["enabled"]]
    assert enabled == [
        "Ionian", "Dorian", "Phrygian", "Lydian",
        "Mixolydian", "Aeolian", "Locrian",
    ]


def test_info_absolute_examples():
    rows = {row["name"]: row for row in ScaleLibrary().payload()["rows"]}
    assert "C Ionian ≡ A Aeolian" in rows["Ionian"]["info"]
    assert "C Dorian" in rows["Dorian"]["info"]
    assert "同于 Aeolian" in rows["Bayati"]["info"]


def test_chinese_seven_note_aliases():
    rows = {row["name"]: row for row in ScaleLibrary().payload()["rows"]}
    assert rows["Qingyue"]["alias_of_name"] == "Ionian"
    assert rows["Yanyue"]["alias_of_name"] == "Mixolydian"
    assert rows["Yayue"]["alias_of_name"] == "Lydian"


def test_alias_rows_default_off():
    rows = {row["name"]: row for row in ScaleLibrary().payload()["rows"]}
    assert rows["Flamenco"]["is_alias"]
    assert rows["Flamenco"]["alias_of_name"] == "Phrygian Dominant"
    assert rows["Bayati"]["alias_of_name"] == "Aeolian"
    assert rows["Purvi"]["alias_of_name"] == "Gypsy"
    assert not rows["Flamenco"]["enabled"]


def test_detection_with_default_library():
    library = ScaleLibrary()
    names = [m["name"] for m in detect_modes(
        {60, 62, 64, 65, 67, 69, 71}, scales=library.detection_rows()
    )]
    assert names == ["C Ionian"]

    names = [m["name"] for m in detect_modes(
        {60, 62, 63, 65, 67, 69, 70}, scales=library.detection_rows()
    )]
    assert "C Dorian" in names


def test_same_pcs_aliases_both_shown(tmp_path):
    library = ScaleLibrary(path=tmp_path / "settings.json")
    library.set_group_enabled("world", "Chinese", True)
    names = [m["name"] for m in detect_modes(
        {60, 62, 64, 65, 67, 69, 71}, scales=library.detection_rows()
    )]
    assert "C Ionian" in names
    assert "C Qingyue" in names


def test_set_group_enabled(tmp_path):
    library = ScaleLibrary(path=tmp_path / "settings.json")
    result = library.set_group_enabled("world", "Chinese", True)
    assert result["ok"]
    assert sum(1 for row in result["rows"] if row["enabled"]) == 15

    names = [m["name"] for m in detect_modes(
        {60, 62, 64, 67, 69}, scales=library.detection_rows()
    )]
    assert "C Gong" in names


def test_rename_creates_custom_copy(tmp_path):
    library = ScaleLibrary(path=tmp_path / "settings.json")
    result = library.update("builtin:natural:Ionian", name="Major")
    assert result["ok"]
    assert result["copied"]
    new_id = result["new_id"]
    rows = result["rows"]
    original = next(row for row in rows if row["id"] == "builtin:natural:Ionian")
    assert original["name"] == "Ionian"
    assert not original["enabled"]
    copy = next(row for row in rows if row["id"] == new_id)
    assert copy["section"] == "custom"
    assert copy["name"] == "Major"
    assert copy["enabled"]

    names = [m["name"] for m in detect_modes(
        {60, 62, 64, 65, 67, 69, 71}, scales=library.detection_rows()
    )]
    assert names == ["C Major"]


def test_edit_pcs_creates_custom_copy(tmp_path):
    library = ScaleLibrary(path=tmp_path / "settings.json")
    result = library.update("builtin:natural:Ionian", pcs=[0, 2, 4, 7, 9])
    assert result["ok"]
    assert result["copied"]
    new_id = result["new_id"]
    rows = result["rows"]
    original = next(row for row in rows if row["id"] == "builtin:natural:Ionian")
    assert original["name"] == "Ionian"
    assert not original["enabled"]
    custom = next(row for row in rows if row["id"] == new_id)
    assert custom["section"] == "custom"
    assert custom["name"] == "Ionian (自定义)"
    assert custom["pcs"] == [0, 2, 4, 7, 9]

    restored = library.reset()
    by_id = {row["id"]: row for row in restored["rows"]}
    assert by_id["builtin:natural:Ionian"]["enabled"]
    assert new_id in by_id


def test_default_delete_is_rejected(tmp_path):
    library = ScaleLibrary(path=tmp_path / "settings.json")
    result = library.delete("builtin:natural:Ionian")
    assert not result["ok"]
    assert "默认音阶不可删除" in result["error"]
    assert any(row["id"] == "builtin:natural:Ionian" for row in library.payload()["rows"])


def test_add_delete_and_reset(tmp_path):
    library = ScaleLibrary(path=tmp_path / "settings.json")
    added = library.add(name="我的音阶", pcs=[0, 2, 3, 7, 9])
    assert added["ok"]
    custom_id = added["new_id"]
    assert any(row["id"] == custom_id for row in added["rows"])

    deleted = library.delete(custom_id)
    assert deleted["ok"]
    assert not any(row["id"] == custom_id for row in deleted["rows"])

    reset = library.reset()
    assert any(row["id"] == "builtin:natural:Ionian" for row in reset["rows"])


def test_validation(tmp_path):
    library = ScaleLibrary(path=tmp_path / "settings.json")
    assert not library.add(name="", pcs=[0, 2, 4])["ok"]
    assert not library.add(name="Ionian", pcs=[0, 2, 4])["ok"]
    assert not library.add(name="缺根音", pcs=[2, 4, 7])["ok"]
    assert not library.add(name="太短", pcs=[0, 2])["ok"]
    assert not library.add(name="非法值", pcs=[0, 2, "x"])["ok"]


def test_old_state_is_ignored(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({
        "version": 2,
        "parents": ["Ionian"],
        "scale_library": {"version": 1, "overrides": {}, "deleted": [], "custom": []},
    }), encoding="utf-8")
    payload = ScaleLibrary.load(path).payload()
    assert payload["total"] == 71
    assert payload["enabled"] == 7


def test_persistence_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    library = ScaleLibrary(path=path)
    assert library.update("builtin:natural:Ionian", name="Major")["ok"]
    assert library.set_group_enabled("world", "Japanese", True)["ok"]
    assert library.add(name="我的音阶", pcs=[0, 2, 4, 7, 9])["ok"]

    reloaded = ScaleLibrary.load(path)
    payload = reloaded.payload()
    rows = {row["name"]: row for row in payload["rows"]}
    assert rows["Ionian"]["enabled"] is False
    assert rows["Major"]["enabled"]
    assert rows["Hirajoshi"]["enabled"]
    assert any(row["name"] == "我的音阶" for row in payload["rows"])
