"""Measure how much a watertightness statistic moves under preprocessing alone.

The unit of measurement is a *flip*: the same mesh, the same predicate, two
different preprocessing settings, two different verdicts. Callers may rely on
`scan_mesh` performing a real file round-trip — the format's own topology
handling is part of what is being measured, so it cannot be simulated.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field

import numpy as np
import trimesh

from .verdict import Verdict, official_watertight

# `trimesh.load(process=False)` is what Hunyuan3D-2.1's evaluation entry point
# uses; the default (process=True) is what the same repo's data pipeline uses.
RAW = "process=False"
WELDED = "welded"


@dataclass(frozen=True)
class Observation:
    mesh: str
    fmt: str
    setting: str
    verdict: Verdict


@dataclass
class Flip:
    mesh: str
    fmt: str
    from_setting: str
    to_setting: str
    from_watertight: bool
    to_watertight: bool
    vertices_before: int
    vertices_after: int

    @property
    def vertex_retention(self) -> float:
        return self.vertices_after / self.vertices_before if self.vertices_before else 1.0


@dataclass
class ScanResult:
    observations: list[Observation] = field(default_factory=list)
    flips: list[Flip] = field(default_factory=list)

    def ratio(self, fmt: str, setting: str) -> float:
        """Watertight ratio for one (format, setting) cell — the number a paper reports."""
        cell = [o for o in self.observations if o.fmt == fmt and o.setting == setting]
        if not cell:
            raise KeyError(f"no observations for {fmt}/{setting}")
        return sum(o.verdict.watertight for o in cell) / len(cell)

    def formats(self) -> list[str]:
        return sorted({o.fmt for o in self.observations})


def _load(path: str, *, weld: bool, digits_vertex: int | None) -> trimesh.Trimesh:
    mesh = trimesh.load(path, force="mesh", process=False)
    if weld:
        mesh.merge_vertices(digits_vertex=digits_vertex)
    return mesh


def scan_mesh(
    mesh: trimesh.Trimesh,
    name: str,
    formats: tuple[str, ...] = ("stl", "glb", "ply"),
    digits_vertex: int | None = None,
) -> ScanResult:
    result = ScanResult()
    with tempfile.TemporaryDirectory() as directory:
        for fmt in formats:
            path = os.path.join(directory, f"{name}.{fmt}")
            mesh.export(path)

            raw = _load(path, weld=False, digits_vertex=None)
            welded = _load(path, weld=True, digits_vertex=digits_vertex)

            raw_verdict = official_watertight(raw.vertices, raw.faces)
            welded_verdict = official_watertight(welded.vertices, welded.faces)

            result.observations.append(Observation(name, fmt, RAW, raw_verdict))
            result.observations.append(Observation(name, fmt, WELDED, welded_verdict))

            if raw_verdict.watertight != welded_verdict.watertight:
                result.flips.append(
                    Flip(
                        mesh=name,
                        fmt=fmt,
                        from_setting=RAW,
                        to_setting=WELDED,
                        from_watertight=raw_verdict.watertight,
                        to_watertight=welded_verdict.watertight,
                        vertices_before=raw_verdict.vertices,
                        vertices_after=welded_verdict.vertices,
                    )
                )
    return result


def scan_corpus(
    meshes: dict[str, trimesh.Trimesh],
    formats: tuple[str, ...] = ("stl", "glb", "ply"),
    digits_vertex: int | None = None,
) -> ScanResult:
    combined = ScanResult()
    for name, mesh in meshes.items():
        one = scan_mesh(mesh, name, formats=formats, digits_vertex=digits_vertex)
        combined.observations.extend(one.observations)
        combined.flips.extend(one.flips)
    return combined


def ratio_table(result: ScanResult) -> dict[str, dict[str, float]]:
    """Per-format watertight ratio under each setting, plus the gap in percentage points."""
    table: dict[str, dict[str, float]] = {}
    for fmt in result.formats():
        raw = result.ratio(fmt, RAW)
        welded = result.ratio(fmt, WELDED)
        table[fmt] = {
            RAW: raw,
            WELDED: welded,
            "gap_pp": (welded - raw) * 100.0,
        }
    return table


def tolerance_sweep(
    meshes: dict[str, trimesh.Trimesh],
    digits: tuple[int, ...] = (1, 2, 3, 4, 6, 8),
    fmt: str = "stl",
) -> dict[int, float]:
    """Watertight ratio as the weld tolerance varies — the parameter papers omit."""
    sweep: dict[int, float] = {}
    for d in digits:
        result = scan_corpus(meshes, formats=(fmt,), digits_vertex=d)
        sweep[d] = result.ratio(fmt, WELDED)
    return sweep
