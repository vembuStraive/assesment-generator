"""
AssessBridge Backend — FastAPI application.

Endpoints
---------
GET  /api/health                  → {"status": "ok"}
POST /api/convert                 → ZIP of converted XML files

POST /api/convert accepts:
  - files[]   : one or more DOCX files (multipart/form-data)
  - format    : target LMS format ("moodle_xml")

Returns a ZIP file download.
"""

import io
import zipfile
from datetime import datetime

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from parser.docx_parser import parse_chapter
from exporters.blackboard import chapters_to_bb_zip
from exporters.moodle_xml import chapter_to_moodle_xml
from exporters.qti import chapter_to_qti_zip

app = FastAPI(title="AssessBridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_FORMATS = {"moodle_xml", "qti", "blackboard"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/convert")
async def convert(
    files: list[UploadFile] = File(...),
    format: str = Form(...),
):
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{format}'. Supported: {sorted(SUPPORTED_FORMATS)}",
        )

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── Blackboard: parse all chapters, return a single importable ZIP directly ──
    if format == "blackboard":
        errors: list[str] = []
        bb_chapters = []

        for upload in files:
            if not upload.filename.lower().endswith(".docx"):
                errors.append(f"{upload.filename}: not a .docx file, skipped.")
                continue
            try:
                file_bytes = await upload.read()
                bb_chapters.append(parse_chapter(file_bytes))
            except Exception as exc:
                errors.append(f"{upload.filename}: {exc}")

        if not bb_chapters:
            raise HTTPException(status_code=422, detail="\n".join(errors))

        bb_bytes = chapters_to_bb_zip(bb_chapters)
        filename = f"blackboard_{timestamp}.zip"
        return StreamingResponse(
            io.BytesIO(bb_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # ── All other formats: wrap individual outputs in an outer ZIP ──
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        errors: list[str] = []

        for upload in files:
            if not upload.filename.lower().endswith(".docx"):
                errors.append(f"{upload.filename}: not a .docx file, skipped.")
                continue

            try:
                file_bytes = await upload.read()
                chapter = parse_chapter(file_bytes)

                if format == "moodle_xml":
                    xml_content = chapter_to_moodle_xml(chapter)
                    safe_title = _safe_filename(chapter.title)
                    out_name = f"{safe_title}_moodle.xml"
                    zf.writestr(out_name, xml_content.encode("utf-8"))

                elif format == "qti":
                    qti_bytes = chapter_to_qti_zip(chapter)
                    safe_title = _safe_filename(chapter.title)
                    out_name = f"{safe_title}_qti.zip"
                    zf.writestr(out_name, qti_bytes)

            except Exception as exc:
                errors.append(f"{upload.filename}: {exc}")

        # If every file failed, abort
        if errors and len(errors) == len(files):
            raise HTTPException(status_code=422, detail="\n".join(errors))

        # Write a small error log if some files failed
        if errors:
            zf.writestr("_conversion_errors.txt", "\n".join(errors))

    zip_buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"assessbridge_{format}_{timestamp}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _safe_filename(title: str) -> str:
    """Convert a chapter title to a safe filesystem name."""
    import re
    safe = re.sub(r'[\\/:*?"<>|]', "_", title)
    safe = re.sub(r"\s+", "_", safe)
    return safe[:120]  # cap length
