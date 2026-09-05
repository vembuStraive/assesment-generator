import io
import re
import zipfile
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from exporters.blackboard import chapters_to_bb_zip
from exporters.moodle_xml import chapter_to_moodle_xml
from exporters.qti import chapter_to_qti_zip
from models import AssessmentTitle, ConversionJob, ConversionJobFile, Download, SourceFile, User
from parser.docx_parser import parse_chapter

SUPPORTED_FORMATS = {"moodle_xml", "qti", "blackboard"}


class StoredUpload:
    def __init__(self, source_file):
        self.filename = source_file.original_name
        self.content_type = source_file.content_type
        self.source_file = source_file
        self._content = source_file.content

    async def read(self):
        return self._content


async def convert_files(files: list[UploadFile], output_format: str, title: AssessmentTitle, user: User, db: Session, existing_files=None) -> tuple[str, bytes]:
    if output_format not in SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{output_format}'. Supported: {sorted(SUPPORTED_FORMATS)}")
    files = list(files) + [StoredUpload(source) for source in (existing_files or [])]
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    job = ConversionJob(owner_id=user.id, title_id=title.id, output_format=output_format, status="processing", started_at=datetime.utcnow())
    db.add(job)
    db.commit()
    db.refresh(job)
    try:
        content = await _convert_blackboard(files, title, job, db) if output_format == "blackboard" else await _convert_archive(files, output_format, title, job, db)
        filename = _output_filename(files, output_format, title)
        _complete_job(db, job, filename, content)
        return filename, content
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail="Conversion failed. Please try again.") from exc


async def _convert_blackboard(files, title, job, db) -> bytes:
    errors, chapters = [], []
    for upload in files:
        if not (upload.filename or "").lower().endswith(".docx"):
            errors.append(f"{upload.filename}: not a .docx file, skipped.")
            continue
        try:
            file_bytes = await upload.read()
            _save_source_file(db, title, upload, file_bytes, job)
            chapters.append(parse_chapter(file_bytes))
        except Exception as exc:
            db.rollback()
            errors.append(f"{upload.filename}: {exc}")
    if not chapters:
        _fail_job(db, job, errors)
        raise HTTPException(status_code=422, detail="\n".join(errors))
    return chapters_to_bb_zip(chapters)


async def _convert_archive(files, output_format, title, job, db) -> bytes:
    errors = []
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for upload in files:
            if not (upload.filename or "").lower().endswith(".docx"):
                errors.append(f"{upload.filename}: not a .docx file, skipped.")
                continue
            try:
                file_bytes = await upload.read()
                _save_source_file(db, title, upload, file_bytes, job)
                chapter = parse_chapter(file_bytes)
                safe_title = _safe_filename(chapter.title)
                if output_format == "moodle_xml":
                    archive.writestr(f"{safe_title}_moodle.xml", chapter_to_moodle_xml(chapter).encode("utf-8"))
                else:
                    archive.writestr(f"{safe_title}_qti.zip", chapter_to_qti_zip(chapter))
            except Exception as exc:
                db.rollback()
                errors.append(f"{upload.filename}: {exc}")
        if errors and len(errors) == len(files):
            _fail_job(db, job, errors)
            raise HTTPException(status_code=422, detail="\n".join(errors))
        if errors:
            archive.writestr("_conversion_errors.txt", "\n".join(errors))
    return zip_buffer.getvalue()


def _save_source_file(db: Session, title, upload, content, job):
    if getattr(upload, "source_file", None) is not None:
        job.files.append(ConversionJobFile(source_file=upload.source_file))
        return
    source_file = SourceFile(title_id=title.id, original_name=upload.filename or "uploaded.docx", storage_key=f"db://source/{uuid4()}", content_type=upload.content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document", size_bytes=len(content), content=content)
    db.add(source_file)
    db.flush()
    job.files.append(ConversionJobFile(source_file=source_file))


def _complete_job(db, job, filename, content):
    job.status = "completed"
    job.output_filename = filename
    job.output_storage_key = f"db://output/{uuid4()}"
    job.output_content = content
    job.completed_at = datetime.utcnow()
    db.add(Download(owner_id=job.owner_id, job=job, filename=filename))
    db.commit()


def _fail_job(db, job, errors):
    job.status = "failed"
    job.error_message = "\n".join(errors)
    job.completed_at = datetime.utcnow()
    db.commit()


def _safe_filename(title: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", title)
    return re.sub(r"\s+", "_", safe)[:120]


def _output_filename(files, output_format: str, title: AssessmentTitle) -> str:
    """Return a predictable package name based on the selected source files."""
    file_count = len(files)
    if file_count > 1:
        return f"{_safe_filename(title.short_name)}.zip"

    source_name = files[0].filename if files else title.name
    source_base = re.sub(r"\.[^.]+$", "", source_name or title.name)
    suffix = "blackboard" if output_format == "blackboard" else output_format
    return f"{_safe_filename(title.short_name)}_{_safe_filename(source_base)}_{suffix}.zip"
