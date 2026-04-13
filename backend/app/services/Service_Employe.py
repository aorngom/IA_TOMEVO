from sqlalchemy.orm import Session, joinedload
from app.models.Model_Employe import Employe
from app.schemas.Schema_Employe import EmployeCreation, EmployeModification
import uuid

def obtenir_tous_employes(db: Session):
    return db.query(Employe).options(
        joinedload(Employe.poste),
        joinedload(Employe.departement)
    ).all()

def obtenir_employe_par_id(db: Session, employe_id: str):
    return db.query(Employe).options(
        joinedload(Employe.poste),
        joinedload(Employe.departement)
    ).filter(Employe.id == employe_id).first()

def creer_employe(db: Session, donnees: EmployeCreation):
    employe = Employe(**donnees.model_dump())
    db.add(employe)
    db.commit()
    db.refresh(employe)
    return db.query(Employe).options(
        joinedload(Employe.poste),
        joinedload(Employe.departement)
    ).filter(Employe.id == employe.id).first()

def modifier_employe(db: Session, employe_id: str, donnees: EmployeModification):
    employe = db.query(Employe).filter(Employe.id == employe_id).first()
    if not employe:
        return None
    for champ, valeur in donnees.model_dump(exclude_unset=True).items():
        setattr(employe, champ, valeur)
    db.commit()
    db.refresh(employe)
    return employe

def supprimer_employe(db: Session, employe_id: str):
    employe = db.query(Employe).filter(Employe.id == employe_id).first()
    if not employe:
        return False
    db.delete(employe)
    db.commit()
    return True