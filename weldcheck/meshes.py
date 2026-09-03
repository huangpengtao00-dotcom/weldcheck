"""Programmatically built meshes whose topological status is known by construction.

Every builder returns a mesh whose ground-truth watertightness is stated in
`KNOWN_WATERTIGHT`, so a predicate's verdict can be scored without shipping any
model files. This is what makes the sensitivity experiment reproducible from a
clean clone with no downloads.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import trimesh

_SEED = 0


def closed_sphere() -> trimesh.Trimesh:
    return trimesh.creation.icosphere(subdivisions=3)


def closed_box() -> trimesh.Trimesh:
    return trimesh.creation.box(extents=(1.0, 1.0, 1.0))


def closed_torus() -> trimesh.Trimesh:
    return trimesh.creation.torus(major_radius=1.0, minor_radius=0.3)


def open_box() -> trimesh.Trimesh:
    """A cube with one face removed — genuinely not watertight."""
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    return trimesh.Trimesh(vertices=box.vertices, faces=box.faces[2:], process=False)


def two_boxes_sharing_a_vertex() -> trimesh.Trimesh:
    """Two cubes touching at a single corner: edge-manifold but vertex-non-manifold."""
    a = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    b = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    b.apply_translation((1.0, 1.0, 1.0))
    merged = trimesh.util.concatenate([a, b])
    merged.merge_vertices()
    return merged


def two_intersecting_boxes() -> trimesh.Trimesh:
    """Two interpenetrating cubes: self-intersecting, yet edge-manifold."""
    a = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    b = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    b.apply_translation((0.5, 0.5, 0.5))
    return trimesh.util.concatenate([a, b])


def noisy_sphere() -> trimesh.Trimesh:
    """A closed sphere with vertices jittered — closed, but not exactly coincident."""
    mesh = trimesh.creation.icosphere(subdivisions=3)
    rng = np.random.default_rng(_SEED)
    mesh.vertices += rng.normal(scale=1e-4, size=mesh.vertices.shape)
    return mesh


def quantized_sphere() -> trimesh.Trimesh:
    """A closed sphere whose shared corners no longer coincide exactly.

    Real STL files carry per-triangle floats, so corners that were one vertex
    upstream can land microns apart. Welding then depends on a tolerance the
    predicate's callers never report.
    """
    mesh = trimesh.creation.icosphere(subdivisions=3)
    rng = np.random.default_rng(_SEED)
    corners = mesh.vertices[mesh.faces].copy()
    corners += rng.normal(scale=1e-5, size=corners.shape)
    vertices = corners.reshape(-1, 3)
    faces = np.arange(len(vertices)).reshape(-1, 3)
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)


BUILDERS: dict[str, Callable[[], trimesh.Trimesh]] = {
    "closed_sphere": closed_sphere,
    "closed_box": closed_box,
    "closed_torus": closed_torus,
    "noisy_sphere": noisy_sphere,
    "quantized_sphere": quantized_sphere,
    "open_box": open_box,
    "two_boxes_sharing_a_vertex": two_boxes_sharing_a_vertex,
    "two_intersecting_boxes": two_intersecting_boxes,
}

# Topological ground truth by construction: closed surface, everywhere manifold.
# This is what the official predicate actually measures, so it is the fair target.
KNOWN_CLOSED_MANIFOLD: dict[str, bool] = {
    "closed_sphere": True,
    "closed_box": True,
    "closed_torus": True,
    "noisy_sphere": True,
    # Closed upstream, but its corners are no longer identical, so the predicate
    # sees a triangle soup until a coarse enough weld tolerance is applied.
    "quantized_sphere": False,
    "open_box": False,
    "two_boxes_sharing_a_vertex": False,
    "two_intersecting_boxes": True,
}

# Geometric defects the predicate cannot see: it pairs edges and never tests
# whether the surface passes through itself. A mesh listed here is reported
# watertight while being unusable downstream — the predicate's blind spot.
KNOWN_SELF_INTERSECTING: frozenset[str] = frozenset({"two_intersecting_boxes"})


def build(name: str) -> trimesh.Trimesh:
    return BUILDERS[name]()
