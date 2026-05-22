"""Probe QTI exporter — verify structure for MC, TF, Essay, and manifest."""
import io
import zipfile

from parser.docx_parser import parse_chapter
from exporters.qti import chapter_to_qti_zip

PATH = (
    "../BOVEE_MS Word_Business Communication Essentials_6Ce/Input/"
    "BOVEE_MS Word_Business Communication Essentials_6Ce/chapter 1.docx"
)

with open(PATH, "rb") as f:
    ch = parse_chapter(f.read())

raw = chapter_to_qti_zip(ch)
z = zipfile.ZipFile(io.BytesIO(raw))
print("ZIP contents:", z.namelist())

xml_name = [n for n in z.namelist() if n.endswith(".xml") and "manifest" not in n][0]
xml = z.read(xml_name).decode("utf-8")
lines = xml.split("\n")
print(f"Question XML: {len(lines)} lines, {len(xml)} bytes")

# First MC item
start = next(i for i, l in enumerate(lines) if "Multiple Choice" in l) - 2
print("\n-- First MC item --")
print("\n".join(lines[start : start + 32]))

# First TF item
start = next(i for i, l in enumerate(lines) if "True False" in l) - 2
print("\n-- First TF item --")
print("\n".join(lines[start : start + 26]))

# First Essay item
start = next(i for i, l in enumerate(lines) if 'fieldentry>Essay' in l) - 2
print("\n-- First Essay item --")
print("\n".join(lines[start : start + 22]))

# imsmanifest.xml
manifest = z.read("imsmanifest.xml").decode("utf-8")
print("\n-- imsmanifest.xml --")
print(manifest)


PATH_CH1 = (
    "../BOVEE_MS Word_Business Communication Essentials_6Ce/Input/"
    "BOVEE_MS Word_Business Communication Essentials_6Ce/chapter 1.docx"
)
PATH_CH2 = (
    "../BOVEE_MS Word_Business Communication Essentials_6Ce/Input/"
    "BOVEE_MS Word_Business Communication Essentials_6Ce/chapter 2.docx"
)

# ── Chapter 1 regression check ────────────────────────────────────────────────
with open(PATH_CH1, "rb") as f:
    ch1 = parse_chapter(f.read())

print(f"Ch1 title: {ch1.title}")
print(f"Ch1 questions: {len(ch1.questions)}")

from collections import Counter
types = Counter(q.q_type for q in ch1.questions)
print(f"Types: {dict(types)}")

# Spot-check MC Q1
for q in ch1.questions:
    if q.q_type == "multichoice":
        print(f"\n[MC] Q{q.number}: {q.stem[:80]}")
        for c in q.choices:
            mark = "  <-- correct" if c.letter == q.correct_letter else ""
            print(f"  {c.letter}) {c.text[:60]}{mark}")
        break

# ── Chapter 2: italic/bold preservation ──────────────────────────────────────
with open(PATH_CH2, "rb") as f:
    ch2 = parse_chapter(f.read())

print(f"\nCh2 questions: {len(ch2.questions)}")

# Q10 should have italic "Bliss"
q10 = ch2.questions[9]
print(f"\nQ10 stem: {q10.stem[:200]}")

# Essay answer with italic
for q in ch2.questions:
    if q.q_type == "essay" and "<i>" in q.model_answer:
        print(f"\nEssay Q{q.number} has italic in answer:")
        print(f"  answer (first 200): {q.model_answer[:200]}")
        break

# ── CDATA in XML output ───────────────────────────────────────────────────────
xml = chapter_to_moodle_xml(ch2)
lines = xml.split("\n")

cdata_lines = [l.strip() for l in lines if "CDATA" in l]
print(f"\nCDATA lines ({len(cdata_lines)} total), first 3:")
for l in cdata_lines[:3]:
    print(f"  {l[:120]}")

italic_lines = [l for l in lines if "<i>" in l]
print(f"\nLines with <i> tags in XML ({len(italic_lines)} total), first 3:")
for l in italic_lines[:3]:
    print(f"  {l.strip()[:120]}")
