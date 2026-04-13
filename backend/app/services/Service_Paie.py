from sqlalchemy.orm import Session, joinedload
from app.models.Model_FichePaie import FichePaie
from app.models.Model_Employe import Employe  # Ajout nécessaire pour récupérer l'employé
from app.schemas.Schema_FichePaie import FichePaieCreation

def obtenir_toutes_fiches(db: Session):
    return db.query(FichePaie).options(
        joinedload(FichePaie.employe)
    ).order_by(FichePaie.periode_annee.desc(), FichePaie.periode_mois.desc()).all()

def obtenir_fiche_par_id(db: Session, fiche_id: str):
    return db.query(FichePaie).options(
        joinedload(FichePaie.employe)
    ).filter(FichePaie.id == fiche_id).first()

def obtenir_fiches_par_employe(db: Session, employe_id: str):
    return db.query(FichePaie).options(
        joinedload(FichePaie.employe)
    ).filter(FichePaie.employe_id == employe_id).order_by(
        FichePaie.periode_annee.desc(),
        FichePaie.periode_mois.desc()
    ).all()

def creer_fiche(db: Session, donnees: FichePaieCreation):
    # 1. Récupérer l'employé pour avoir ses infos de nom/prénom
    employe = db.query(Employe).filter(Employe.id == donnees.employe_id).first()
    
    # 2. Préparer les données en ajoutant le nom et le prénom récupérés
    infos_fiche = donnees.model_dump()
    if employe:
        infos_fiche["nom_employe"] = employe.nom
        infos_fiche["prenom_employe"] = employe.prenom
    
    # 3. Création de la fiche avec les champs obligatoires remplis
    fiche = FichePaie(**infos_fiche)
    db.add(fiche)
    db.commit()
    db.refresh(fiche)
    
    return db.query(FichePaie).options(
        joinedload(FichePaie.employe)
    ).filter(FichePaie.id == fiche.id).first()

def supprimer_fiche(db: Session, fiche_id: str):
    fiche = db.query(FichePaie).filter(FichePaie.id == fiche_id).first()
    if not fiche:
        return False
    db.delete(fiche)
    db.commit()
    return True