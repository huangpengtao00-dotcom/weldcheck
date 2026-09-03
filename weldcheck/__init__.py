"""weldcheck — measure how much a mesh-topology statistic depends on preprocessing."""

from .audit import audit_tree, is_inconsistent, summarize
from .meshes import BUILDERS, KNOWN_CLOSED_MANIFOLD, KNOWN_SELF_INTERSECTING, build
from .ranking import rank_swap
from .sensitivity import RAW, WELDED, ratio_table, scan_corpus, scan_mesh, tolerance_sweep
from .verdict import Verdict, official_watertight

__all__ = [
    "BUILDERS",
    "KNOWN_CLOSED_MANIFOLD",
    "KNOWN_SELF_INTERSECTING",
    "RAW",
    "WELDED",
    "Verdict",
    "audit_tree",
    "build",
    "is_inconsistent",
    "official_watertight",
    "rank_swap",
    "ratio_table",
    "scan_corpus",
    "scan_mesh",
    "summarize",
    "tolerance_sweep",
]
