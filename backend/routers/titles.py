import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import AssessmentTitle, User
from schemas import SourceFileResponse, TitleCreate, TitleResponse
from models import SourceFile

router = APIRouter(prefix="/api/titles", tags=["titles"])


def _short_name(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name)
    if len(words) <= 1:
        return words[0] if words else "title"
    return "".join(word[0] for word in words).upper()


def _available_short_name(db: Session, owner_id: int, name: str) -> str:
    candidate = _short_name(name)
    base = candidate
    number = 2
    while db.query(AssessmentTitle).filter(
        AssessmentTitle.owner_id == owner_id,
        AssessmentTitle.short_name == candidate,
    ).first() is not None:
        candidate = f"{base}-{number}"
        number += 1
    return candidate


@router.get("", response_model=list[TitleResponse])
def list_titles(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(AssessmentTitle).filter(AssessmentTitle.owner_id == current_user.id).order_by(AssessmentTitle.updated_at.desc()).all()


@router.post("", response_model=TitleResponse, status_code=status.HTTP_201_CREATED)
def create_title(title_data: TitleCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = title_data.name.strip()
    if db.query(AssessmentTitle).filter(
        AssessmentTitle.owner_id == current_user.id,
        func.lower(AssessmentTitle.name) == name.lower(),
    ).first() is not None:
        raise HTTPException(status_code=409, detail="A title with this name already exists.")
    title = AssessmentTitle(owner_id=current_user.id, name=name, short_name=_available_short_name(db, current_user.id, name), description=title_data.description.strip() if title_data.description else None)
    db.add(title)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A title with this name already exists.") from exc
    db.refresh(title)
    return title


@router.delete("/{title_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_title(title_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    title = db.query(AssessmentTitle).filter(AssessmentTitle.id == title_id, AssessmentTitle.owner_id == current_user.id).first()
    if title is None:
        raise HTTPException(status_code=404, detail="Title not found")
    db.delete(title)
    db.commit()


@router.get("/{title_id}/files", response_model=list[SourceFileResponse])
def list_title_files(title_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    title = db.query(AssessmentTitle).filter(AssessmentTitle.id == title_id, AssessmentTitle.owner_id == current_user.id).first()
    if title is None:
        raise HTTPException(status_code=404, detail="Title not found")
    return db.query(SourceFile).filter(SourceFile.title_id == title_id).order_by(SourceFile.created_at.desc()).all()
