from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.parametres import parametres

engine = create_engine(parametres.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dépendance à injecter dans les routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()