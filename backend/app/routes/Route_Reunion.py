from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.base_de_donnees import get_db
from app.services.Service_Reunion import (
    obtenir_toutes_reunions,
    obtenir_reunion_par_id,
    creer_reunion,
    modifier_reunion,
    supprimer_reunion,
    confirmer_presence
)
from app.schemas.Schema_Reunion import ReunionCreation, ReunionModification, ReunionReponse
import uuid
 
router = APIRouter(tags=["Réunions"])
 
 
@router.get("/", response_model=list[ReunionReponse])
def liste_reunions(db: Session = Depends(get_db)):
    reunions = obtenir_toutes_reunions(db)
    result = []
    for r in reunions:
        participants_data = []
        for p in r.participants:
            participants_data.append({
                "employe_id": p.employe_id,
                "presence_confirmee": p.presence_confirmee,
                "nom": p.employe.nom if p.employe else None,
                "prenom": p.employe.prenom if p.employe else None,
                "poste": p.employe.poste.libelle if p.employe and p.employe.poste else None,
            })
        result.append({
            "id": r.id,
            "sujet": r.sujet,
            "date_heure": r.date_heure,
            "lieu": r.lieu,
            "ordre_du_jour": r.ordre_du_jour,
            "created_at": r.created_at,
            "participants": participants_data,
        })
    return result
 
 
@router.get("/{reunion_id}", response_model=ReunionReponse)
def detail_reunion(reunion_id: uuid.UUID, db: Session = Depends(get_db)):
    reunion = obtenir_reunion_par_id(db, reunion_id)
    if not reunion:
        raise HTTPException(status_code=404, detail="Réunion non trouvée")
    return reunion
 
 
@router.post("/", response_model=ReunionReponse)
def creer(donnees: ReunionCreation, db: Session = Depends(get_db)):
    return creer_reunion(db, donnees)
 
 
@router.put("/{reunion_id}", response_model=ReunionReponse)
def modifier(reunion_id: uuid.UUID, donnees: ReunionModification, db: Session = Depends(get_db)):
    reunion = modifier_reunion(db, reunion_id, donnees)
    if not reunion:
        raise HTTPException(status_code=404, detail="Réunion non trouvée")
    return reunion
 
 
@router.delete("/{reunion_id}")
def supprimer(reunion_id: uuid.UUID, db: Session = Depends(get_db)):
    ok = supprimer_reunion(db, reunion_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Réunion non trouvée")
    return {"message": "Réunion supprimée avec succès"}
 
 
@router.patch("/{reunion_id}/presence/{employe_id}")
def confirmer(reunion_id: uuid.UUID, employe_id: uuid.UUID, db: Session = Depends(get_db)):
    p = confirmer_presence(db, reunion_id, employe_id)
    if not p:
        raise HTTPException(status_code=404, detail="Participant non trouvé")
    return {"message": "Présence confirmée"}
 