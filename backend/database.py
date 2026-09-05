import importlib.util

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings

database_url = settings.database_url
# Keep the .env contract on mysql+pymysql while allowing local environments
# that already provide mysql-connector-python to use the same MySQL database.
if database_url.startswith("mysql+pymysql://") and importlib.util.find_spec("pymysql") is None:
    database_url = database_url.replace("mysql+pymysql://", "mysql+mysqlconnector://", 1)

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
