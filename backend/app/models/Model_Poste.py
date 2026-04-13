import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.config.base_de_donnees import Base

class Poste(Base):
    __tablename__ = "poste"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    libelle = Column(String(100), nullable=False, unique=True)