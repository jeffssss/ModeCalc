import pytest
from mode_engine import (
    build_mode_pcs,
    detect_modes,
    PARENT_SCALES,
)


def test_build_mode_pcs_c_ionian():
    pcs = build_mode_pcs(0, PARENT_SCALES["Ionian"], 0)
    assert pcs == {0, 2, 4, 5, 7, 9, 11}


def test_build_mode_pcs_e_aeolian():
    pcs = build_mode_pcs(4, PARENT_SCALES["Ionian"], 5)
    assert pcs == {0, 2, 4, 6, 7, 9, 11}


def test_empty_notes():
    assert detect_modes(set()) == []


def test_c_major_triad_ionian():
    matches = detect_modes({60, 64, 67}, {"Ionian"})
    names = [m["name"] for m in matches]
    assert "C Ionian (Ionian #1)" in names


def test_e_scale_fragment_aeolian():
    # E F# A C D E G — 子集匹配 E Aeolian (bass=E)
    matches = detect_modes({64, 66, 69, 71, 72, 74, 76}, {"Ionian"})
    names = [m["name"] for m in matches]
    assert "E Aeolian (Ionian #6)" in names


def test_c_d_g_multiple_c_tonic():
    matches = detect_modes({60, 62, 67})
    names = [m["name"] for m in matches]
    assert "C Ionian (Ionian #1)" in names
    assert "C Dorian (Ionian #2)" in names
    assert all(m["tonic"] == "C" for m in matches)


def test_c_eb_g_aeolian():
    matches = detect_modes({60, 63, 67}, {"Ionian"})
    names = [m["name"] for m in matches]
    assert "C Aeolian (Ionian #6)" in names


def test_c_natural_minor_scale():
    # C D Eb F G A Bb — 完整音阶匹配 C Dorian (自然 6 音)
    matches = detect_modes({60, 62, 63, 65, 67, 69, 70})
    names = [m["name"] for m in matches]
    assert "C Dorian (Ionian #2)" in names


def test_active_parents_filter():
    notes = {60, 64, 67}
    all_matches = detect_modes(notes)
    ionian_only = detect_modes(notes, {"Ionian"})
    assert len(ionian_only) >= 1
    assert all(m["parent"] == "Ionian" for m in ionian_only)
    assert len(all_matches) >= len(ionian_only)


def test_single_note_matches_all_rotations():
    matches = detect_modes({60}, {"Ionian"})
    assert len(matches) == 7
    assert all(m["tonic"] == "C" for m in matches)


def test_no_match_outside_scale():
    matches = detect_modes({60, 61, 62}, {"Ionian"})
    assert matches == []


def test_harmonic_minor_parent():
    matches = detect_modes({60, 62, 63, 65, 67, 68, 71}, {"Harmonic Minor"})
    names = [m["name"] for m in matches]
    assert "C Harmonic Minor (Harmonic Minor #1)" in names


def test_melodic_minor_parent():
    matches = detect_modes({60, 62, 63, 65, 67, 69, 71}, {"Melodic Minor"})
    names = [m["name"] for m in matches]
    assert "C Melodic Minor (Melodic Minor #1)" in names


def test_all_parents_default():
    matches = detect_modes({60, 64, 67})
    names = [m["name"] for m in matches]
    assert "C Ionian (Ionian #1)" in names
    assert len(matches) >= 1


def test_display_includes_parent_rotation():
    m = detect_modes({60, 64, 67}, {"Ionian"})[0]
    assert m["name"] == "C Ionian (Ionian #1)"
    assert m["parent"] == "Ionian"
    assert m["rotation"] == 0


# ── 七音阶扩展 ───────────────────────────────────────

def test_harmonic_major():
    # C D E F G Ab B → C Harmonic Major
    matches = detect_modes({60, 62, 64, 65, 67, 68, 71}, {"Harmonic Major"})
    names = [m["name"] for m in matches]
    assert "C Harmonic Major (Harmonic Major #1)" in names


def test_double_harmonic_major():
    # C Db E F G Ab B → C Double Harmonic Major
    matches = detect_modes({60, 61, 64, 65, 67, 68, 71}, {"Double Harmonic Major"})
    names = [m["name"] for m in matches]
    assert "C Double Harmonic Major (Double Harmonic Major #1)" in names


def test_neapolitan_major():
    # C Db Eb F G A B → C Neapolitan Major
    matches = detect_modes({60, 61, 63, 65, 67, 69, 71}, {"Neapolitan Major"})
    names = [m["name"] for m in matches]
    assert "C Neapolitan Major (Neapolitan Major #1)" in names


def test_hungarian_minor():
    # C D Eb F# G Ab B → C Hungarian Minor
    matches = detect_modes({60, 62, 63, 66, 67, 68, 71}, {"Hungarian Minor"})
    names = [m["name"] for m in matches]
    assert "C Hungarian Minor (Hungarian Minor #1)" in names


def test_enigmatic():
    # C Db E F# G# A# B → C Enigmatic
    matches = detect_modes({60, 61, 64, 66, 68, 70, 71}, {"Enigmatic"})
    names = [m["name"] for m in matches]
    assert "C Enigmatic (Enigmatic #1)" in names


# ── 对称音阶 ──────────────────────────────────────────

def test_whole_tone():
    # C D E F# G# A# → C Whole Tone (全对称 → 1 条结果)
    matches = detect_modes({60, 62, 64, 66, 68, 70}, {"Whole Tone"})
    assert len(matches) == 1
    assert matches[0]["name"] == "C Whole Tone (Whole Tone #1)"


def test_diminished_wh():
    """Dim7 (C Eb Gb A) 匹配 Diminished WH — 仅 1 转位"""
    notes = {60, 63, 66, 69}
    matches = detect_modes(notes, {"Diminished WH"})
    assert len(matches) == 1
    assert matches[0]["name"] == "C Diminished (WH) (Diminished WH #1)"


def test_diminished_dedup():
    """Diminished WH + HW 各自产生 1 条不同结果"""
    notes = {60, 63, 66, 69}
    both = detect_modes(notes, {"Diminished WH", "Diminished HW"})
    names = [m["name"] for m in both]
    assert len(both) == 2
    assert "C Diminished (WH) (Diminished WH #1)" in names
    assert "C Diminished (HW) (Diminished HW #1)" in names


def test_augmented():
    """增三和弦 C E G# 同时匹配两个转位"""
    matches = detect_modes({60, 64, 68}, {"Augmented"})
    names = [m["name"] for m in matches]
    assert "C Augmented (Augmented #1)" in names
    assert "C Augmented (inv) (Augmented #2)" in names


# ── 梅西安有限移位调式 ───────────────────────────────────
# 命名规则：最小循环音程单元（半音数），如 211 = 大二度-小二度-小二度

def test_messiaen_211():
    """Messiaen 211（官方第 3 调式，rotation=0）匹配"""
    notes = {60, 62, 63, 64, 66, 67, 68, 70, 71}
    matches = detect_modes(notes, {"Messiaen"})
    names = [m["name"] for m in matches]
    assert "C Messiaen 211" in names


def test_messiaen_1131():
    """Messiaen 1131（官方第 4 调式）匹配"""
    notes = {60, 61, 62, 65, 66, 67, 68, 71}  # Mode 4 完整音阶
    matches = detect_modes(notes, {"Messiaen"})
    names = [m["name"] for m in matches]
    assert "C Messiaen 1131" in names


def test_messiaen_141():
    """Messiaen 141（官方第 5 调式）匹配"""
    notes = {60, 61, 65, 66, 67, 71}
    matches = detect_modes(notes, {"Messiaen"})
    names = [m["name"] for m in matches]
    assert "C Messiaen 141" in names


def test_messiaen_2211():
    """Messiaen 2211（官方第 6 调式）匹配"""
    notes = {60, 62, 64, 65, 66, 68, 70, 71}
    matches = detect_modes(notes, {"Messiaen"})
    names = [m["name"] for m in matches]
    assert "C Messiaen 2211" in names


def test_messiaen_11121():
    """Messiaen 11121（官方第 7 调式）匹配"""
    notes = {60, 61, 62, 63, 65, 66, 67, 68, 69, 71}
    matches = detect_modes(notes, {"Messiaen"})
    names = [m["name"] for m in matches]
    assert "C Messiaen 11121" in names


# ── 世界民族调式 ─────────────────────────────────────────

def test_japanese_hirajoshi():
    """Japanese 包含 Hirajoshi"""
    notes = {60, 62, 63, 67, 68}
    matches = detect_modes(notes, {"Japanese"})
    names = [m["name"] for m in matches]
    assert "C Hirajoshi (Japanese #1)" in names


def test_japanese_in_sen():
    """Japanese 包含 In Sen"""
    notes = {60, 61, 65, 67, 69}
    matches = detect_modes(notes, {"Japanese"})
    names = [m["name"] for m in matches]
    assert "C In Sen (Japanese #4)" in names


def test_indian_bhairav():
    """Indian 包含 Bhairav"""
    notes = {60, 61, 64, 66, 68, 70, 71}
    matches = detect_modes(notes, {"Indian"})
    names = [m["name"] for m in matches]
    assert "C Bhairav (Indian #1)" in names


def test_arabic_rast():
    """Arabic 包含 Rast"""
    notes = {60, 62, 64, 65, 67, 68, 70}
    matches = detect_modes(notes, {"Arabic"})
    names = [m["name"] for m in matches]
    assert "C Rast (Arabic #1)" in names


def test_persian_shur():
    """Persian 包含 Shur"""
    notes = {60, 62, 63, 65, 67, 69, 70}
    matches = detect_modes(notes, {"Persian"})
    names = [m["name"] for m in matches]
    assert "C Shur (Persian #1)" in names


def test_ethiopian_tizita():
    """Ethiopian 包含 Tizita"""
    notes = {60, 62, 63, 65, 67, 69, 70}
    matches = detect_modes(notes, {"Ethiopian"})
    names = [m["name"] for m in matches]
    assert "C Tizita (Ethiopian #1)" in names


def test_jewish_mi_shebeirach():
    """Jewish 包含 Mi Shebeirach"""
    notes = {60, 62, 63, 66, 67, 69, 71}
    matches = detect_modes(notes, {"Jewish"})
    names = [m["name"] for m in matches]
    assert "C Mi Shebeirach (Jewish #1)" in names


def test_spanish_phrygian():
    """Spanish 包含 Spanish Phrygian"""
    notes = {60, 61, 64, 65, 67, 68, 70}
    matches = detect_modes(notes, {"Spanish"})
    names = [m["name"] for m in matches]
    assert "C Spanish Phrygian (Spanish #1)" in names


# ── 五声/Blues ─────────────────────────────────────────

def test_major_pentatonic():
    # C D E G A → C Major Pentatonic
    matches = detect_modes({60, 62, 64, 67, 69}, {"Major Pentatonic"})
    names = [m["name"] for m in matches]
    assert "C Major Pentatonic (Major Pentatonic #1)" in names


def test_minor_pentatonic_is_rotation():
    # C Eb F G Bb = Major Pentatonic rotation 4 = C Minor Pentatonic
    matches = detect_modes({60, 63, 65, 67, 70}, {"Major Pentatonic"})
    names = [m["name"] for m in matches]
    assert "C Minor Pentatonic (Major Pentatonic #5)" in names


def test_blues_scale():
    # C Eb F F# G Bb → C Blues
    matches = detect_modes({60, 63, 65, 66, 67, 70}, {"Blues"})
    names = [m["name"] for m in matches]
    assert "C Blues (Blues #1)" in names


def test_major_blues():
    # C D D# E G A → C Major Blues
    matches = detect_modes({60, 62, 63, 64, 67, 69}, {"Major Blues"})
    names = [m["name"] for m in matches]
    assert "C Major Blues (Major Blues #1)" in names


# ── Bebop ─────────────────────────────────────────────

def test_bebop_dominant():
    # C D E F G A Bb B → C Bebop Dominant
    notes = {60, 62, 64, 65, 67, 69, 70, 71}
    matches = detect_modes(notes, {"Bebop Dominant"})
    names = [m["name"] for m in matches]
    assert "C Bebop Dominant (Bebop Dominant #1)" in names


def test_bebop_major():
    # C D E F G Ab A B → C Bebop Major
    notes = {60, 62, 64, 65, 67, 68, 69, 71}
    matches = detect_modes(notes, {"Bebop Major"})
    names = [m["name"] for m in matches]
    assert "C Bebop Major (Bebop Major #1)" in names


# ── 排序 ──────────────────────────────────────────────

def test_sort_by_missing():
    """3 个音匹配五声音阶 (missing=2) 优于匹配七音阶 (missing=4)"""
    matches = detect_modes({60, 64, 67}, {"Ionian", "Major Pentatonic"})
    # Major Pentatonic 在 Ionian 之前（missing=2 < 4）
    assert matches[0]["parent"] == "Major Pentatonic"


def test_sort_then_parent_alpha():
    """missing/category 相同时按 parent 字母序"""
    matches = detect_modes({60, 64, 67}, {"Harmonic Minor", "Ionian", "Melodic Minor"})
    # 提取 distinct parent 顺序（跳过每个 scale 内部的多 match）
    distinct = []
    for m in matches:
        p = m["parent"]
        if not distinct or p != distinct[-1]:
            distinct.append(p)
    assert distinct[:3] == ["Harmonic Minor", "Ionian", "Melodic Minor"]
