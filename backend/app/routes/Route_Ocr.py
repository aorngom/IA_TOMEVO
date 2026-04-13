from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.config.base_de_donnees import get_db
from sqlalchemy.orm import Session
from app.models.Model_Employe import Employe
from app.models.Model_FichePaie import FichePaie
from typing import List, Optional
import httpx
import os
import base64

router = APIRouter(tags=["OCR / IA"])

# Modèles de données (Identiques)
class Message(BaseModel):
    role: str
    content: str

class ChatPayload(BaseModel):
    messages: List[Message]
    contexte: Optional[str] = ""

@router.post("/chat")
async def chat_document(payload: ChatPayload, db: Session = Depends(get_db)): 
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="La clé API Groq est absente du serveur.")

    #  LOGIQUE BDD : On récupère les infos nécessaires

#  RÉCUPÉRATION DES DONNÉES COMPLÈTES (Employés + Paie)
    try:
        # 1. On récupère tous les employés avec leurs détails
        employes = db.query(Employe).all()
        details_employes = []
        for e in employes:
            details_employes.append(
                f"ID: {e.matricule} | Nom: {e.prenom} {e.nom} | "
                f"Poste: {e.poste_id} | Salaire Base: {e.salaire_base_contrat} FCFA | "
                f"Banque: {e.nom_banque} | Situation: {e.situation_matrimoniale} ({e.nombre_enfants} enfants)"
            )
        
        # 2. On récupère les fiches de paie
        fiches = db.query(FichePaie).all()
        details_paie = []
        for f in fiches:
            # On cherche le nom de l'employé correspondant pour que l'IA fasse le lien
            emp = next((e for e in employes if e.id == f.employe_id), None)
            nom_emp = f"{emp.prenom} {emp.nom}" if emp else "Inconnu"
            
            details_paie.append(
                f"Fiche de {nom_emp} | Période: {f.periode_mois}/{f.periode_annee} | "
                f"Brut: {f.salaire_brut} | Net: {f.salaire_net}"
            )

        # 3. On fusionne tout en texte
        infos_bdd = (
            "LISTE DES EMPLOYÉS : " + " ; ".join(details_employes) + 
            " | HISTORIQUE DES PAIES : " + " ; ".join(details_paie)
        )

    except Exception as e:
        print(f"Erreur lecture BDD : {str(e)}")
        infos_bdd = "Information BDD indisponible (Vérifiez les imports des modèles Employe et FichePaie)"

    # On fusionne le contexte du Front + les infos de la BDD
    system_prompt = (
        f"Tu es l'intelligence de gestion centrale de Jariniou. Écoute bien ces consignes comme si tu étais à l'école :\n\n"
        f"1. ANALYSE MULTIMODALE : Tu es capable d'analyser des images de documents (fiches de paie, factures, contrats) transmises sous format visuel. "
        f"Ton rôle est d'extraire avec précision les données textuelles et numériques de ces images pour les traiter.\n\n"
        f"2. NE PARLE PAS TROP : Si l'utilisateur te dit juste 'Bonjour' ou 'Salut', réponds simplement et poliment par une phrase courte. "
        f"NE DONNE JAMAIS les informations de la base de données ou du document tant qu'on ne t'a pas posé une question précise sur eux.\n\n"
        f"3. ATTENDS LES ORDRES : Ton savoir est secret. Tu ne dois sortir les tableaux et les chiffres que si on te demande une analyse, "
        f"un calcul ou une vérification de document.\n\n"
        f"4. TRAVAILLE BIEN : Quand on te demande de l'aide :\n"
        f"   - Utilise des tableaux Markdown pour que ce soit propre.\n"
        f"   - Mets les noms, matricules et prix en **gras**.\n"
        f"   - Si tu vois une erreur entre le document scanné (image) et la base de données, écris en gros : ALERTE DE CONFORMITE.\n\n"
        f"5. RESTE SÉRIEUX : Tu es un expert de la Direction. Pas d'emojis, pas de petits dessins, et reste très poli mais efficace.\n\n"
        f"6. PROTECTION DES INFOS : Si on te demande qui sont les employés, ne donne que le Nom, le Matricule et le Poste. Garde le reste pour toi sauf si on te demande tout.\n\n"
        f"Voici tes outils pour travailler (mais ne les montre pas tout de suite) :\n"
        f"- Tes connaissances BDD : {infos_bdd}\n"
        f"- Ton analyse de document (résultat de l'OCR image) : {payload.contexte}"
    )

    messages = [{"role": "system", "content": system_prompt}]

    for msg in payload.messages:
        messages.append(msg.model_dump())

    chat_payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": messages,
        "max_tokens": 500
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            reponse = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=chat_payload
            )
            
            if reponse.status_code != 200:
                error_data = reponse.json()
                detail = error_data.get("error", {}).get("message", "Erreur Groq")
                raise HTTPException(status_code=reponse.status_code, detail=detail)

            data = reponse.json()
            return {"reponse": data["choices"][0]["message"]["content"]}

    except Exception as e:
        print(f"Crash Serveur : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/analyser")
async def analyser_document(fichier: UploadFile = File(...)):
    api_key = os.getenv("GROQ_API_KEY")
    
    # 1. Lecture du fichier et conversion en Base64
    contenu = await fichier.read()
    image_b64 = base64.b64encode(contenu).decode("utf-8")

    # 2. Préparation de la requête pour Groq Vision
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct", 
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extrais tout le texte de ce document RH de manière structurée."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                    }
                ]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            reponse = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload
            )
            
            if reponse.status_code != 200:
                return JSONResponse(status_code=reponse.status_code, content=reponse.json())

            data = reponse.json()
            texte_extrait = data["choices"][0]["message"]["content"]
            
            return {"texte": texte_extrait}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))