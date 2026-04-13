from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.Model_Utilisateur import Utilisateur
from app.config.parametres import parametres

# Configuration du hachage de mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verifier_mot_de_passe(mot_de_passe_brut: str, mot_de_passe_hache: str) -> bool:
    """Vérifie si le mot de passe correspond au hash en BDD"""
    return pwd_context.verify(mot_de_passe_brut, mot_de_passe_hache)

def obtenir_utilisateur_par_email(db: Session, email: str) -> Utilisateur | None:
    """Récupère un utilisateur depuis la BDD par son email"""
    return db.query(Utilisateur).filter(Utilisateur.email == email).first()

def authentifier_utilisateur(db: Session, email: str, mot_de_passe: str) -> Utilisateur | None:
    """Authentifie l'utilisateur et retourne l'objet ou None"""
    utilisateur = obtenir_utilisateur_par_email(db, email)
    if not utilisateur:
        return None
    if not verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe):
        return None
    return utilisateur

def creer_token_access(data: dict) -> str:
    """Crée un token JWT signé"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=parametres.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, parametres.SECRET_KEY, algorithm=parametres.ALGORITHM)