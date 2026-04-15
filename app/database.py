from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_PUBLIC_URL = os.getenv("DATABASE_PUBLIC_URL")

DATABASE_PUBLIC_URL = os.getenv("DATABASE_PUBLIC_URL")
assert DATABASE_PUBLIC_URL, "DATABASE_PUBLIC_URL is not set"

engine = create_engine(DATABASE_PUBLIC_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()