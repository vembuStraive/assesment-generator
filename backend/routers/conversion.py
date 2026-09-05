import io
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import AssessmentTitle, SourceFile, User
from services.conversion import convert_files

router = APIRouter(prefix="/api", tags=["conversion"])


@router.post("/convert")
async def convert(files: list[UploadFile] = File(default=[]), format: str = Form(...), title_id: int = Form(...), source_file_ids: str = Form("[]"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    title = db.query(AssessmentTitle).filter(AssessmentTitle.id == title_id, AssessmentTitle.owner_id == current_user.id).first()
    if title is None:
        raise HTTPException(status_code=404, detail="Title not found")
    try:
        requested_ids = [int(item) for item in json.loads(source_file_ids)]
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid source file selection") from exc
    existing_files = db.query(SourceFile).filter(SourceFile.title_id == title_id, SourceFile.id.in_(requested_ids)).all() if requested_ids else []
    if len(existing_files) != len(set(requested_ids)):
        raise HTTPException(status_code=404, detail="One or more source files were not found")
    filename, content = await convert_files(files, format, title, current_user, db, existing_files)
    return StreamingResponse(io.BytesIO(content), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
