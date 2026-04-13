import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.config.base_de_donnees import Base

class Employe(Base):
    __tablename__ = "employe"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    utilisateur_id = Column(UUID(as_uuid=True), ForeignKey("utilisateur.id"), nullable=True)
    matricule = Column(String(50), unique=True, nullable=False)
    civilite = Column(String(10))
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    date_naissance = Column(Date, nullable=False)
    lieu_naissance = Column(String(100))
    nationalite = Column(String(50), default="Sénégalaise")
    num_cni = Column(String(50))
    num_securite_sociale = Column(String(50))
    situation_matrimoniale = Column(String(50))
    nombre_enfants = Column(Integer, default=0)
    nombre_parts_fiscales = Column(Numeric(3, 1), default=1.0)
    adresse_residentielle = Column(Text, nullable=False)
    ville = Column(String(100), default="Dakar")
    quartier = Column(String(100))
    telephone_perso = Column(String(20))
    email_perso = Column(String(255))
    nom_banque = Column(String(100))
    rib_iban = Column(String(100))
    poste_id = Column(UUID(as_uuid=True), ForeignKey("poste.id"))
    departement_id = Column(UUID(as_uuid=True), ForeignKey("departement.id"))
    date_embauche = Column(Date, nullable=False)
    salaire_base_contrat = Column(Numeric(12, 2), nullable=False)
    actif = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    poste = relationship("Poste", backref="employes")
    departement = relationship("Departement", backref="employes")