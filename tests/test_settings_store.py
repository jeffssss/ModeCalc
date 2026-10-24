"""settings_store 单元测试"""

import json

import settings_store


def test_load_missing_returns_empty(tmp_path):
    missing = tmp_path / "nope.json"
    assert settings_store.load_settings(missing) == {}
    assert settings_store.load_parents(missing) is None


def test_save_and_load_parents_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    assert settings_store.save_parents(["Ionian", "Messiaen"], path) is True
    assert settings_store.load_parents(path) == ["Ionian", "Messiaen"]
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["version"] == settings_store.SETTINGS_VERSION


def test_empty_parents_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    assert settings_store.save_parents([], path) is True
    assert settings_store.load_parents(path) == []


def test_save_preserves_other_keys(tmp_path):
    path = tmp_path / "settings.json"
    settings_store.save_settings(
        {"version": 1, "parents": ["Ionian"], "future_key": 42}, path
    )
    settings_store.save_parents(["Messiaen"], path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["future_key"] == 42
    assert data["parents"] == ["Messiaen"]


def test_corrupt_json_falls_back(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    assert settings_store.load_settings(path) == {}
    assert settings_store.load_parents(path) is None


def test_invalid_parents_type_falls_back(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"parents": [1, 2]}), encoding="utf-8")
    assert settings_store.load_parents(path) is None


def test_save_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "dir" / "settings.json"
    assert settings_store.save_parents(["Ionian"], path) is True
    assert settings_store.load_parents(path) == ["Ionian"]


def test_default_path_uses_env_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MODECALC_SETTINGS_DIR", str(tmp_path))
    assert settings_store.default_settings_path() == tmp_path / "ModeCalc" / "settings.json"
