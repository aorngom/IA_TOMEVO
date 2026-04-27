import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.config.base_de_donnees import Base
from datetime import datetime


class Reunion(Base):
    __tablename__ = "reunion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sujet = Column(String(255), nullable=False)
    date_heure = Column(DateTime(timezone=True), nullable=False)
    lieu = Column(String(255), nullable=True)
    ordre_du_jour = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    participants = relationship("ParticipantReunion", back_populates="reunion", cascade="all, delete-orphan")


class ParticipantReunion(Base):
    __tablename__ = "participants_reunion"

    reunion_id = Column(UUID(as_uuid=True), ForeignKey("reunion.id", ondelete="CASCADE"), primary_key=True)
    employe_id = Column(UUID(as_uuid=True), ForeignKey("employe.id", ondelete="CASCADE"), primary_key=True)
    presence_confirmee = Column(Boolean, default=False)

    reunion = relationship("Reunion", back_populates="participants")
    employe = relationship("Employe")