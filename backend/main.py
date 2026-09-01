"""
AssessBridge Backend — FastAPI application.

Endpoints
---------
GET  /api/health                  → {"status": "ok"}
POST /api/auth/register           → User registration
POST /api/auth/login              → User login
GET  /api/auth/me                 → Get current user
POST /api/convert                 → ZIP of converted XML files (requires auth)

POST /api/convert accepts:
  - files[]   : one or more DOCX files (multipart/form-data)
  - format    : target LMS format ("moodle_xml")

Returns a ZIP file download.
"""

import io
import zipfile
from datetime import datetime

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from parser.docx_parser import parse_chapter
from exporters.blackboard import chapters_to_bb_zip
from exporters.moodle_xml import chapter_to_moodle_xml
from exporters.qti import chapter_to_qti_zip
from database import get_db, engine
from models import Base, User
from auth_routes import router as auth_router
from security import decode_token
from schemas import TokenData

app = FastAPI(title="AssessBridge", version="1.0.0")

# Create database tables
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

SUPPORTED_FORMATS = {"moodle_xml", "qti", "blackboard"}


async def get_current_user(
    authorization: str = Header(None), db: Session = Depends(get_db)
) -> User:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/convert")
async def convert(
    files: list[UploadFile] = File(...),
    format: str = Form(...),
    current_user: User = Depends(get_current_user),
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
