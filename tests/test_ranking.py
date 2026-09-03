"""Preprocessing must be shown to reorder a leaderboard, not merely shift it."""

from weldcheck.meshes import build
from weldcheck.ranking import rank_swap

BEST = ("closed_sphere", "closed_box", "closed_torus")
MIDDLING = ("closed_sphere", "closed_box", "open_box")
WORST = ("closed_sphere", "open_box", "two_boxes_sharing_a_vertex")


def _systems():
    return {
        "A_stl": ("stl", {n: build(n) for n in BEST}),
        "B_glb": ("glb", {n: build(n) for n in MIDDLING}),
        "C_glb": ("glb", {n: build(n) for n in WORST}),
    }


def test_ranking_swaps_under_preprocessing_alone():
    result = rank_swap(_systems())
    assert result.swapped


def test_the_soundest_system_ranks_last_before_welding():
    result = rank_swap(_systems())
    assert result.raw_order[-1] == "A_stl"
    assert result.welded_order[0] == "A_stl"


def test_displacement_is_reported_per_system():
    result = rank_swap(_systems())
    moved = dict((name, (before, after)) for name, before, after in result.displaced)
    assert moved["A_stl"] == (3, 1)
