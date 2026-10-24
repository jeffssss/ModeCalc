import pytest
from chord_engine import recognize


def test_empty():
    r = recognize(set())
    assert r["result_type"] == "none"
    assert r["result"] is None


def test_single_note():
    r = recognize({60})
    assert r["result_type"] == "single"
    assert r["result"]["name"] == "C"


def test_interval_fifth():
    r = recognize({60, 67})
    assert r["result_type"] == "interval"
    assert r["result"]["name"] == "C Perfect 5th"


def test_major_triad():
    r = recognize({60, 64, 67})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C"
    assert r["result"]["inversion"] == 0
    assert r["result"]["is_incomplete"] is False


def test_major_first_inversion():
    r = recognize({64, 67, 72})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C/E"
    assert r["result"]["inversion"] == 1
    assert r["result"]["is_incomplete"] is False


def test_minor_triad():
    r = recognize({60, 63, 67})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C-"
    assert r["result"]["inversion"] == 0


def test_dominant_7th():
    r = recognize({60, 64, 67, 70})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C7"
    assert r["result"]["inversion"] == 0


def test_half_dim_7th():
    r = recognize({60, 63, 66, 70})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "Cø"
    assert r["result"]["inversion"] == 0


def test_octave_duplicates():
    r = recognize({48, 60, 64, 67, 72})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C"


def test_five_pcs_major_9th():
    """C E G B D → C△9（5 PC 不再 unknown）"""
    r = recognize({60, 64, 67, 71, 74})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C△9"


def test_no_match_unknown():
    r = recognize({60, 61, 62})
    assert r["result_type"] == "unknown"
    assert r["result"]["name"] == "C n.c."


def test_b_major():
    r = recognize({59, 63, 66})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "B"


def test_csharp_major():
    r = recognize({61, 65, 68})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C#"


def test_interval_third():
    r = recognize({60, 64})
    assert r["result_type"] == "interval"
    assert r["result"]["name"] == "C Major 3rd"


def test_second_inversion():
    r = recognize({55, 60, 64})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C/G"
    assert r["result"]["inversion"] == 2


def test_minor_7th():
    r = recognize({60, 63, 67, 70})  # C Eb G Bb
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C-7"


def test_dim_7th():
    r = recognize({60, 63, 66, 69})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C°7"


def test_augmented():
    r = recognize({60, 64, 68})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C+"


def test_sus2():
    r = recognize({60, 62, 67})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "Csus2"


def test_sus4():
    r = recognize({60, 65, 67})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "Csus4"


def test_7sus4():
    r = recognize({60, 65, 67, 70})  # C F G Bb = C7sus4
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C7sus4"


# ── 和弦模板库新测试 ─────────────────────────────────

def test_dominant_7_sharp_11_voicing():
    """C E Bb F# → C7b5（缺 5th，C7b5 精确匹配优先于 C7#11）"""
    r = recognize({60, 64, 70, 66})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C7b5"


def test_dominant_9th():
    """C E G Bb D → C9"""
    r = recognize({60, 64, 67, 70, 74})
    assert r["result_type"] == "chord"
    assert r["result"]["name"] == "C9"


def test_complete_over_subset():
    """C E G Bb D → C9 优于 C7（完整度优先）"""
    r = recognize({60, 64, 67, 70, 74})
    assert r["result"]["name"] == "C9"


def test_root_position_over_inversion():
    """C E G A → C6 优于 Am7/C（原位优先）"""
    r = recognize({60, 64, 67, 69})
    assert r["result"]["name"] == "C6"


def test_dominant_7b5():
    """C E Gb Bb → C7b5"""
    r = recognize({60, 64, 66, 70})
    assert r["result"]["name"] == "C7b5"


def test_dominant_7sharp5():
    """C E G# Bb → C7#5"""
    r = recognize({60, 64, 68, 70})
    assert r["result"]["name"] == "C7#5"


def test_minor_9th():
    """C Eb G Bb D → C-9"""
    r = recognize({60, 63, 67, 70, 74})
    assert r["result"]["name"] == "C-9"


def test_half_dim_9th():
    """C Eb Gb Bb D → Cø9"""
    r = recognize({60, 63, 66, 70, 74})
    assert r["result"]["name"] == "Cø9"


def test_add9():
    """C E G D → Cadd9"""
    r = recognize({60, 64, 67, 74})
    assert r["result"]["name"] == "Cadd9"


def test_six_nine():
    """C E G A D → C69"""
    r = recognize({60, 64, 67, 69, 74})
    assert r["result"]["name"] == "C69"


def test_dim_major_7th():
    """C Eb Gb B → C°△7"""
    r = recognize({60, 63, 66, 71})
    assert r["result"]["name"] == "C°△7"
