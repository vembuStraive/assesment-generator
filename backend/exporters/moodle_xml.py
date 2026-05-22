"""
Moodle XML exporter.

Produces a Moodle-compatible question bank XML file from a Chapter object.
The schema matches Moodle's native GIFT-XML export format (Moodle backup XML v2).
"""

from lxml import etree

from parser.models import Chapter, Question


def _needs_cdata(text: str) -> bool:
    """True when text contains HTML markup, embedded CSS, or special XML/HTML symbols."""
    return bool(text) and ("<" in text or ">" in text or "&" in text)


def _cdata_text(el, content: str) -> None:
    if _needs_cdata(content):
        el.text = etree.CDATA(content)
    else:
        el.text = content


def chapter_to_moodle_xml(chapter: Chapter) -> str:
    """Return a UTF-8 Moodle XML string for the given chapter."""
    root = etree.Element("quiz")

    # ── Category header question ─────────────────────────────────
    cat_q = etree.SubElement(root, "question", type="category")
    cat_node = etree.SubElement(cat_q, "category")
    cat_text = etree.SubElement(cat_node, "text")
    cat_text.text = f"$course$/{chapter.title}"

    # ── Individual questions ──────────────────────────────────────────
    for q in chapter.questions:
        if q.q_type == "multichoice":
            _add_multichoice(root, q)
        elif q.q_type == "truefalse":
            _add_truefalse(root, q)
        else:
            _add_essay(root, q)

    return _pretty_xml(root)


# ─── question builders ────────────────────────────────────────────────────────

def _add_multichoice(parent, q: Question) -> None:
    node = etree.SubElement(parent, "question", type="multichoice")
    _name(node, f"Question {q.number}")
    _questiontext(node, q.stem)
    _generalfeedback(node, "")
    _grade_penalty(node)
    etree.SubElement(node, "single").text = "true"
    etree.SubElement(node, "shuffleanswers").text = "false"
    etree.SubElement(node, "answernumbering").text = "abc"
    _feedback_block(node, "correctfeedback", "")
    _feedback_block(node, "partiallycorrectfeedback", "")
    _feedback_block(node, "incorrectfeedback", "")

    correct = q.correct_letter.upper()
    for choice in q.choices:
        fraction = "100" if choice.letter.upper() == correct else "0"
        ans = etree.SubElement(node, "answer", fraction=fraction, format="html")
        _cdata_text(etree.SubElement(ans, "text"), choice.text)
        fb = etree.SubElement(ans, "feedback", format="html")
        etree.SubElement(fb, "text").text = ""


def _add_truefalse(parent, q: Question) -> None:
    node = etree.SubElement(parent, "question", type="truefalse")
    _name(node, f"Question {q.number}")
    _questiontext(node, q.stem)
    _generalfeedback(node, "")
    _grade_penalty(node)

    correct_is_true = q.correct_letter.upper() == "TRUE"

    for val, label in [("true", correct_is_true), ("false", not correct_is_true)]:
        fraction = "100" if label else "0"
        ans = etree.SubElement(node, "answer", fraction=fraction, format="plain_text")
        etree.SubElement(ans, "text").text = val
        fb = etree.SubElement(ans, "feedback", format="html")
        etree.SubElement(fb, "text").text = ""


def _add_essay(parent, q: Question) -> None:
    node = etree.SubElement(parent, "question", type="essay")
    _name(node, f"Question {q.number}")
    _questiontext(node, q.stem)
    _generalfeedback(node, q.model_answer)
    _grade_penalty(node)
    etree.SubElement(node, "responseformat").text = "editor"
    etree.SubElement(node, "responserequired").text = "1"
    etree.SubElement(node, "responsefieldlines").text = "15"
    etree.SubElement(node, "attachments").text = "0"
    etree.SubElement(node, "attachmentsrequired").text = "0"
    gi = etree.SubElement(node, "graderinfo", format="html")
    etree.SubElement(gi, "text").text = ""
    rt = etree.SubElement(node, "responsetemplate", format="html")
    etree.SubElement(rt, "text").text = ""


# ─── shared helpers ───────────────────────────────────────────────────────────

def _name(parent, label: str) -> None:
    name_el = etree.SubElement(parent, "name")
    etree.SubElement(name_el, "text").text = label


def _questiontext(parent, stem: str) -> None:
    """Always wrap questiontext in CDATA (format=html field)."""
    qt = etree.SubElement(parent, "questiontext", format="html")
    text_el = etree.SubElement(qt, "text")
    text_el.text = etree.CDATA(stem) if stem else ""


def _generalfeedback(parent, content: str) -> None:
    gf = etree.SubElement(parent, "generalfeedback", format="html")
    _cdata_text(etree.SubElement(gf, "text"), content)


def _grade_penalty(parent) -> None:
    etree.SubElement(parent, "defaultgrade").text = "1.0000000"
    etree.SubElement(parent, "penalty").text = "0.0000000"
    etree.SubElement(parent, "hidden").text = "0"


def _feedback_block(parent, tag: str, content: str) -> None:
    fb = etree.SubElement(parent, tag, format="html")
    etree.SubElement(fb, "text").text = content


# ─── XML serialisation ────────────────────────────────────────────────────────

def _pretty_xml(root) -> str:
    """Return indented UTF-8 XML string with XML declaration (via lxml)."""
    raw = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    return raw.decode("utf-8")
