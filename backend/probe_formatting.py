"""Probe DOCX runs for all bold/italic/underline and page-break paragraphs."""
import io
from docx import Document

PATH = (
    "../BOVEE_MS Word_Business Communication Essentials_6Ce/Input/"
    "BOVEE_MS Word_Business Communication Essentials_6Ce/chapter 2.docx"
)

with open(PATH, "rb") as f:
    doc = Document(io.BytesIO(f.read()))

rich_count = 0
for i, para in enumerate(doc.paragraphs):
    t = para.text.strip()
    if not t:
        continue
    pbefore = para.paragraph_format.page_break_before
    has_bold = any(r.bold for r in para.runs)
    has_italic = any(r.italic for r in para.runs)
    has_underline = any(r.underline for r in para.runs)
    has_special = any(c in t for c in ["<", ">", "&"])

    if pbefore or has_bold or has_italic or has_underline or has_special:
        print(f"[{i}] pbreak={pbefore} bold={has_bold} italic={has_italic} underline={has_underline} special_chars={has_special}")
        print(f"  text={t[:120]!r}")
        for r in para.runs:
            if r.text.strip():
                print(f"    run={r.text[:60]!r}  B={r.bold} I={r.italic} U={r.underline}")
        print()
        rich_count += 1
        if rich_count >= 20:
            break

print(f"Total rich paragraphs shown: {rich_count}")
