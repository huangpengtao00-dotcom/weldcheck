"""Command line entry points: reproduce the experiment, or audit a repository."""

from __future__ import annotations

import argparse
from pathlib import Path

from .audit import audit_tree, summarize
from .meshes import BUILDERS, KNOWN_SELF_INTERSECTING, build
from .ranking import rank_swap
from .sensitivity import RAW, WELDED, ratio_table, scan_corpus, tolerance_sweep


def _corpus():
    return {name: build(name) for name in BUILDERS}


def cmd_scan(_: argparse.Namespace) -> int:
    result = scan_corpus(_corpus())
    print(f"corpus: {len(BUILDERS)} meshes, known topology by construction")
    print(f"observations: {len(result.observations)}   flips: {len(result.flips)}\n")
    print(f"{'format':8}{RAW:>16}{WELDED:>12}{'gap (pp)':>12}")
    for fmt, row in ratio_table(result).items():
        print(f"{fmt:8}{row[RAW] * 100:15.1f}%{row[WELDED] * 100:11.1f}%{row['gap_pp']:+12.1f}")
    print()
    for flip in result.flips:
        blind = "  (also self-intersecting)" if flip.mesh in KNOWN_SELF_INTERSECTING else ""
        print(
            f"flip  {flip.mesh:30} {flip.fmt:4} "
            f"{flip.from_watertight} -> {flip.to_watertight}   "
            f"vertices retained {flip.vertex_retention:.1%}{blind}"
        )
    return 0


def cmd_tolerance(_: argparse.Namespace) -> int:
    sweep = tolerance_sweep(_corpus())
    print("weld tolerance sweep (STL input)\n")
    print(f"{'digits_vertex':>14}{'watertight ratio':>20}")
    for digits, ratio in sweep.items():
        print(f"{digits:>14}{ratio * 100:19.1f}%")
    return 0


def cmd_rank(_: argparse.Namespace) -> int:
    good = {n: build(n) for n in ("closed_sphere", "closed_box", "closed_torus")}
    mixed = {n: build(n) for n in ("closed_sphere", "closed_box", "open_box")}
    poor = {n: build(n) for n in ("closed_sphere", "open_box", "two_boxes_sharing_a_vertex")}
    result = rank_swap(
        {
            "A (best geometry, ships STL)": ("stl", good),
            "B (middling geometry, ships GLB)": ("glb", mixed),
            "C (worst geometry, ships GLB)": ("glb", poor),
        }
    )
    print(f"{'system':34}{RAW:>16}{WELDED:>12}")
    for score in sorted(result.scores, key=lambda s: -s.welded_ratio):
        print(f"{score.system:34}{score.raw_ratio * 100:15.1f}%{score.welded_ratio * 100:11.1f}%")
    print(f"\nranking, {RAW:<14}: {' > '.join(result.raw_order)}")
    print(f"ranking, {WELDED:<14}: {' > '.join(result.welded_order)}")
    print(f"\nranking swapped: {result.swapped}")
    for name, before, after in result.displaced:
        print(f"  {name}: #{before} -> #{after}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    sites = audit_tree(Path(args.path))
    stats = summarize(sites)
    print(f"repository: {args.path}")
    print(
        f"mesh-loading call sites: {stats['call_sites']}   "
        f"welds: {stats['welds']}   does not weld: {stats['does_not_weld']}"
    )
    print(f"inconsistent preprocessing: {bool(stats['inconsistent'])}\n")
    for site in sites:
        mark = "weld  " if site.effective_weld else "NOWELD"
        print(f"{mark} {site.path}:{site.line}  {site.source[:90]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="weldcheck", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="watertight ratio per format, welded vs not").set_defaults(fn=cmd_scan)
    sub.add_parser("tolerance", help="sweep the weld tolerance").set_defaults(fn=cmd_tolerance)
    sub.add_parser("rank", help="does preprocessing reorder a leaderboard").set_defaults(fn=cmd_rank)
    audit = sub.add_parser("audit", help="find inconsistent mesh preprocessing in a repository")
    audit.add_argument("path")
    audit.set_defaults(fn=cmd_audit)

    args = parser.parse_args(argv)
    return int(args.fn(args))
