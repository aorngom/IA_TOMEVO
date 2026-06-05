from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config.base_de_donnees import get_db
from typing import List, Optional
import httpx
import os
import json

router = APIRouter(tags=["Agent IA Paie"])


class MessagePaie(BaseModel):
    role: str
    content: str


class ChatPaiePayload(BaseModel):
    messages: List[MessagePaie]
    session_id: Optional[str] = None


@router.post("/chat")
async def chat_paie(payload: ChatPaiePayload, db: Session = Depends(get_db)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Clé API absente.")

    # ── Récupération du contexte BDD ──────────────────────────
    try:
        # Employés actifs avec salaire
        employes_raw = db.execute(text("""
            SELECT e.id, e.matricule, e.nom, e.prenom, e.salaire_base_contrat,
                   p.libelle as poste, d.nom as departement,
                   e.situation_matrimoniale, e.nombre_enfants, e.actif
            FROM employe e
            LEFT JOIN poste p ON e.poste_id = p.id
            LEFT JOIN departement d ON e.departement_id = d.id
            ORDER BY e.nom
        """)).fetchall()

        employes = [
            {
                "id": str(r[0]), "matricule": r[1], "nom": r[2], "prenom": r[3],
                "salaire_base": float(r[4]) if r[4] else 0,
                "poste": r[5], "departement": r[6],
                "situation_matrimoniale": r[7],
                "nombre_enfants": r[8], "actif": r[9]
            }
            for r in employes_raw
        ]

        # Fiches de paie récentes
        fiches_raw = db.execute(text("""
            SELECT f.id, e.matricule, e.nom, e.prenom,
                   f.periode_mois, f.periode_annee,
                   f.salaire_brut, f.salaire_net, f.date_generation
            FROM fiche_paie f
            LEFT JOIN employe e ON f.employe_id = e.id
            ORDER BY f.date_generation DESC
            LIMIT 20
        """)).fetchall()

        fiches = [
            {
                "id": str(r[0]), "matricule": r[1], "nom": r[2], "prenom": r[3],
                "mois": r[4], "annee": r[5],
                "salaire_brut": float(r[6]) if r[6] else 0,
                "salaire_net": float(r[7]) if r[7] else 0,
                "date_generation": str(r[8]) if r[8] else None
            }
            for r in fiches_raw
        ]

        # Masse salariale
        masse = db.execute(text("""
            SELECT SUM(salaire_base_contrat) FROM employe WHERE actif = TRUE
        """)).scalar() or 0

        contexte_bdd = (
            f"EMPLOYÉS ACTIFS ({len(employes)}) : {json.dumps(employes, ensure_ascii=False)}\n"
            f"FICHES DE PAIE RÉCENTES : {json.dumps(fiches, ensure_ascii=False)}\n"
            f"MASSE SALARIALE TOTALE : {float(masse):,.0f} FCFA"
        )

    except Exception as e:
        contexte_bdd = f"Erreur lecture BDD : {str(e)}"

    # ── Tools ────────────────────────────────────────────────
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generer_fiche_paie",
                "description": "Génère et enregistre une fiche de paie pour un employé sur une période donnée.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employe_id": {"type": "string", "description": "UUID de l'employé"},
                        "nom_employe": {"type": "string"},
                        "periode_mois": {"type": "integer", "description": "Mois (1-12)"},
                        "periode_annee": {"type": "integer"},
                        "salaire_brut": {"type": "number"},
                        "salaire_net": {"type": "number"}
                    },
                    "required": ["employe_id", "periode_mois", "periode_annee", "salaire_brut", "salaire_net"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "supprimer_fiche_paie",
                "description": "Supprime une fiche de paie. Demande confirmation avant d'agir.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fiche_id": {"type": "string", "description": "UUID de la fiche à supprimer"},
                        "description_fiche": {"type": "string", "description": "Description pour confirmation"}
                    },
                    "required": ["fiche_id", "description_fiche"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculer_salaire",
                "description": (
                    "Calcule le salaire net d'un employé en appliquant les cotisations sénégalaises : "
                    "IPRES part salariale (5.6%), Impôt sur le Revenu (taux progressif). "
                    "Retourne le détail du calcul."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employe_id": {"type": "string"},
                        "nom_employe": {"type": "string"},
                        "salaire_brut": {"type": "number"}
                    },
                    "required": ["employe_id", "salaire_brut"]
                }
            }
        }
    ]

    # ── System prompt ─────────────────────────────────────────
    system_prompt = (
        "Tu es l'assistant IA de gestion de la paie pour Jariniou.\n\n"
        "Tu peux :\n"
        "- Répondre à des questions sur les salaires, fiches de paie, cotisations\n"
        "- Calculer automatiquement les salaires nets avec les cotisations sénégalaises\n"
        "- Générer des fiches de paie pour un ou plusieurs employés\n"
        "- Supprimer des fiches (avec confirmation obligatoire)\n"
        "- Détecter des anomalies (fiches manquantes, doublons, incohérences)\n"
        "- Fournir des statistiques sur la masse salariale\n\n"
        "RÈGLES DE CALCUL SÉNÉGALAISES :\n"
        "- IPRES régime général part salariale : 5.6% du salaire brut\n"
        "- Impôt sur le Revenu (IR) : taux progressif\n"
        "  * 0 à 630 000 FCFA/an : 0%\n"
        "  * 630 001 à 1 500 000 : 20%\n"
        "  * 1 500 001 à 4 000 000 : 30%\n"
        "  * Au-delà de 4 000 000 : 40%\n"
        "- Salaire net = Brut - IPRES salariale - IR\n\n"
        "RÈGLES COMPORTEMENTALES :\n"
        "- Toujours demander confirmation avant de supprimer\n"
        "- Utiliser des tableaux Markdown pour les données chiffrées\n"
        "- Répondre en français, de manière professionnelle\n"
        "- Pas d'emojis\n\n"
        f"DONNÉES ACTUELLES :\n{contexte_bdd}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in payload.messages:
        messages.append(msg.model_dump())

    # ── Appel API ─────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            reponse = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto"
                }
            )

            res_data = reponse.json()
            if "choices" not in res_data:
                return {"reponse": f"Erreur API : {res_data.get('error', {}).get('message', str(res_data))}"}

            message_ia = res_data["choices"][0]["message"]

            if "tool_calls" in message_ia:
                tool_call = message_ia["tool_calls"][0]
                tool_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])

                # ── Générer une fiche ──────────────────────────
                if tool_name == "generer_fiche_paie":
                    try:
                        # Récupérer les infos de l'employé
                        emp = db.execute(text(
                            "SELECT nom, prenom FROM employe WHERE id = :id"
                        ), {"id": args["employe_id"]}).fetchone()

                        if not emp:
                            return {"reponse": "Employé introuvable."}

                        db.execute(text("""
                            INSERT INTO fiche_paie
                                (employe_id, prenom_employe, nom_employe,
                                 periode_mois, periode_annee, salaire_brut, salaire_net)
                            VALUES
                                (:emp_id, :prenom, :nom, :mois, :annee, :brut, :net)
                        """), {
                            "emp_id": args["employe_id"],
                            "prenom": emp[1],
                            "nom": emp[0],
                            "mois": args["periode_mois"],
                            "annee": args["periode_annee"],
                            "brut": args["salaire_brut"],
                            "net": args["salaire_net"]
                        })
                        db.commit()

                        mois_noms = ['Janvier','Février','Mars','Avril','Mai','Juin',
                                     'Juillet','Août','Septembre','Octobre','Novembre','Décembre']
                        msg_ia = (
                            f"Fiche de paie générée pour **{emp[1]} {emp[0]}**.\n\n"
                            f"| Élément | Montant |\n|---|---|\n"
                            f"| Salaire brut | {args['salaire_brut']:,.0f} FCFA |\n"
                            f"| Salaire net | {args['salaire_net']:,.0f} FCFA |\n"
                            f"| Cotisations | {args['salaire_brut'] - args['salaire_net']:,.0f} FCFA |\n"
                            f"| Période | {mois_noms[args['periode_mois']-1]} {args['periode_annee']} |"
                        )
                        return {
                            "action": "FICHE_GENEREE",
                            "reponse": msg_ia,
                            "rafraichir": True
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur lors de la génération : {str(e)}"}

                # ── Supprimer une fiche ────────────────────────
                elif tool_name == "supprimer_fiche_paie":
                    try:
                        db.execute(text(
                            "DELETE FROM fiche_paie WHERE id = :id"
                        ), {"id": args["fiche_id"]})
                        db.commit()

                        return {
                            "action": "FICHE_SUPPRIMEE",
                            "reponse": f"La fiche **{args['description_fiche']}** a été supprimée.",
                            "rafraichir": True
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur lors de la suppression : {str(e)}"}

                # ── Calculer un salaire ────────────────────────
                elif tool_name == "calculer_salaire":
                    brut = args["salaire_brut"]
                    nom = args.get("nom_employe", "l'employé")

                    # IPRES part salariale
                    ipres = brut * 0.056

                    brut_annuel = brut * 12
                    if brut_annuel <= 630000:
                        ir_annuel = 0
                    elif brut_annuel <= 1500000:
                        ir_annuel = (brut_annuel - 630000) * 0.20
                    elif brut_annuel <= 4000000:
                        ir_annuel = (870000 * 0.20) + ((brut_annuel - 1500000) * 0.30)
                    else:
                        ir_annuel = (870000 * 0.20) + (2500000 * 0.30) + ((brut_annuel - 4000000) * 0.40)

                    ir_mensuel = ir_annuel / 12
                    net = brut - ipres - ir_mensuel

                    msg_ia = (
                        f"Calcul de salaire pour **{nom}** :\n\n"
                        f"| Élément | Montant |\n|---|---|\n"
                        f"| Salaire brut | {brut:,.0f} FCFA |\n"
                        f"| IPRES part salariale (5.6%) | -{ipres:,.0f} FCFA |\n"
                        f"| Impôt sur le Revenu | -{ir_mensuel:,.0f} FCFA |\n"
                        f"| **Salaire net** | **{net:,.0f} FCFA** |"
                    )
                    return {
                        "action": "CALCUL_SALAIRE",
                        "reponse": msg_ia,
                        "salaire_brut": brut,
                        "salaire_net": round(net, 2),
                        "employe_id": args.get("employe_id")
                    }

            return {"reponse": message_ia["content"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))