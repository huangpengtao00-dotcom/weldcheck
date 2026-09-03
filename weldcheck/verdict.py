"""The watertightness predicate as shipped by public 3D-generation projects.

`official_watertight` is a faithful transcription of the predicate in
Hunyuan3D-2.1's `hy3dshape/tools/evaluation/is_watertight.py`: no boundary
loops, edge-manifold, and vertex-manifold everywhere. Callers may rely on it
matching that script's verdict for the same face array.
"""

from __future__ import annotations

from dataclasses import dataclass

import igl
import numpy as np


@dataclass(frozen=True)
class Verdict:
    """One watertightness decision, with the raw counts that produced it."""

    watertight: bool
    boundary_loops: int
    edge_manifold: bool
    vertex_manifold: bool
    vertices: int
    faces: int


def official_watertight(vertices: np.ndarray, faces: np.ndarray) -> Verdict:
    faces = np.asarray(faces)
    if faces.size == 0:
        return Verdict(False, 0, False, False, len(vertices), 0)

    boundary = igl.boundary_loop(faces)
    # igl returns a flat array for a single loop and a list of arrays for several.
    if isinstance(boundary, np.ndarray):
        loops = 0 if boundary.size == 0 else 1
    else:
        loops = len(boundary)

    edge_manifold = bool(igl.is_edge_manifold(faces))
    vertex_manifold = bool(np.asarray(igl.is_vertex_manifold(faces)).all())

    return Verdict(
        watertight=loops == 0 and edge_manifold and vertex_manifold,
        boundary_loops=loops,
        edge_manifold=edge_manifold,
        vertex_manifold=vertex_manifold,
        vertices=len(vertices),
        faces=len(faces),
    )
