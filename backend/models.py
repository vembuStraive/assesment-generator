from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, ForeignKey, Text, Index, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    titles = relationship("AssessmentTitle", back_populates="owner", cascade="all, delete-orphan")
    conversion_jobs = relationship("ConversionJob", back_populates="owner", cascade="all, delete-orphan")
    downloads = relationship("Download", back_populates="owner", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class AssessmentTitle(Base):
    """A user's assessment workspace/title."""

    __tablename__ = "assessment_titles"
    __table_args__ = (
        Index("ix_assessment_titles_owner_updated", "owner_id", "updated_at"),
        Index("uq_assessment_titles_owner_name", "owner_id", "name", unique=True),
        Index("uq_assessment_titles_owner_short_name", "owner_id", "short_name", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    short_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="titles")
    source_files = relationship("SourceFile", back_populates="title", cascade="all, delete-orphan")
    conversion_jobs = relationship("ConversionJob", back_populates="title", cascade="all, delete-orphan")


class SourceFile(Base):
    """Uploaded source-file metadata; binary content lives in configured storage."""

    __tablename__ = "source_files"
    __table_args__ = (
        Index("ix_source_files_title_created", "title_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title_id = Column(Integer, ForeignKey("assessment_titles.id", ondelete="CASCADE"), nullable=False, index=True)
    original_name = Column(String(255), nullable=False)
    storage_key = Column(String(512), nullable=False, unique=True)
    content_type = Column(String(128), nullable=False, default="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    size_bytes = Column(BigInteger, nullable=False)
    checksum = Column(String(128), nullable=True)
    content = Column(LargeBinary(length=16_777_215), nullable=False)
    status = Column(String(32), nullable=False, default="ready")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    title = relationship("AssessmentTitle", back_populates="source_files")
    job_links = relationship("ConversionJobFile", back_populates="source_file", cascade="all, delete-orphan")


class ConversionJob(Base):
    """One requested conversion, including its lifecycle and generated output."""

    __tablename__ = "conversion_jobs"
    __table_args__ = (
        Index("ix_conversion_jobs_owner_created", "owner_id", "created_at"),
        Index("ix_conversion_jobs_title_created", "title_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title_id = Column(Integer, ForeignKey("assessment_titles.id", ondelete="CASCADE"), nullable=False, index=True)
    output_format = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="queued")
    output_filename = Column(String(255), nullable=True)
    output_storage_key = Column(String(512), nullable=True)
    output_content = Column(LargeBinary(length=16_777_215), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="conversion_jobs")
    title = relationship("AssessmentTitle", back_populates="conversion_jobs")
    files = relationship("ConversionJobFile", back_populates="job", cascade="all, delete-orphan")
    downloads = relationship("Download", back_populates="job", cascade="all, delete-orphan")


class ConversionJobFile(Base):
    """Join table recording which uploaded files were included in a job."""

    __tablename__ = "conversion_job_files"
    __table_args__ = (
        Index("ix_conversion_job_files_job_file", "job_id", "source_file_id", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("conversion_jobs.id", ondelete="CASCADE"), nullable=False)
    source_file_id = Column(Integer, ForeignKey("source_files.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("ConversionJob", back_populates="files")
    source_file = relationship("SourceFile", back_populates="job_links")


class Download(Base):
    """Download events for generated conversion packages."""

    __tablename__ = "downloads"
    __table_args__ = (
        Index("ix_downloads_owner_downloaded", "owner_id", "downloaded_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("conversion_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    downloaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("ConversionJob", back_populates="downloads")
    owner = relationship("User", back_populates="downloads")


class UserPreference(Base):
    """Per-user defaults used by the settings screen and conversion form."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    default_output_format = Column(String(32), nullable=False, default="moodle_xml")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="preferences")
