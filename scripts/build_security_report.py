from __future__ import annotations

from pathlib import Path


def _markdown_to_text(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        line = line.rstrip("\n")
        if line.startswith("#"):
            line = line.lstrip("#").strip()
            out.append(line.upper())
            out.append("")
            continue
        if line.startswith("- "):
            out.append("- " + line[2:])
            continue
        if line.startswith("  "):
            out.append(line.strip())
            continue
        out.append(line)
    return out


def _escape_pdf_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(lines: list[str], out_path: Path) -> None:
    width = 595  # A4
    height = 842
    margin = 72
    font_size = 10
    leading = 14

    pages = []
    current = []
    y = height - margin
    for line in lines:
        if y < margin:
            pages.append(current)
            current = []
            y = height - margin
        current.append((margin, y, line))
        y -= leading
    if current:
        pages.append(current)

    objects = []
    # Object IDs
    catalog_id = 1
    pages_id = 2
    font_id = 3
    next_id = 4

    page_ids = []
    content_ids = []

    for page in pages:
        page_id = next_id
        content_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)
        content_ids.append(content_id)

        # Content stream
        content_lines = ["BT", f"/F1 {font_size} Tf"]
        for x, y, text in page:
            text = _escape_pdf_text(text)
            content_lines.append(f"{x} {y} Td ({text}) Tj")
        content_lines.append("ET")
        content_stream = "\n".join(content_lines).encode("utf-8")
        content_obj = f"<< /Length {len(content_stream)} >>\nstream\n".encode("utf-8") + content_stream + b"\nendstream"
        objects.append((content_id, content_obj))

        # Page object
        page_obj = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {width} {height}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("utf-8")
        objects.append((page_id, page_obj))

    # Pages object
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    pages_obj = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("utf-8")
    objects.append((pages_id, pages_obj))

    # Font object (Helvetica)
    font_obj = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects.append((font_id, font_obj))

    # Catalog object
    catalog_obj = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("utf-8")
    objects.append((catalog_id, catalog_obj))

    # Sort objects by ID
    objects_sorted = sorted(objects, key=lambda x: x[0])

    # Build PDF
    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    offsets = {0: 0}
    for obj_id, obj_body in objects_sorted:
        offsets[obj_id] = len(pdf)
        pdf.extend(f"{obj_id} 0 obj\n".encode("utf-8"))
        pdf.extend(obj_body)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    max_id = max(offsets.keys())
    pdf.extend(f"xref\n0 {max_id + 1}\n".encode("utf-8"))
    pdf.extend(b"0000000000 65535 f \n")
    for i in range(1, max_id + 1):
        off = offsets.get(i, 0)
        pdf.extend(f"{off:010d} 00000 n \n".encode("utf-8"))
    pdf.extend(f"trailer << /Size {max_id + 1} /Root {catalog_id} 0 R >>\n".encode("utf-8"))
    pdf.extend(f"startxref\n{xref_offset}\n%%EOF\n".encode("utf-8"))

    out_path.write_bytes(bytes(pdf))


def main() -> None:
    src = Path("docs/SECURITY_REPORT.md")
    if not src.exists():
        raise SystemExit("docs/SECURITY_REPORT.md not found")
    lines = src.read_text(encoding="utf-8").splitlines()
    excerpts = Path("docs/COMPLIANCE_EXCERPTS.md")
    if excerpts.exists():
        lines.append("")
        lines.append("# Compliance Appendix — Excerpts")
        lines.append("")
        lines.extend(excerpts.read_text(encoding="utf-8").splitlines())
    plain = _markdown_to_text(lines)
    out = Path("docs/SECURITY_REPORT.pdf")
    _build_pdf(plain, out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
