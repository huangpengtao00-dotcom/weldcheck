"""The auditor must find a disagreement that really is in the source."""

from pathlib import Path

from weldcheck.audit import audit_file, audit_tree, is_inconsistent, summarize

EVAL_ENTRY = """
import trimesh
mesh = trimesh.load(mesh_file, force='mesh', process=False)
"""

PIPELINE = """
import trimesh
a = trimesh.load(path)
b = trimesh.load(path, process=True)
"""


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "tools" / "evaluation").mkdir(parents=True)
    (tmp_path / "tools" / "evaluation" / "is_watertight.py").write_text(EVAL_ENTRY)
    (tmp_path / "pipeline.py").write_text(PIPELINE)
    return tmp_path


def test_finds_every_loader_call_site(tmp_path):
    sites = audit_tree(_repo(tmp_path))
    assert len(sites) == 3


def test_reports_inconsistency_when_a_repo_does_both(tmp_path):
    sites = audit_tree(_repo(tmp_path))
    assert is_inconsistent(sites)
    stats = summarize(sites)
    assert stats["welds"] == 2
    assert stats["does_not_weld"] == 1


def test_default_counts_as_welding(tmp_path):
    path = tmp_path / "m.py"
    path.write_text("import trimesh\nm = trimesh.load(p)\n")
    site = audit_file(path)[0]
    assert site.welds is None
    assert site.effective_weld is True


def test_consistent_repo_is_not_flagged(tmp_path):
    path = tmp_path / "only.py"
    path.write_text("import trimesh\nm = trimesh.load(p, process=False)\n")
    assert not is_inconsistent(audit_file(path))


def test_ignores_unrelated_load_calls(tmp_path):
    path = tmp_path / "other.py"
    path.write_text("import json\nd = json.load(f)\n")
    assert audit_file(path) == []


def test_survives_a_syntax_error(tmp_path):
    path = tmp_path / "broken.py"
    path.write_text("def (:\n")
    assert audit_file(path) == []
