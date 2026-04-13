import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.config.base_de_donnees import Base

class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    mot_de_passe = Column(String, nullable=False)
    nom = Column(String(100))
    prenom = Column(String(100))
    role = Column(String(20), default="client")
    telephone = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())