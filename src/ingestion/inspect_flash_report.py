from pathlib import Path
import re
import sys

import pymupdf


def inspect_pdf(pdf_path: Path) -> None:
    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    doc = pymupdf.open(pdf_path)
    file_size = pdf_path.stat().st_size
    print("=" * 75)
    print(f"FLASH REPORT SOURCE INSPECTION: {pdf_path.name}")
    print("=" * 75)
    print(f"File path   : {pdf_path}")
    print(f"File size   : {file_size:,} bytes")
    print(f"Total pages : {doc.page_count}")
    print()

    # Search for table of contents or table mentions
    toc_mentions = []
    for idx, page in enumerate(doc):
        text = page.get_text()
        for line in text.splitlines():
            line_s = line.strip()
            if any(k in line_s.lower() for k in ["all ongoing projects", "ongoing projects"]):
                toc_mentions.append((idx + 1, line_s))

    print(f"Mentions of 'Ongoing Projects': {len(toc_mentions)}")
    for page_num, line_text in toc_mentions[:15]:
        print(f"  Page {page_num:3d}: {line_text[:80]}")
    print("=" * 75)


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw/flash_reports/FlashReport_July_2025.pdf")
    inspect_pdf(target)


if __name__ == "__main__":
    main()
