"""The predicate must agree with topology known by construction."""

import pytest

from weldcheck.meshes import BUILDERS, KNOWN_CLOSED_MANIFOLD, KNOWN_SELF_INTERSECTING, build
from weldcheck.verdict import official_watertight


@pytest.mark.parametrize("name", sorted(BUILDERS))
def test_verdict_matches_constructed_topology(name):
    mesh = build(name)
    verdict = official_watertight(mesh.vertices, mesh.faces)
    assert verdict.watertight == KNOWN_CLOSED_MANIFOLD[name]


@pytest.mark.parametrize("name", sorted(KNOWN_SELF_INTERSECTING))
def test_predicate_cannot_see_self_intersection(name):
    """The documented blind spot: a self-intersecting mesh still passes."""
    mesh = build(name)
    assert official_watertight(mesh.vertices, mesh.faces).watertight is True


def test_empty_faces_is_not_watertight():
    import numpy as np

    verdict = official_watertight(np.zeros((0, 3)), np.zeros((0, 3), dtype=int))
    assert verdict.watertight is False
