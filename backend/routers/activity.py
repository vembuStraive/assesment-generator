from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import io

from database import get_db
from dependencies import get_current_user
from models import AssessmentTitle, ConversionJob, ConversionJobFile, Download, User
from schemas import ConversionActivityResponse, DownloadResponse

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("/conversions", response_model=list[ConversionActivityResponse])
def list_conversions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(ConversionJob, AssessmentTitle.name, func.count(ConversionJobFile.id))
        .join(AssessmentTitle, AssessmentTitle.id == ConversionJob.title_id)
        .outerjoin(ConversionJobFile, ConversionJobFile.job_id == ConversionJob.id)
        .filter(ConversionJob.owner_id == current_user.id)
        .group_by(ConversionJob.id, AssessmentTitle.name)
        .order_by(ConversionJob.created_at.desc())
        .all()
    )
    return [_conversion_response(job, title_name, file_count) for job, title_name, file_count in rows]


@router.get("/downloads", response_model=list[DownloadResponse])
def list_downloads(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Download, AssessmentTitle.name, ConversionJob.output_format)
        .join(ConversionJob, ConversionJob.id == Download.job_id)
        .join(AssessmentTitle, AssessmentTitle.id == ConversionJob.title_id)
        .filter(Download.owner_id == current_user.id)
        .order_by(Download.downloaded_at.desc())
        .all()
    )
    return [DownloadResponse(id=item.id, job_id=item.job_id, title_name=title_name, filename=item.filename, output_format=output_format, downloaded_at=item.downloaded_at) for item, title_name, output_format in rows]


@router.get("/downloads/{download_id}/file")
def download_file(download_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Download).filter(Download.id == download_id, Download.owner_id == current_user.id).first()
    if item is None or item.job.output_content is None:
        raise HTTPException(status_code=404, detail="Download not found")
    return StreamingResponse(io.BytesIO(item.job.output_content), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{item.filename}"'})


def _conversion_response(job, title_name, file_count):
    return ConversionActivityResponse(id=job.id, title_id=job.title_id, title_name=title_name, output_format=job.output_format, status=job.status, output_filename=job.output_filename, file_count=file_count, created_at=job.created_at, completed_at=job.completed_at)
