from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
import uuid

class EmployeCreation(BaseModel):
    matricule: str
    civilite: Optional[str] = None
    nom: str
    prenom: str
    date_naissance: date
    lieu_naissance: Optional[str] = None
    nationalite: Optional[str] = "Sénégalaise"
    num_cni: Optional[str] = None
    num_securite_sociale: Optional[str] = None
    situation_matrimoniale: Optional[str] = None
    nombre_enfants: Optional[int] = 0
    nombre_parts_fiscales: Optional[float] = 1.0
    adresse_residentielle: str
    ville: Optional[str] = "Dakar"
    quartier: Optional[str] = None
    telephone_perso: Optional[str] = None
    email_perso: Optional[str] = None
    nom_banque: Optional[str] = None
    rib_iban: Optional[str] = None
    poste_id: Optional[uuid.UUID] = None
    departement_id: Optional[uuid.UUID] = None
    date_embauche: date
    salaire_base_contrat: float
    actif: Optional[bool] = True

class EmployeModification(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone_perso: Optional[str] = None
    adresse_residentielle: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    situation_matrimoniale: Optional[str] = None
    nombre_enfants: Optional[int] = None
    nom_banque: Optional[str] = None
    rib_iban: Optional[str] = None
    poste_id: Optional[uuid.UUID] = None
    departement_id: Optional[uuid.UUID] = None
    salaire_base_contrat: Optional[float] = None
    actif: Optional[bool] = None

class PosteReponse(BaseModel):
    id: uuid.UUID
    libelle: str
    class Config:
        from_attributes = True

class DepartementReponse(BaseModel):
    id: uuid.UUID
    nom: str
    class Config:
        from_attributes = True

class EmployeReponse(BaseModel):
    id: uuid.UUID
    matricule: str
    civilite: Optional[str]
    nom: str
    prenom: str
    date_naissance: date
    lieu_naissance: Optional[str]
    nationalite: Optional[str]
    num_cni: Optional[str]
    num_securite_sociale: Optional[str]
    situation_matrimoniale: Optional[str]
    nombre_enfants: Optional[int]
    adresse_residentielle: str
    ville: Optional[str]
    quartier: Optional[str]
    telephone_perso: Optional[str]
    email_perso: Optional[str]
    nom_banque: Optional[str]
    rib_iban: Optional[str]
    poste_id: Optional[uuid.UUID]
    departement_id: Optional[uuid.UUID]
    poste: Optional[PosteReponse]
    departement: Optional[DepartementReponse]
    date_embauche: date
    salaire_base_contrat: float
    actif: bool

    class Config:
        from_attributes = True