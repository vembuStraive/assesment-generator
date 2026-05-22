"""
IMS QTI 1.2 exporter.

Produces a per-chapter ZIP containing:
  - imsmanifest.xml     IMS Content Packaging 1.1.2 manifest
  - <safe_title>.xml    QTI 1.2 question-bank XML

Compatible with Blackboard, D2L, and generic QTI 1.2 importers.
"""

import io
import re
import zipfile

from lxml import etree

from parser.models import Chapter, Question

_CP_NS = "http://www.imsproject.org/xsd/imscp_rootv1p1p2"
_XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


def chapter_to_qti_zip(chapter: Chapter) -> bytes:
    """Return raw bytes of a QTI 1.2 ZIP for *chapter*."""
    safe = _safe_name(chapter.title)
    xml_filename = f"{safe}.xml"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(xml_filename, _build_questions_xml(chapter).encode("utf-8"))
        zf.writestr("imsmanifest.xml", _build_manifest_xml(chapter, xml_filename).encode("utf-8"))
    return buf.getvalue()


def _safe_name(title: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", title)
    safe = re.sub(r"\s+", "_", safe)
    return safe.strip()[:100]


# ─── question XML ─────────────────────────────────────────────────────────────────────────────────

def _build_questions_xml(chapter: Chapter) -> str:
    root = etree.Element("questestinterop")
    assessment = etree.SubElement(
        root, "assessment",
        ident=f"ch{chapter.number:02d}",
        title=chapter.title,
    )
    section = etree.SubElement(assessment, "section", ident="main")

    for q in chapter.questions:
        if q.q_type == "multichoice":
            _add_mc_item(section, q)
        elif q.q_type == "truefalse":
            _add_tf_item(section, q)
        else:
            _add_essay_item(section, q)

    return _pretty_xml(root)


def _add_mc_item(parent, q: Question) -> None:
    item = etree.SubElement(parent, "item", ident=f"q{q.number}", title=f"Question {q.number}")
    _item_metadata(item, "Multiple Choice")

    pres = etree.SubElement(item, "presentation")
    _stem_material(pres, q.stem)

    resp = etree.SubElement(pres, "response_lid", ident="response", rcardinality="Single")
    render = etree.SubElement(resp, "render_choice", shuffle="No")

    for choice in q.choices:
        lbl = etree.SubElement(render, "response_label", ident=choice.letter.upper())
        _content_material(lbl, choice.text)

    _resprocessing(item, "response", q.correct_letter.upper())


def _add_tf_item(parent, q: Question) -> None:
    item = etree.SubElement(parent, "item", ident=f"q{q.number}", title=f"Question {q.number}")
    _item_metadata(item, "True False")

    pres = etree.SubElement(item, "presentation")
    _stem_material(pres, q.stem)

    resp = etree.SubElement(pres, "response_lid", ident="response", rcardinality="Single")
    render = etree.SubElement(resp, "render_choice", shuffle="No")

    for ident, label in [("True", "True"), ("False", "False")]:
        lbl = etree.SubElement(render, "response_label", ident=ident)
        mat = etree.SubElement(lbl, "material")
        etree.SubElement(mat, "mattext").text = label

    correct = "True" if q.correct_letter.upper() == "TRUE" else "False"
    _resprocessing(item, "response", correct)


def _add_essay_item(parent, q: Question) -> None:
    item = etree.SubElement(parent, "item", ident=f"q{q.number}", title=f"Question {q.number}")
    _item_metadata(item, "Essay")

    pres = etree.SubElement(item, "presentation")
    _stem_material(pres, q.stem)

    resp = etree.SubElement(pres, "response_str", ident="response", rcardinality="Single")
    etree.SubElement(resp, "render_fib", rows="15", columns="80", fibtype="String")

    if q.model_answer:
        fb = etree.SubElement(item, "itemfeedback", ident="solution", view="Instructor")
        flow = etree.SubElement(fb, "flow_mat")
        _content_material(flow, q.model_answer)


# ─── shared helpers ─────────────────────────────────────────────────────────────────────────

def _item_metadata(item, item_type: str) -> None:
    meta = etree.SubElement(item, "itemmetadata")
    qmeta = etree.SubElement(meta, "qtimetadata")
    field = etree.SubElement(qmeta, "qtimetadatafield")
    etree.SubElement(field, "fieldlabel").text = "qmd_itemtype"
    etree.SubElement(field, "fieldentry").text = item_type


def _stem_material(parent, stem: str) -> None:
    mat = etree.SubElement(parent, "material")
    _mattext_el(mat, stem)


def _content_material(parent, text: str) -> None:
    mat = etree.SubElement(parent, "material")
    _mattext_el(mat, text)


def _needs_cdata(text: str) -> bool:
    """True when text contains HTML markup, embedded CSS, or special XML/HTML symbols."""
    return bool(text) and ("<" in text or ">" in text or "&" in text)


def _mattext_el(parent, text: str) -> None:
    mt = etree.SubElement(parent, "mattext")
    mt.set("texttype", "text/html")
    if _needs_cdata(text):
        mt.text = etree.CDATA(text)
    else:
        mt.text = text or ""


def _resprocessing(item, resp_ident: str, correct_ident: str) -> None:
    rp = etree.SubElement(item, "resprocessing")

    outcomes = etree.SubElement(rp, "outcomes")
    decvar = etree.SubElement(outcomes, "decvar")
    decvar.set("varname", "SCORE")
    decvar.set("vartype", "Decimal")
    decvar.set("defaultval", "0")
    decvar.set("minvalue", "0")
    decvar.set("maxvalue", "1")

    cond = etree.SubElement(rp, "respcondition")
    cond.set("continue", "No")  # "continue" is a Python keyword — use .set()
    condvar = etree.SubElement(cond, "conditionvar")
    varequal = etree.SubElement(condvar, "varequal", respident=resp_ident)
    varequal.text = correct_ident
    setvar = etree.SubElement(cond, "setvar", varname="SCORE", action="Set")
    setvar.text = "1"


# ─── manifest XML ─────────────────────────────────────────────────────────────────────────────

def _build_manifest_xml(chapter: Chapter, xml_filename: str) -> str:
    NS = _CP_NS

    root = etree.Element(
        f"{{{NS}}}manifest",
        nsmap={None: NS, "xsi": _XSI_NS},
    )
    root.set("identifier", f"ch{chapter.number:02d}_manifest")
    root.set(
        f"{{{_XSI_NS}}}schemaLocation",
        f"{NS} http://www.imsproject.org/xsd/imscp_rootv1p1p2.xsd",
    )

    meta = etree.SubElement(root, f"{{{NS}}}metadata")
    etree.SubElement(meta, f"{{{NS}}}schema").text = "IMS Content"
    etree.SubElement(meta, f"{{{NS}}}schemaversion").text = "1.1.2"

    etree.SubElement(root, f"{{{NS}}}organizations")

    resources = etree.SubElement(root, f"{{{NS}}}resources")
    res = etree.SubElement(resources, f"{{{NS}}}resource")
    res.set("identifier", f"ch{chapter.number:02d}_resource")
    res.set("type", "imsqti_xmlv1p2")
    res.set("href", xml_filename)
    etree.SubElement(res, f"{{{NS}}}file").set("href", xml_filename)

    return _pretty_xml(root)


def _pretty_xml(root) -> str:
    raw = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    return raw.decode("utf-8")
