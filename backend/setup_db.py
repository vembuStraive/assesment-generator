"""
Database setup script for AssessBridge.
Run this script to create the database and tables.

Usage:
    python setup_db.py
"""

from config import settings
from database import engine, database_url
from models import Base


def create_database():
    """Create the assessbridge database if it doesn't exist."""
    try:
        from sqlalchemy import create_engine as sa_create_engine, text

        # Create a connection without specifying the database
        base_url = database_url.replace("/assessbridge", "")
        temp_engine = sa_create_engine(base_url)

        with temp_engine.connect() as conn:
            conn.execute(text("CREATE DATABASE IF NOT EXISTS assessbridge"))
            conn.commit()
        print("✓ Database 'assessbridge' created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return False


def create_tables():
    """Create all tables using SQLAlchemy models."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False


def migrate_existing_tables():
    """Add columns introduced after the initial schema without dropping data."""
    try:
        import re
        from sqlalchemy import inspect, text

        job_columns = {column["name"] for column in inspect(engine).get_columns("conversion_jobs")}
        source_columns = {column["name"] for column in inspect(engine).get_columns("source_files")}
        title_columns = {column["name"] for column in inspect(engine).get_columns("assessment_titles")}
        if "output_content" not in job_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE conversion_jobs ADD COLUMN output_content MEDIUMBLOB NULL"))
            print("✓ Added conversion_jobs.output_content")
        if "content" not in source_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE source_files ADD COLUMN content MEDIUMBLOB NULL"))
            print("✓ Added source_files.content")
        if "short_name" not in title_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE assessment_titles ADD COLUMN short_name VARCHAR(255) NULL"))
                rows = conn.execute(text("SELECT id, owner_id, name FROM assessment_titles ORDER BY id")).mappings().all()
                used = set()
                for row in rows:
                    words = re.findall(r"[A-Za-z0-9]+", row["name"] or "")
                    base = words[0] if len(words) <= 1 and words else ("title" if not words else "".join(word[0] for word in words).upper())
                    candidate = base
                    suffix = 2
                    while (row["owner_id"], candidate.lower()) in used:
                        candidate = f"{base}-{suffix}"
                        suffix += 1
                    used.add((row["owner_id"], candidate.lower()))
                    conn.execute(text("UPDATE assessment_titles SET short_name = :short_name WHERE id = :id"), {"short_name": candidate, "id": row["id"]})
                conn.execute(text("ALTER TABLE assessment_titles MODIFY short_name VARCHAR(255) NOT NULL"))
            print("✓ Added assessment_titles.short_name")

        indexes = {index["name"] for index in inspect(engine).get_indexes("assessment_titles")}
        with engine.begin() as conn:
            if "uq_assessment_titles_owner_name" not in indexes:
                conn.execute(text("CREATE UNIQUE INDEX uq_assessment_titles_owner_name ON assessment_titles (owner_id, name)"))
            if "uq_assessment_titles_owner_short_name" not in indexes:
                conn.execute(text("CREATE UNIQUE INDEX uq_assessment_titles_owner_short_name ON assessment_titles (owner_id, short_name)"))
        return True
    except Exception as e:
        print(f"✗ Error migrating existing tables: {e}")
        return False


if __name__ == "__main__":
    print("Setting up AssessBridge database...")
    print()

    if create_database():
        if create_tables():
            if migrate_existing_tables():
                print()
                print("✓ Database setup completed successfully!")
            else:
                print("✗ Failed to migrate existing tables")
        else:
            print("✗ Failed to create tables")
    else:
        print("✗ Failed to create database")
