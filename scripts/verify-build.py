#!/usr/bin/env python3
"""Check the PDF, page size, fonts, and unresolved references before publishing."""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    output = Path(sys.argv[1])
    pdf = output / "main.pdf"
    data = pdf.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF")
    log = (output / "main.log").read_text(encoding="utf-8", errors="replace")
    for pattern in (r"LaTeX Warning: There were undefined references",
                    r"LaTeX Warning: Label .* multiply defined",
                    r"Missing character:"):
        if re.search(pattern, log):
            raise ValueError("Unresolved references or missing characters: " + pattern)
    fonts = (output / "fonts.txt").read_text(encoding="utf-8").splitlines()[2:]
    if not fonts or any(row.split()[-5] != "yes" for row in fonts if row.strip()):
        raise ValueError("PDF contains fonts that are not embedded")
    if not any("HaranoAji" in row for row in fonts):
        raise ValueError("Japanese fonts are missing")
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    match = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
    if not match or any(abs(float(actual) - expected) > 1 for actual, expected in zip(match.groups(), (595.276, 841.890))):
        raise ValueError("PDF page size must be A4")
    metadata = {
        "commit": os.environ["COMMIT"],
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tex": subprocess.check_output(["lualatex", "--version"], text=True).splitlines()[0],
        "toolchain": "Ubuntu 24.04 / TeX Live (apt)",
        "fonts": sorted({row.split()[0] for row in fonts if row.strip()}),
        "pdfs": {"a4": {"sha256": hashlib.sha256(data).hexdigest()}},
    }
    (output / "build-info.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
