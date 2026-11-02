"""Record whether a pinned publisher preview contains the Egua-2 article tables."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "data/evidence/wet-co2/obaseki_2023_publisher_preview.pdf"
DEFAULT_OUTPUT = ROOT / "validation/wet_co2_egua_publisher_preview.json"
EXPECTED_SHA256 = "5af16053136ec746e2d2c09f7a4bf63c3b8e0c539cdccab534c5a2bf2a7efeed"
TARGET_DOI = "10.4028/p-brqaI1"
TARGET_TITLE = "Corrosion Rate Prediction in Oil and Gas Pipelines Based on Multiphase Flow Modelling"
FIRST_ARTICLE_DOI = "10.4028/p-E7ehFB"


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def inspect(evidence_path=DEFAULT_EVIDENCE):
    evidence_path = Path(evidence_path)
    digest = _digest(evidence_path)
    if digest != EXPECTED_SHA256:
        raise ValueError("publisher preview hash changed")
    try:
        import pdfplumber
    except ImportError as error:  # pragma: no cover - optional evidence-review dependency
        raise RuntimeError("pdfplumber is required to inspect caller-held PDF evidence") from error

    with pdfplumber.open(evidence_path) as document:
        page_text = [page.extract_text(x_tolerance=2, y_tolerance=3) or "" for page in document.pages]
    if len(page_text) != 12:
        raise ValueError("reviewed publisher preview page count changed")
    target_title_pages = [index for index, text in enumerate(page_text, start=1) if TARGET_TITLE in text]
    target_doi_pages = [index for index, text in enumerate(page_text, start=1) if TARGET_DOI in text]
    first_article_doi_pages = [
        index for index, text in enumerate(page_text, start=1) if FIRST_ARTICLE_DOI in text
    ]
    if target_title_pages != [4] or target_doi_pages or first_article_doi_pages != [5]:
        raise ValueError("publisher preview structure differs from the manually reviewed revision")
    return {
        "schema": "matintegrity.wet_co2_egua_publisher_preview_audit.v1",
        "source_publication_doi": TARGET_DOI,
        "source_publication_title": TARGET_TITLE,
        "publisher_preview_sha256": digest,
        "publisher_preview_bytes": evidence_path.stat().st_size,
        "publisher_preview_pages": len(page_text),
        "target_title_occurrence_pages": target_title_pages,
        "target_doi_occurrence_pages": target_doi_pages,
        "different_first_article_doi_occurrence_pages": first_article_doi_pages,
        "manual_visual_review_pages": [4, 5],
        "manual_visual_review_status": "target_in_contents_then_different_article_body",
        "target_article_body_in_preview": False,
        "target_observation_tables_in_preview": False,
        "source_group_assignment_status": "not_available_from_preview",
        "publication_rights_notice": "publisher_all_rights_reserved",
        "observation_redistribution_status": "not_verified",
        "empirical_calibration_ready": False,
        "mechanistic_calibration_ready": False,
        "public_release_boundary": (
            "Only this metadata audit is public. The publisher preview remains outside distribution."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-pdf", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = inspect(args.evidence_pdf)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
