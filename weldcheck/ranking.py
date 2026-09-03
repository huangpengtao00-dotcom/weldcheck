"""Does preprocessing reorder a leaderboard, or only move the numbers?

A metric whose absolute values drift is a nuisance; a metric whose *ranking*
depends on an undocumented switch cannot be used to compare systems at all.
`rank_swap` answers that question for a set of systems, each contributing its
own meshes in its own delivery format.
"""

from __future__ import annotations

from dataclasses import dataclass

import trimesh

from .sensitivity import RAW, WELDED, scan_mesh


@dataclass
class SystemScore:
    system: str
    raw_ratio: float
    welded_ratio: float
    meshes: int


@dataclass
class RankSwap:
    scores: list[SystemScore]
    raw_order: list[str]
    welded_order: list[str]

    @property
    def swapped(self) -> bool:
        return self.raw_order != self.welded_order

    @property
    def displaced(self) -> list[tuple[str, int, int]]:
        """Systems whose rank changed, as (system, rank_raw, rank_welded), 1-indexed."""
        moved = []
        for name in self.raw_order:
            before = self.raw_order.index(name) + 1
            after = self.welded_order.index(name) + 1
            if before != after:
                moved.append((name, before, after))
        return moved


def _ratio(observations, setting: str) -> float:
    cell = [o for o in observations if o.setting == setting]
    return sum(o.verdict.watertight for o in cell) / len(cell) if cell else 0.0


def rank_swap(systems: dict[str, tuple[str, dict[str, trimesh.Trimesh]]]) -> RankSwap:
    """systems maps a system name to (delivery_format, {mesh_name: mesh})."""
    scores: list[SystemScore] = []
    for system, (fmt, meshes) in systems.items():
        observations = []
        for name, mesh in meshes.items():
            observations.extend(scan_mesh(mesh, name, formats=(fmt,)).observations)
        scores.append(
            SystemScore(
                system=system,
                raw_ratio=_ratio(observations, RAW),
                welded_ratio=_ratio(observations, WELDED),
                meshes=len(meshes),
            )
        )

    raw_order = [s.system for s in sorted(scores, key=lambda s: (-s.raw_ratio, s.system))]
    welded_order = [s.system for s in sorted(scores, key=lambda s: (-s.welded_ratio, s.system))]
    return RankSwap(scores=scores, raw_order=raw_order, welded_order=welded_order)
