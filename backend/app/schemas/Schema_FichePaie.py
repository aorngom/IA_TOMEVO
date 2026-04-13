from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class EmployeSimple(BaseModel):
    id: uuid.UUID
    matricule: str
    nom: str
    prenom: str
    salaire_base_contrat: float

    class Config:
        from_attributes = True

class FichePaieCreation(BaseModel):
    employe_id: uuid.UUID
    periode_mois: int
    periode_annee: int
    salaire_brut: float
    salaire_net: float

class FichePaieReponse(BaseModel):
    id: uuid.UUID
    employe_id: uuid.UUID
    periode_mois: int
    periode_annee: int
    salaire_brut: float
    salaire_net: float
    date_generation: Optional[datetime]
    employe: Optional[EmployeSimple]

    class Config:
        from_attributes = True