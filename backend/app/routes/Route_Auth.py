from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.base_de_donnees import get_db
from app.schemas.Schema_Utilisateur import LoginSchema, TokenSchema, UtilisateurReponse
from app.services.Service_Auth import authentifier_utilisateur, creer_token_access

router = APIRouter(tags=["Authentification"])

@router.post("/login", response_model=TokenSchema)
def login(donnees: LoginSchema, db: Session = Depends(get_db)):
    """Endpoint de connexion — retourne un token JWT + infos utilisateur"""
    utilisateur = authentifier_utilisateur(db, donnees.email, donnees.mot_de_passe)
    
    if not utilisateur:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    token = creer_token_access({"sub": str(utilisateur.id), "role": utilisateur.role})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "utilisateur": utilisateur
    }

@router.get("/moi", response_model=UtilisateurReponse)
def moi(db: Session = Depends(get_db)):
    """Route de test — à sécuriser plus tard avec le token"""
    pass