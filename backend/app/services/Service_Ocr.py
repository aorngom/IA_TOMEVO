from sqlalchemy.orm import Session
from sqlalchemy import text

def preparer_donnees_formulaire(db: Session, arguments: dict):
    """
    Vérifie les noms de départements et postes et prépare 
    le dictionnaire final pour le formulaire React.
    """
    try:
        # On vérifie si le département existe pour récupérer son UUID
        dep_id = db.execute(
            text("SELECT id FROM departement WHERE nom = :nom"), 
            {"nom": arguments.get("departement")}
        ).scalar()

        # On vérifie si le poste existe pour récupérer son UUID
        poste_id = db.execute(
            text("SELECT id FROM poste WHERE libelle = :libelle"), 
            {"libelle": arguments.get("poste")}
        ).scalar()

        # On renvoie l'objet prêt pour le Frontend
        return {
            "status": "success",
            "data": {
                **arguments,
                "departement_id": str(dep_id) if dep_id else None,
                "poste_id": str(poste_id) if poste_id else None,
                "alerte": False # Sera mis à True si l'IA détecte une incohérence
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}