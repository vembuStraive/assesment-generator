"""
Database setup script for AssessBridge.
Run this script to create the database and tables.

Usage:
    python setup_db.py
"""

import pymysql
from config import settings
from database import engine
from models import Base


def create_database():
    """Create the assessbridge database if it doesn't exist."""
    try:
        from sqlalchemy import create_engine as sa_create_engine, text

        # Create a connection without specifying the database
        base_url = settings.database_url.replace("/assessbridge", "")
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


if __name__ == "__main__":
    print("Setting up AssessBridge database...")
    print()

    if create_database():
        if create_tables():
            print()
            print("✓ Database setup completed successfully!")
        else:
            print("✗ Failed to create tables")
    else:
        print("✗ Failed to create database")
