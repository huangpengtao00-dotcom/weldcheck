# weldcheck

**A published watertight ratio can depend more on one undocumented preprocessing switch than on the meshes being measured.**

`trimesh.load()` welds duplicate vertices by default. Hunyuan3D-2.1's official
watertightness evaluation script turns that off — `process=False` — while the same
repository's data pipeline leaves it on. Feed STL to the evaluation entry point and it
reports a systematically low watertight rate, no matter how sound the geometry is.

This repository turns that observation into something you can run. Every number below
reproduces from a clean clone with **no model downloads**: the corpus is built
programmatically, so its topology is known by construction.

```bash
uv sync && uv run pytest -q     # 33 passed
uv run weldcheck scan           # the table below
uv run weldcheck rank           # does preprocessing reorder a leaderboard?
uv run weldcheck audit <repo>   # find the same inconsistency in any project
```

## 1. The switch decides the answer, and only for STL

Eight meshes, each exported to three formats and loaded twice — once the way the
evaluation script does it, once the way the pipeline does it. Same meshes, same
predicate, one setting apart:

| format | `process=False` | welded | gap |
|---|---|---|---|
| stl | **0.0 %** | **62.5 %** | **+62.5 pp** |
| glb | 62.5 % | 62.5 % | 0.0 pp |
| ply | 62.5 % | 62.5 % | 0.0 pp |

Five meshes flip. Four of them — a sphere, a box, a torus, a jittered sphere — are
**closed and manifold by construction**. STL stores every triangle's corners
independently, so a sound mesh arrives as a triangle soup: welding recovers 1/6 of the
vertices and the verdict inverts.

This is the part that matters for interpretation. The flip is not evidence that the
models are defective. It is a property of the format and the switch.

## 2. The tolerance is a second unreported parameter

Vertices that were one point upstream can land microns apart after quantization. Then
the verdict depends on how coarse the weld is:

| `digits_vertex` | watertight ratio |
|---|---|
| 1 | 75.0 % |
| 2 | 75.0 % |
| 3 → 8 | 62.5 % |

One mesh in the corpus (`quantized_sphere`) is closed upstream but has corners
displaced by 1e-5. A tolerance of 0.01 welds it and it passes; 0.001 does not and it
fails. Papers reporting these statistics generally name neither the switch nor the
tolerance.

## 3. It reorders leaderboards, not just numbers

A metric whose absolute values drift is a nuisance. A metric whose **ranking** depends
on an undocumented switch cannot compare systems at all. Three synthetic systems, with
geometry quality set deliberately as A > B > C, differing only in delivery format:

| system | `process=False` | welded |
|---|---|---|
| A — best geometry, ships STL | 0.0 % | **100.0 %** |
| B — middling geometry, ships GLB | 66.7 % | 66.7 % |
| C — worst geometry, ships GLB | 33.3 % | 33.3 % |

```
ranking, process=False : B > C > A
ranking, welded        : A > B > C     ← full reversal
```

The soundest system ranks **last** under the evaluation script's own settings, purely
because it delivers STL. Rank 3 → rank 1 when the switch flips.

## 4. Finding the inconsistency in real projects

`weldcheck audit` parses a repository's AST, lists every `trimesh` load site with the
weld setting it requests, and flags a project that does both. Run it on a 3D-generation
codebase and check whether its evaluation entry point agrees with its data pipeline. A
project is only inconsistent if its own source says so — the tool reports call sites,
not opinions.

```
weld   pipeline/postprocess.py:195   mesh = trimesh.load(path)
NOWELD tools/evaluation/is_watertight.py:6   mesh = trimesh.load(f, force='mesh', process=False)
inconsistent preprocessing: True
```

## 5. The predicate's blind spot

`official_watertight` is a faithful transcription of the shipped predicate: no boundary
loops, edge-manifold, vertex-manifold. It pairs edges and never asks whether the surface
passes through itself, so `two_intersecting_boxes` — two interpenetrating cubes — is
reported **watertight**. `tests/test_verdict.py` asserts this blind spot rather than
papering over it, because a mesh can pass the check and still be unusable downstream.

## What this is not

The corpus is eight constructed meshes, chosen to isolate mechanism. It shows that the
switch *can* decide the verdict and *does* reorder a leaderboard; it does not estimate
how often that happens across real generators. Doing that needs a public corpus at
scale (3D Arena, Thingi10K) and is the obvious next step. The ranking experiment uses
synthetic systems: it is an existence proof of reordering, not a measurement of any
real leaderboard.

## Layout

- `weldcheck/verdict.py` — the shipped predicate, transcribed
- `weldcheck/meshes.py` — the corpus, with topology known by construction and the blind spot named
- `weldcheck/sensitivity.py` — format round-trip × weld × tolerance, reported as flips
- `weldcheck/ranking.py` — whether a leaderboard reorders
- `weldcheck/audit.py` — AST audit of a repository's load sites

MIT licensed.

---

More context: [opallagent.com/evidence.html](https://opallagent.com/evidence.html) — How OPALL separates what a number proves from what it does not.
