from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class ParticipantReponse(BaseModel):
    employe_id: uuid.UUID
    presence_confirmee: bool
    nom: Optional[str] = None
    prenom: Optional[str] = None
    poste: Optional[str] = None

    class Config:
        from_attributes = True


class ReunionCreation(BaseModel):
    sujet: str
    date_heure: datetime
    lieu: Optional[str] = None
    ordre_du_jour: Optional[str] = None
    employe_ids: List[uuid.UUID] = []


class ReunionModification(BaseModel):
    sujet: Optional[str] = None
    date_heure: Optional[datetime] = None
    lieu: Optional[str] = None
    ordre_du_jour: Optional[str] = None
    employe_ids: Optional[List[uuid.UUID]] = None


class ReunionReponse(BaseModel):
    id: uuid.UUID
    sujet: str
    date_heure: datetime
    lieu: Optional[str] = None
    ordre_du_jour: Optional[str] = None
    created_at: datetime
    participants: List[ParticipantReponse] = []

    class Config:
        from_attributes = True