import uuid
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.base_de_donnees import Base

class FichePaie(Base):
    __tablename__ = "fiche_paie"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employe_id = Column(UUID(as_uuid=True), ForeignKey("employe.id", ondelete="CASCADE"))
    
    prenom_employe = Column(String(100), nullable=False)
    nom_employe = Column(String(100), nullable=False)
    
    periode_mois = Column(Integer, nullable=False)
    periode_annee = Column(Integer, nullable=False)
    salaire_brut = Column(Numeric(12, 2))
    salaire_net = Column(Numeric(12, 2))
    date_generation = Column(DateTime(timezone=True), server_default=func.now())

    employe = relationship("Employe", backref="fiches_paie")