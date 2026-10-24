"""固定音阶 + 红音派生音阶测试"""

from chord_engine import analyze
from mode_engine import detect_modes

# C Ionian: C D E F G A B
C_IONIAN = frozenset({0, 2, 4, 5, 7, 9, 11})


def _names(result):
    return [m["name"] for m in result["derived_matches"]]


def test_detect_modes_forced_tonic():
    """强制调中心时，名称与 tonic_pc 都用指定值，而非最低音。"""
    matches = detect_modes({60, 64, 67, 70}, {"Ionian"}, tonic_pc=0)
    names = [m["name"] for m in matches]
    assert "C Mixolydian (Ionian #5)" in names
    assert all(m["tonic"] == "C" and m["tonic_pc"] == 0 for m in matches)


def test_detect_modes_forced_tonic_flat_key():
    """调号为 F（降号）时派生名称使用降号拼写。"""
    # Bb D F Ab → Bb Mixolydian（Ionian 第 5 转位）
    matches = detect_modes({70, 74, 77, 80}, {"Ionian"}, key_sig="F", tonic_pc=10)
    assert "Bb Mixolydian (Ionian #5)" in [m["name"] for m in matches]


def test_derived_when_red_note_pressed():
    """固定 C Ionian，按 C E G Bb（Bb 为红音）→ 派生 C Mixolydian。"""
    result = analyze(
        {60, 64, 67, 70},
        analysis_mode="mode",
        active_parents={"Ionian"},
        pinned_pcs=C_IONIAN,
        pinned_tonic=0,
    )
    names = _names(result)
    assert "C Mixolydian (Ionian #5)" in names
    assert "C Ionian (Ionian #1)" not in names
    # 派生项必须包含全部按下音，且调中心仍是 C
    for m in result["derived_matches"]:
        assert {0, 4, 7, 10}.issubset(set(m["pcs"]))
        assert m["tonic_pc"] == 0
        assert frozenset(m["pcs"]) != C_IONIAN


def test_no_derived_without_red_note():
    """按下的音全在固定音阶内 → 不派生。"""
    result = analyze(
        {60, 64, 67},
        analysis_mode="mode",
        active_parents={"Ionian"},
        pinned_pcs=C_IONIAN,
        pinned_tonic=0,
    )
    assert result["derived_matches"] == []


def test_no_derived_with_single_note():
    """单个红音不触发派生（需要至少 2 个不同音高）。"""
    result = analyze(
        {70},
        analysis_mode="mode",
        active_parents={"Ionian"},
        pinned_pcs=C_IONIAN,
        pinned_tonic=0,
    )
    assert result["derived_matches"] == []


def test_no_derived_without_pinned_scale():
    """没有固定音阶时即使有音阶外音也不派生。"""
    result = analyze(
        {60, 64, 67, 70},
        analysis_mode="mode",
        active_parents={"Ionian"},
    )
    assert result["derived_matches"] == []


def test_no_derived_in_chord_mode():
    """Chord 分析模式下不计算派生音阶。"""
    result = analyze(
        {60, 64, 67, 70},
        analysis_mode="chord",
        active_parents={"Ionian"},
        pinned_pcs=C_IONIAN,
        pinned_tonic=0,
    )
    assert result["derived_matches"] == []


def test_derived_returns_all_matches():
    """勾选范围放大时返回全部满足条件的音阶（全部显示）。"""
    result = analyze(
        {60, 64, 67, 70},
        analysis_mode="mode",
        active_parents=None,  # 全部启用
        pinned_pcs=C_IONIAN,
        pinned_tonic=0,
    )
    assert len(result["derived_matches"]) >= 2
    assert all(m["tonic_pc"] == 0 for m in result["derived_matches"])
    assert all({0, 4, 7, 10}.issubset(set(m["pcs"]))
               for m in result["derived_matches"])
