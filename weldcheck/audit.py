"""Find preprocessing inconsistency inside a repository, by AST rather than grep.

A project is *inconsistent* when its mesh-loading call sites disagree about
vertex welding — typically an evaluation entry point that disables it while the
data pipeline leaves it on. `audit_tree` reports every call site with the weld
setting it requests, so the disagreement is a fact about the code, not a claim.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

LOADERS = {"load", "load_mesh", "load_scene"}
WELD_KEYWORDS = {"process", "merge_vertices", "merge_primitives"}


@dataclass(frozen=True)
class CallSite:
    path: str
    line: int
    callee: str
    welds: bool | None
    """True = welds vertices, False = does not, None = default (trimesh welds by default)."""
    source: str

    @property
    def effective_weld(self) -> bool:
        # trimesh.load(process=...) defaults to True.
        return True if self.welds is None else self.welds


def _literal(node: ast.AST) -> bool | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    return None


class _Visitor(ast.NodeVisitor):
    def __init__(self, path: str, lines: list[str]) -> None:
        self.path = path
        self.lines = lines
        self.sites: list[CallSite] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        name = None
        if isinstance(node.func, ast.Attribute) and node.func.attr in LOADERS:
            name = node.func.attr
        if name is not None and self._is_mesh_loader(node.func):
            welds: bool | None = None
            for kw in node.keywords:
                if kw.arg in WELD_KEYWORDS:
                    value = _literal(kw.value)
                    if value is not None:
                        welds = value
            line = node.lineno
            self.sites.append(
                CallSite(
                    path=self.path,
                    line=line,
                    callee=self._render(node.func),
                    welds=welds,
                    source=self.lines[line - 1].strip() if line <= len(self.lines) else "",
                )
            )
        self.generic_visit(node)

    @staticmethod
    def _is_mesh_loader(func: ast.Attribute) -> bool:
        root = func
        while isinstance(root, ast.Attribute):
            root = root.value
        return isinstance(root, ast.Name) and root.id in {"trimesh", "tm"}

    @staticmethod
    def _render(func: ast.AST) -> str:
        parts: list[str] = []
        while isinstance(func, ast.Attribute):
            parts.append(func.attr)
            func = func.value
        if isinstance(func, ast.Name):
            parts.append(func.id)
        return ".".join(reversed(parts))


def audit_file(path: Path) -> list[CallSite]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
    except SyntaxError:
        return []
    visitor = _Visitor(str(path), text.splitlines())
    visitor.visit(tree)
    return visitor.sites


def audit_tree(root: Path, skip: tuple[str, ...] = (".git", "node_modules", ".venv")) -> list[CallSite]:
    sites: list[CallSite] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in skip for part in path.parts):
            continue
        sites.extend(audit_file(path))
    return sites


def is_inconsistent(sites: list[CallSite]) -> bool:
    """True when the same project both welds and does not weld."""
    settings = {site.effective_weld for site in sites}
    return len(settings) > 1


def summarize(sites: list[CallSite]) -> dict[str, int]:
    welding = sum(site.effective_weld for site in sites)
    return {
        "call_sites": len(sites),
        "welds": welding,
        "does_not_weld": len(sites) - welding,
        "inconsistent": int(is_inconsistent(sites)),
    }
