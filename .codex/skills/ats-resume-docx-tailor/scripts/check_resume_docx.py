#!/usr/bin/env python3
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from docx import Document


BAD_MARKERS = ("[TODO", "TODO", "TBD", "[Company", "[Role", "[DEGREE", "[MONTH")
CORE_MARKERS = ("EUNWHA PARK", "linkedin.com/", "github.com/")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: check_resume_docx.py <resume.docx> [keyword ...]", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    keywords = sys.argv[2:]
    if not path.exists():
        print(f"ERROR missing file: {path}", file=sys.stderr)
        return 2

    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)

    errors: list[str] = []
    for marker in CORE_MARKERS:
        if marker not in text:
            errors.append(f"missing core marker: {marker}")
    for marker in BAD_MARKERS:
        if marker in text:
            errors.append(f"placeholder marker remains: {marker}")

    with zipfile.ZipFile(path) as zf:
        rel_text = "\n".join(
            zf.read(name).decode("utf-8", "ignore")
            for name in zf.namelist()
            if name.endswith(".rels")
        )
    hyperlink_count = rel_text.count("hyperlink")
    if hyperlink_count < 2:
        errors.append(f"expected at least 2 hyperlinks, found {hyperlink_count}")

    for keyword in keywords:
        if keyword.lower() not in text.lower():
            errors.append(f"missing keyword: {keyword}")

    print(f"file: {path}")
    print(f"paragraphs: {len(paragraphs)}")
    print(f"characters: {len(text)}")
    print(f"hyperlinks: {hyperlink_count}")
    if keywords:
        print(f"keywords_checked: {len(keywords)}")

    if errors:
        print("status: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("status: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
