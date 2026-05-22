"""
Blackboard QTI exporter.

Produces a Blackboard-compatible uploadable ZIP from a Chapter object.
The ZIP mirrors Blackboard's native export format:

  .bb-package-sig      MD5 hex digest of the .dat file
  imsmanifest.xml      Blackboard CP manifest
  res00001.dat         Blackboard QTI XML for the chapter
"""

import hashlib
import io
import random
import uuid
import zipfile

from lxml import etree

from parser.models import Chapter, Question

_BB_NS = "http://www.blackboard.com/content-packaging/"
_XML_NS = "http://www.w3.org/XML/1998/namespace"


def chapter_to_bb_zip(chapter: Chapter) -> bytes:
    """Return raw bytes of a Blackboard-importable ZIP for a single chapter."""
    return chapters_to_bb_zip([chapter])


def chapters_to_bb_zip(chapters: list[Chapter]) -> bytes:
    """Return raw bytes of a Blackboard-importable ZIP for one or more chapters.

    Produces:
      .bb-package-sig               MD5 of the first dat file
      imsmanifest.xml               manifest listing all dat resources
      res00001.dat … res0000N.dat   one QTI dat per chapter
      res0000(N+1).dat              ASSESSMENTCREATIONSETTINGS for all chapters
    """
    dat_entries: list[tuple[str, bytes, str]] = []  # (filename, content, assessment_id)

    for i, chapter in enumerate(chapters, start=1):
        dat_xml, assessment_id = _build_dat_xml(chapter)
        dat_bytes = dat_xml.encode("utf-8")
        dat_entries.append((f"res{i:05d}.dat", dat_bytes, assessment_id))

    settings_idx = len(dat_entries) + 1
    settings_filename = f"res{settings_idx:05d}.dat"
    assessment_ids = [e[2] for e in dat_entries]
    settings_content = _build_settings_xml(assessment_ids).encode("utf-8")

    manifest_content = _build_manifest_xml_multi(
        [(fn, ch.title) for (fn, _, _), ch in zip(dat_entries, chapters)],
        settings_filename,
    ).encode("utf-8")

    sig = hashlib.md5(dat_entries[0][1]).hexdigest().upper()

    package_info = _build_package_info()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(".bb-package-info", package_info)
        zf.writestr(".bb-package-sig", sig)
        zf.writestr("imsmanifest.xml", manifest_content)
        for fn, content, _ in dat_entries:
            zf.writestr(fn, content)
        zf.writestr(settings_filename, settings_content)
    return buf.getvalue()


# ─── package info ─────────────────────────────────────────────────────────────

def _build_package_info() -> str:
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%a %b %d %H:%M:%S UTC %Y")
    return (
        "#Bb PackageInfo Property File\n"
        f"#{ts}\n"
        "app.release.number=3900.0.0-rel.1+0\n"
        "cx.config.operation=blackboard.apps.cx.CxConfig$Operation\\:IMPORT\n"
        "cx.package.info.version=6.0\n"
    )


# ─── manifest ────────────────────────────────────────────────────────────────

def _build_manifest_xml_multi(
    chapter_entries: list[tuple[str, str]],  # (filename, title) per chapter
    settings_filename: str,
) -> str:
    root = etree.Element("manifest", identifier="man00001", nsmap={"bb": _BB_NS})
    etree.SubElement(root, "organizations")
    resources = etree.SubElement(root, "resources")
    for filename, title in chapter_entries:
        ident = filename.replace(".dat", "")
        res = etree.SubElement(resources, "resource")
        res.set(f"{{{_BB_NS}}}file", filename)
        res.set(f"{{{_BB_NS}}}title", title)
        res.set("identifier", ident)
        res.set("type", "assessment/x-bb-qti-test")
        res.set(f"{{{_XML_NS}}}base", ident)
    settings_ident = settings_filename.replace(".dat", "")
    sr = etree.SubElement(resources, "resource")
    sr.set(f"{{{_BB_NS}}}file", settings_filename)
    sr.set(f"{{{_BB_NS}}}title", "Assessment Creation Settings")
    sr.set("identifier", settings_ident)
    sr.set("type", "course/x-bb-courseassessmentcreationsettings")
    sr.set(f"{{{_XML_NS}}}base", settings_ident)
    return _minified_xml(root)


# ─── settings dat ─────────────────────────────────────────────────────────────

def _build_settings_xml(assessment_ids: list[str]) -> str:
    root = etree.Element("ASSESSMENTCREATIONSETTINGS")
    setting_base = random.randint(10000, 89999)
    for i, assessment_id in enumerate(assessment_ids):
        setting_id = f"_{setting_base + i}_1"
        s = etree.SubElement(root, "ASSESSMENTCREATIONSETTING", id=setting_id)
        etree.SubElement(s, "QTIASSESSMENTID", value=assessment_id)
        for tag in (
            "ANSWERFEEDBACKENABLED",
            "QUESTIONATTACHMENTSENABLED",
            "ANSWERATTACHMENTSENABLED",
            "QUESTIONMETADATAENABLED",
            "DEFAULTPOINTVALUEENABLED",
        ):
            etree.SubElement(s, tag).text = "true"
        etree.SubElement(s, "DEFAULTPOINTVALUE").text = "10.00000"
        for tag in (
            "ANSWERPARTIALCREDITENABLED",
            "ANSWERNEGATIVEPOINTSENABLED",
            "ANSWERRANDOMORDERENABLED",
            "ANSWERORIENTATIONENABLED",
            "ANSWERNUMBEROPTIONSENABLED",
            "USEPOINTSFROMSOURCEBYDEFAULT",
        ):
            etree.SubElement(s, tag).text = "true"
    return _minified_xml(root)


# ─── dat XML ─────────────────────────────────────────────────────────────────

def _build_dat_xml(chapter: Chapter) -> tuple[str, str]:
    """Return (xml_string, assessment_obj_id)."""
    _base = [random.randint(100000, 899999)]

    def _next_id() -> str:
        val = _base[0]
        _base[0] += 1
        return f"_{val}_1"

    root = etree.Element("questestinterop")
    score_max = float(len(chapter.questions))
    assessment = etree.SubElement(root, "assessment", title=chapter.title)
    assessment_obj_id = _next_id()
    _assessment_metadata(assessment, score_max, assessment_obj_id)
    _empty_block_mat(etree.SubElement(assessment, "rubric", view="All"))
    _empty_block_mat(etree.SubElement(assessment, "presentation_material"))

    section = etree.SubElement(assessment, "section")
    _section_metadata(section, score_max, _next_id())

    for q in chapter.questions:
        if q.q_type == "multichoice":
            _add_mc_item(section, q, _next_id())
        elif q.q_type == "truefalse":
            _add_tf_item(section, q, _next_id())
        else:
            _add_essay_item(section, q, _next_id())

    return _minified_xml(root), assessment_obj_id


# ─── metadata builders ───────────────────────────────────────────────────────

def _assessment_metadata(assessment, score_max: float, obj_id: str) -> None:
    meta = etree.SubElement(assessment, "assessmentmetadata")
    etree.SubElement(meta, "bbmd_asi_object_id").text = obj_id
    for tag, val in [
        ("bbmd_asitype",            "Assessment"),
        ("bbmd_assessmenttype",     "Test"),
        ("bbmd_sectiontype",        "Subsection"),
        ("bbmd_questiontype",       "Multiple Choice"),
        ("bbmd_is_from_cartridge",  "false"),
        ("bbmd_is_disabled",        "false"),
        ("bbmd_negative_points_ind","N"),
        ("bbmd_canvas_fullcrdt_ind","false"),
        ("bbmd_all_fullcredit_ind", "false"),
        ("bbmd_numbertype",         "none"),
    ]:
        etree.SubElement(meta, tag).text = val
    etree.SubElement(meta, "bbmd_partialcredit")
    for tag, val in [
        ("bbmd_orientationtype",    "vertical"),
        ("bbmd_is_extracredit",     "false"),
        ("bbmd_ai_state",           "No"),
    ]:
        etree.SubElement(meta, tag).text = val
    etree.SubElement(meta, "qmd_absolutescore_max").text = f"{score_max:.15f}"
    etree.SubElement(meta, "qmd_weighting").text = "0"
    etree.SubElement(meta, "qmd_instructornotes")


def _section_metadata(section, score_max: float, obj_id: str) -> None:
    meta = etree.SubElement(section, "sectionmetadata")
    etree.SubElement(meta, "bbmd_asi_object_id").text = obj_id
    for tag, val in [
        ("bbmd_asitype",            "Section"),
        ("bbmd_assessmenttype",     "Test"),
        ("bbmd_sectiontype",        "Subsection"),
        ("bbmd_questiontype",       "Multiple Choice"),
        ("bbmd_is_from_cartridge",  "false"),
        ("bbmd_is_disabled",        "false"),
        ("bbmd_negative_points_ind","N"),
        ("bbmd_canvas_fullcrdt_ind","false"),
        ("bbmd_all_fullcredit_ind", "false"),
        ("bbmd_numbertype",         "none"),
    ]:
        etree.SubElement(meta, tag).text = val
    etree.SubElement(meta, "bbmd_partialcredit")
    for tag, val in [
        ("bbmd_orientationtype",    "vertical"),
        ("bbmd_is_extracredit",     "false"),
        ("bbmd_ai_state",           "No"),
    ]:
        etree.SubElement(meta, tag).text = val
    etree.SubElement(meta, "qmd_absolutescore_max").text = f"{score_max:.15f}"
    etree.SubElement(meta, "qmd_weighting").text = "0"
    etree.SubElement(meta, "qmd_instructornotes")


def _item_metadata(item, question_type: str, obj_id: str) -> None:
    meta = etree.SubElement(item, "itemmetadata")
    etree.SubElement(meta, "bbmd_asi_object_id").text = obj_id
    for tag, val in [
        ("bbmd_asitype",            "Item"),
        ("bbmd_assessmenttype",     "Test"),
        ("bbmd_sectiontype",        "Subsection"),
        ("bbmd_questiontype",       question_type),
        ("bbmd_is_from_cartridge",  "false"),
        ("bbmd_is_disabled",        "false"),
        ("bbmd_negative_points_ind","N"),
        ("bbmd_canvas_fullcrdt_ind","false"),
        ("bbmd_all_fullcredit_ind", "false"),
        ("bbmd_numbertype",         "none"),
    ]:
        etree.SubElement(meta, tag).text = val
    etree.SubElement(meta, "bbmd_partialcredit")
    for tag, val in [
        ("bbmd_orientationtype",    "vertical"),
        ("bbmd_is_extracredit",     "false"),
        ("bbmd_ai_state",           "No"),
    ]:
        etree.SubElement(meta, tag).text = val
    etree.SubElement(meta, "qmd_absolutescore_max").text = "1.000000000000000"
    etree.SubElement(meta, "qmd_weighting").text = "0"
    etree.SubElement(meta, "qmd_instructornotes")


# ─── item builders ────────────────────────────────────────────────────────────

def _add_mc_item(parent, q: Question, obj_id: str) -> None:
    item = etree.SubElement(parent, "item", maxattempts="0")
    _item_metadata(item, "Multiple Choice", obj_id)

    pres = etree.SubElement(item, "presentation")
    outer = etree.SubElement(pres, "flow", **{"class": "Block"})
    q_flow = etree.SubElement(outer, "flow", **{"class": "QUESTION_BLOCK"})
    _bb_material(etree.SubElement(q_flow, "flow", **{"class": "FORMATTED_TEXT_BLOCK"}), q.stem)

    r_flow = etree.SubElement(outer, "flow", **{"class": "RESPONSE_BLOCK"})
    resp = etree.SubElement(r_flow, "response_lid", ident="response", rcardinality="Single", rtiming="No")
    render = etree.SubElement(resp, "render_choice", shuffle="No", minnumber="0", maxnumber="0")

    correct = q.correct_letter.upper()
    correct_ident = None
    choice_idents: list[str] = []

    for choice in q.choices:
        ident = uuid.uuid4().hex.upper()
        choice_idents.append(ident)
        if choice.letter.upper() == correct:
            correct_ident = ident

        fl = etree.SubElement(render, "flow_label", **{"class": "Block"})
        rl = etree.SubElement(fl, "response_label", ident=ident, shuffle="Yes", rarea="Ellipse", rrange="Exact")
        _bb_material(etree.SubElement(rl, "flow_mat", **{"class": "FORMATTED_TEXT_BLOCK"}), choice.text)

    _scored_resprocessing(item, correct_ident or "")
    _feedback_pair(item)

    for ident in choice_idents:
        _solution_feedback(item, ident, "", smart_text=True)


def _add_tf_item(parent, q: Question, obj_id: str) -> None:
    item = etree.SubElement(parent, "item", maxattempts="0")
    _item_metadata(item, "True/False", obj_id)

    pres = etree.SubElement(item, "presentation")
    outer = etree.SubElement(pres, "flow", **{"class": "Block"})
    q_flow = etree.SubElement(outer, "flow", **{"class": "QUESTION_BLOCK"})
    _bb_material(etree.SubElement(q_flow, "flow", **{"class": "FORMATTED_TEXT_BLOCK"}), q.stem)

    r_flow = etree.SubElement(outer, "flow", **{"class": "RESPONSE_BLOCK"})
    resp = etree.SubElement(r_flow, "response_lid", ident="response", rcardinality="Single", rtiming="No")
    render = etree.SubElement(resp, "render_choice", shuffle="No", minnumber="0", maxnumber="0")

    fl = etree.SubElement(render, "flow_label", **{"class": "Block"})
    for val in ("true", "false"):
        rl = etree.SubElement(fl, "response_label", ident=val, shuffle="Yes", rarea="Ellipse", rrange="Exact")
        fm = etree.SubElement(rl, "flow_mat", **{"class": "Block"})
        mat = etree.SubElement(fm, "material")
        mt = etree.SubElement(mat, "mattext", charset="us-ascii", texttype="text/plain")
        mt.set(f"{{{_XML_NS}}}space", "default")
        mt.text = val

    correct = "true" if q.correct_letter.upper() == "TRUE" else "false"
    _scored_resprocessing(item, correct)
    _feedback_pair(item)


def _add_essay_item(parent, q: Question, obj_id: str) -> None:
    item = etree.SubElement(parent, "item", maxattempts="0")
    _item_metadata(item, "Essay", obj_id)

    pres = etree.SubElement(item, "presentation")
    outer = etree.SubElement(pres, "flow", **{"class": "Block"})
    q_flow = etree.SubElement(outer, "flow", **{"class": "QUESTION_BLOCK"})
    _bb_material(etree.SubElement(q_flow, "flow", **{"class": "FORMATTED_TEXT_BLOCK"}), q.stem)

    r_flow = etree.SubElement(outer, "flow", **{"class": "RESPONSE_BLOCK"})
    resp = etree.SubElement(r_flow, "response_str", ident="response", rcardinality="Single", rtiming="No")
    etree.SubElement(
        resp, "render_fib",
        charset="us-ascii", encoding="UTF_8", rows="8", columns="127",
        maxchars="0", prompt="Box", fibtype="String", minnumber="0", maxnumber="0",
    )

    _essay_resprocessing(item)
    _feedback_pair(item)

    # Always emit solution feedback — Blackboard calls getAnswerTextMaterial()
    # on every essay item and crashes with NPE if the block is absent.
    _solution_feedback(item, "solution", q.model_answer or "", smart_text=False)


# ─── resprocessing helpers ────────────────────────────────────────────────────

def _scored_resprocessing(item, correct_ident: str) -> None:
    """MC / TF: mark the matching response as correct, everything else incorrect."""
    rp = etree.SubElement(item, "resprocessing", scoremodel="SumOfScores")
    outcomes = etree.SubElement(rp, "outcomes")
    etree.SubElement(
        outcomes, "decvar",
        varname="SCORE", vartype="Decimal", defaultval="0.0", minvalue="0.0", maxvalue="1.00",
    )

    cond_c = etree.SubElement(rp, "respcondition", title="correct")
    cv = etree.SubElement(cond_c, "conditionvar")
    ve = etree.SubElement(cv, "varequal", respident="response")
    ve.set("case", "No")
    ve.text = correct_ident
    etree.SubElement(cond_c, "setvar", variablename="SCORE", action="Set").text = "SCORE.max"
    etree.SubElement(cond_c, "displayfeedback", linkrefid="correct", feedbacktype="Response")

    cond_i = etree.SubElement(rp, "respcondition", title="incorrect")
    etree.SubElement(etree.SubElement(cond_i, "conditionvar"), "other")
    etree.SubElement(cond_i, "setvar", variablename="SCORE", action="Set").text = "0.0"
    etree.SubElement(cond_i, "displayfeedback", linkrefid="incorrect", feedbacktype="Response")


def _essay_resprocessing(item) -> None:
    """Essay: no conditionvar for the correct case — graded manually."""
    rp = etree.SubElement(item, "resprocessing", scoremodel="SumOfScores")
    outcomes = etree.SubElement(rp, "outcomes")
    etree.SubElement(
        outcomes, "decvar",
        varname="SCORE", vartype="Decimal", defaultval="0.0", minvalue="0.0", maxvalue="1.00",
    )

    cond_c = etree.SubElement(rp, "respcondition", title="correct")
    etree.SubElement(cond_c, "conditionvar")
    etree.SubElement(cond_c, "setvar", variablename="SCORE", action="Set").text = "SCORE.max"
    etree.SubElement(cond_c, "displayfeedback", linkrefid="correct", feedbacktype="Response")

    cond_i = etree.SubElement(rp, "respcondition", title="incorrect")
    etree.SubElement(etree.SubElement(cond_i, "conditionvar"), "other")
    etree.SubElement(cond_i, "setvar", variablename="SCORE", action="Set").text = "0.0"
    etree.SubElement(cond_i, "displayfeedback", linkrefid="incorrect", feedbacktype="Response")


# ─── feedback helpers ─────────────────────────────────────────────────────────

def _feedback_pair(item) -> None:
    """Empty correct/incorrect itemfeedback (required by Blackboard)."""
    for ident in ("correct", "incorrect"):
        fb = etree.SubElement(item, "itemfeedback", ident=ident, view="All")
        fm = etree.SubElement(fb, "flow_mat", **{"class": "Block"})
        fm2 = etree.SubElement(fm, "flow_mat", **{"class": "FORMATTED_TEXT_BLOCK"})
        mat = etree.SubElement(fm2, "material")
        etree.SubElement(etree.SubElement(mat, "mat_extension"), "mat_formattedtext", type="SMART_TEXT")


def _solution_feedback(item, ident: str, text: str, *, smart_text: bool) -> None:
    """itemfeedback with solution/solutionmaterial content."""
    fb = etree.SubElement(item, "itemfeedback", ident=ident, view="All")
    sol = etree.SubElement(fb, "solution", view="All", feedbackstyle="Complete")
    sol_mat = etree.SubElement(sol, "solutionmaterial")
    fm = etree.SubElement(sol_mat, "flow_mat", **{"class": "Block"})
    if smart_text:
        fm2 = etree.SubElement(fm, "flow_mat", **{"class": "FORMATTED_TEXT_BLOCK"})
        mat = etree.SubElement(fm2, "material")
        ext = etree.SubElement(mat, "mat_extension")
        etree.SubElement(ext, "mat_formattedtext", type="SMART_TEXT")
    else:
        mat = etree.SubElement(fm, "material")
        ext = etree.SubElement(mat, "mat_extension")
        ft = etree.SubElement(ext, "mat_formattedtext", type="HTML")
        ft.text = text or ""


# ─── material helper ──────────────────────────────────────────────────────────

def _bb_material(parent, text: str) -> None:
    """Append <material><mat_extension><mat_formattedtext type="HTML">text to parent."""
    mat = etree.SubElement(parent, "material")
    ext = etree.SubElement(mat, "mat_extension")
    ft = etree.SubElement(ext, "mat_formattedtext", type="HTML")
    ft.text = text or ""


def _empty_block_mat(parent) -> None:
    """Empty flow_mat block (used for rubric / presentation_material)."""
    fm = etree.SubElement(parent, "flow_mat", **{"class": "Block"})
    mat = etree.SubElement(fm, "material")
    etree.SubElement(etree.SubElement(mat, "mat_extension"), "mat_formattedtext", type="HTML")


# ─── XML serialisation ────────────────────────────────────────────────────────

def _minified_xml(root) -> str:
    # Serialize without declaration, then prepend with double-quoted declaration
    # (lxml uses single quotes which some BB parsers reject)
    body = etree.tostring(root, pretty_print=False, xml_declaration=False, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>' + body
