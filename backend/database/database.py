from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base


DATABASE_URL = "sqlite:///studentos.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    )

sessionlocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
    )

def create_database():
    Base.metadata.create_all(bind=engine)