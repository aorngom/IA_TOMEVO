from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

# Ce qu'on reçoit pour le login
class LoginSchema(BaseModel):
    email: EmailStr
    mot_de_passe: str

# Ce qu'on renvoie après login
class UtilisateurReponse(BaseModel):
    id: uuid.UUID
    email: str
    nom: Optional[str]
    prenom: Optional[str]
    role: str

    class Config:
        from_attributes = True

# Token JWT renvoyé
class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    utilisateur: UtilisateurReponse