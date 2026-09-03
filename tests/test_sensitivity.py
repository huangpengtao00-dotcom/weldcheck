"""The central claim, as executable assertions."""

import pytest

from weldcheck.meshes import BUILDERS, build
from weldcheck.sensitivity import RAW, WELDED, ratio_table, scan_corpus, scan_mesh, tolerance_sweep

CLOSED = ("closed_sphere", "closed_box", "closed_torus")


@pytest.fixture(scope="module")
def corpus():
    return {name: build(name) for name in BUILDERS}


@pytest.mark.parametrize("name", CLOSED)
def test_stl_round_trip_flips_a_sound_mesh(name):
    """A mesh that IS closed and manifold fails the predicate after an STL round trip."""
    result = scan_mesh(build(name), name, formats=("stl",))
    assert [f.fmt for f in result.flips] == ["stl"]
    flip = result.flips[0]
    assert flip.from_watertight is False
    assert flip.to_watertight is True


@pytest.mark.parametrize("name", CLOSED)
@pytest.mark.parametrize("fmt", ["glb", "ply"])
def test_topology_carrying_formats_do_not_flip(name, fmt):
    result = scan_mesh(build(name), name, formats=(fmt,))
    assert result.flips == []


def test_stl_gap_is_large_and_others_are_zero(corpus):
    table = ratio_table(scan_corpus(corpus))
    assert table["stl"]["gap_pp"] > 50.0
    assert table["glb"]["gap_pp"] == pytest.approx(0.0)
    assert table["ply"]["gap_pp"] == pytest.approx(0.0)


def test_unwelded_stl_reports_nothing_watertight(corpus):
    result = scan_corpus(corpus, formats=("stl",))
    assert result.ratio("stl", RAW) == 0.0
    assert result.ratio("stl", WELDED) > 0.0


def test_stl_weld_collapses_vertices_to_about_a_sixth():
    result = scan_mesh(build("closed_sphere"), "closed_sphere", formats=("stl",))
    assert result.flips[0].vertex_retention < 0.25


def test_tolerance_sweep_is_monotone_in_nothing_but_still_moves():
    """A coarse tolerance can weld a mesh that a fine one leaves as a triangle soup."""
    sweep = tolerance_sweep({name: build(name) for name in CLOSED}, digits=(1, 4, 8))
    assert len(sweep) == 3
    assert max(sweep.values()) > 0.0


def test_weld_tolerance_alone_flips_the_verdict():
    """Same file, same predicate: a coarser tolerance welds it, a finer one does not."""
    sweep = tolerance_sweep({"quantized_sphere": build("quantized_sphere")}, digits=(2, 5))
    assert sweep[2] == 1.0
    assert sweep[5] == 0.0
