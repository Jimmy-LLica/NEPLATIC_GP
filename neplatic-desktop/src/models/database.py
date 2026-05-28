from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

from src.utils.config import settings

engine = create_engine(settings.get_connection_url(), echo=os.getenv("SQL_ECHO", "false").lower() == "true")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()