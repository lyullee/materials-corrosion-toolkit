from scripts.audit_public_source_boundary import audit_public_source_boundary
from scripts.build_release import ROOT, public_files


def test_public_source_allowlist_excludes_private_roots_and_binary_documents():
    files = public_files()
    forbidden_roots = {"raw", "derived", "evidence", "artifacts", "tmp"}
    forbidden_suffixes = {".pdf", ".opju", ".xlsx", ".xlsm", ".h5", ".mat", ".zip"}
    for path in files:
        relative = path.relative_to(ROOT)
        assert forbidden_roots.isdisjoint(relative.parts)
        assert path.suffix.lower() not in forbidden_suffixes


def test_public_source_boundary_audit_is_explicitly_not_legal_clearance():
    report = audit_public_source_boundary()
    assert report["status"] == "passed"
    assert report["file_count"] > 0
    assert "not legal clearance" in report["meaning"]
