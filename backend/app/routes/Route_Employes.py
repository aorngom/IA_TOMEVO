from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.base_de_donnees import get_db
from app.services.Service_Employe import (
    obtenir_tous_employes,
    obtenir_employe_par_id,
    creer_employe,
    modifier_employe,
    supprimer_employe
)
from app.schemas.Schema_Employe import EmployeCreation, EmployeReponse, EmployeModification
from app.models.Model_Poste import Poste
from app.models.Model_Departement import Departement
from app.schemas.Schema_Employe import PosteReponse, DepartementReponse


router = APIRouter(tags=["Employés"])

@router.get("/", response_model=list[EmployeReponse])
def liste_employes(db: Session = Depends(get_db)):
    return obtenir_tous_employes(db)

@router.get("/{employe_id}", response_model=EmployeReponse)
def detail_employe(employe_id: str, db: Session = Depends(get_db)):
    employe = obtenir_employe_par_id(db, employe_id)
    if not employe:
        raise HTTPException(status_code=404, detail="Employé non trouvé")
    return employe

@router.post("/", response_model=EmployeReponse)
def ajouter_employe(donnees: EmployeCreation, db: Session = Depends(get_db)):
    return creer_employe(db, donnees)

@router.put("/{employe_id}", response_model=EmployeReponse)
def modifier(employe_id: str, donnees: EmployeModification, db: Session = Depends(get_db)):
    employe = modifier_employe(db, employe_id, donnees)
    if not employe:
        raise HTTPException(status_code=404, detail="Employé non trouvé")
    return employe

@router.delete("/{employe_id}")
def supprimer(employe_id: str, db: Session = Depends(get_db)):
    ok = supprimer_employe(db, employe_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Employé non trouvé")
    return {"message": "Employé supprimé avec succès"}
@router.get("/postes/liste", response_model=list[PosteReponse])
def liste_postes(db: Session = Depends(get_db)):
    return db.query(Poste).all()

@router.get("/departements/liste", response_model=list[DepartementReponse])
def liste_departements(db: Session = Depends(get_db)):
    return db.query(Departement).all()