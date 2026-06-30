from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.base_de_donnees import get_db
from app.services.Service_Paie import (
    obtenir_toutes_fiches,
    obtenir_fiche_par_id,
    obtenir_fiches_par_employe,
    creer_fiche,
    supprimer_fiche
)
from app.schemas.Schema_FichePaie import FichePaieCreation, FichePaieReponse

router = APIRouter(tags=["Paie"])

@router.get("/", response_model=list[FichePaieReponse])
def liste_fiches(db: Session = Depends(get_db)):
    return obtenir_toutes_fiches(db)

@router.get("/{fiche_id}", response_model=FichePaieReponse)
def detail_fiche(fiche_id: str, db: Session = Depends(get_db)):
    fiche = obtenir_fiche_par_id(db, fiche_id)
    if not fiche:
        raise HTTPException(status_code=404, detail="Fiche de paie non trouvée")
    return fiche

@router.get("/employe/{employe_id}", response_model=list[FichePaieReponse])
def fiches_par_employe(employe_id: str, db: Session = Depends(get_db)):
    return obtenir_fiches_par_employe(db, employe_id)

from app.services.Service_PaieIA import calculer_salaire_complet, sauvegarder_fiche_calculee

@router.post("/", response_model=FichePaieReponse)
def creer(donnees: FichePaieCreation, db: Session = Depends(get_db)):
    try:
        calcul = calculer_salaire_complet(
            db,
            str(donnees.employe_id),
            donnees.periode_mois,
            donnees.periode_annee
        )
        fiche_id = sauvegarder_fiche_calculee(db, calcul)
        return obtenir_fiche_par_id(db, fiche_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{fiche_id}")
def supprimer(fiche_id: str, db: Session = Depends(get_db)):
    ok = supprimer_fiche(db, fiche_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Fiche non trouvée")
    return {"message": "Fiche supprimée avec succès"}