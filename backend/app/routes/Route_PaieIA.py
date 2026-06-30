from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config.base_de_donnees import get_db
from app.services.Service_PaieIA import (
    calculer_salaire_complet,
    analyser_fiches_mois,
    detecter_irregularites,
    statistiques_masse_salariale,
    comparer_mois,
    sauvegarder_fiche_calculee,
    lancer_paie_masse,
    get_config_pays
)
from app.services.Service_Mail import envoyer_mail_manuel, envoyer_bulletin_employe
from app.services.Service_Scheduler import (
    reconfigurer_planning,
    declencher_maintenant
)
from typing import List, Optional
import httpx
import os
import json
import base64

router = APIRouter(tags=["Agent IA Paie"])


# MODÈLES

class MessagePaie(BaseModel):
    role: str
    content: str


class ChatPaiePayload(BaseModel):
    messages: List[MessagePaie]
    session_id: Optional[str] = None
    fichier_base64: Optional[str] = None
    fichier_nom: Optional[str] = None


# ENDPOINT PRINCIPAL

@router.post("/chat")
async def chat_paie(payload: ChatPaiePayload, db: Session = Depends(get_db)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Clé API absente.")

    #  Contexte BDD temps réel 
    try:
        config = get_config_pays(db)
        devise = config["devise"]
        pays = config["pays_nom"]

        # Employés actifs
        employes_raw = db.execute(text("""
            SELECT e.id, e.matricule, e.nom, e.prenom,
                   e.salaire_base_contrat, p.libelle as poste,
                   d.nom as departement, e.actif, e.email_perso
            FROM employe e
            LEFT JOIN poste p ON e.poste_id = p.id
            LEFT JOIN departement d ON e.departement_id = d.id
            ORDER BY e.nom
        """)).fetchall()

        employes = [
            {
                "id": str(r[0]), "matricule": r[1],
                "nom": r[2], "prenom": r[3],
                "salaire_base": float(r[4]) if r[4] else 0,
                "poste": r[5], "departement": r[6],
                "actif": r[7], "email": r[8]
            }
            for r in employes_raw
        ]

        # Fiches récentes
        fiches_raw = db.execute(text("""
            SELECT f.id, e.matricule, e.nom, e.prenom,
                   f.periode_mois, f.periode_annee,
                   f.salaire_brut, f.salaire_net,
                   f.est_envoyee, f.date_generation
            FROM fiche_paie f
            LEFT JOIN employe e ON f.employe_id = e.id
            ORDER BY f.date_generation DESC
            LIMIT 30
        """)).fetchall()

        fiches = [
            {
                "id": str(r[0]), "matricule": r[1],
                "nom": r[2], "prenom": r[3],
                "mois": r[4], "annee": r[5],
                "brut": float(r[6]) if r[6] else 0,
                "net": float(r[7]) if r[7] else 0,
                "envoyee": r[8],
                "date_generation": str(r[9]) if r[9] else None
            }
            for r in fiches_raw
        ]

        # Config scheduler
        config_paie = db.execute(text("""
            SELECT jour_declenchement, heure_declenchement
            FROM config_paie WHERE actif = TRUE LIMIT 1
        """)).fetchone()

        info_scheduler = (
            f"Paie programmée le {config_paie[0]} de chaque mois "
            f"à {str(config_paie[1])[:5]}"
            if config_paie else "Scheduler non configuré"
        )

        contexte_bdd = (
            f"PAYS : {pays} | DEVISE : {devise}\n"
            f"SCHEDULER : {info_scheduler}\n"
            f"EMPLOYÉS ({len(employes)}) : {json.dumps(employes, ensure_ascii=False)}\n"
            f"FICHES RÉCENTES (30 dernières) : {json.dumps(fiches, ensure_ascii=False)}\n"
        )

    except Exception as e:
        contexte_bdd = f"Erreur lecture BDD : {str(e)}"
        devise = "FCFA"

    #  Analyse fichier si fourni ─
    contexte_fichier = ""
    if payload.fichier_base64:
        contexte_fichier = await _analyser_fichier_bulletin(
            payload.fichier_base64,
            payload.fichier_nom or "document",
            api_key
        )

    #  Tools ─
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculer_salaire",
                "description": (
                    "Calcule le salaire net. Si employe_id est fourni, utilise les données de l'employé. "
                    "Si seulement salaire_brut_override est fourni sans employe_id, fait un calcul générique "
                    "avec les cotisations du pays. Utilise toujours le moteur officiel."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employe_id": {"type": "string", "description": "UUID de l'employé"},
                        "nom_employe": {"type": "string"},
                        "periode_mois": {"type": "integer", "description": "Mois 1-12"},
                        "periode_annee": {"type": "integer"},
                        "salaire_brut_override": {
                            "type": "number",
                            "description": "Si fourni, remplace le salaire de base du contrat"
                        }
                    },
                    "required": ["periode_mois", "periode_annee"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generer_fiche_paie",
                "description": (
                    "Calcule et sauvegarde la fiche de paie complète d'un employé. "
                    "Utilise le moteur officiel. Refuse si une fiche existe déjà pour ce mois."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employe_id": {"type": "string"},
                        "nom_employe": {"type": "string"},
                        "periode_mois": {"type": "integer"},
                        "periode_annee": {"type": "integer"},
                        "salaire_brut_override": {"type": "number"}
                    },
                    "required": ["employe_id", "periode_mois", "periode_annee"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "lancer_paie_masse",
                "description": (
                    "Lance la paie pour TOUS les employés actifs d'un mois donné. "
                    "Ignore ceux qui ont déjà une fiche. "
                    "Demande confirmation avant d'agir."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "periode_mois": {"type": "integer"},
                        "periode_annee": {"type": "integer"},
                        "envoyer_mails": {
                            "type": "boolean",
                            "description": "Si true, envoie les bulletins par mail après génération"
                        }
                    },
                    "required": ["periode_mois", "periode_annee"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyser_fiches_mois",
                "description": (
                    "Analyse qui a eu une fiche de paie et qui n'en a pas eu "
                    "pour un mois donné. Données temps réel depuis la BDD."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "periode_mois": {"type": "integer"},
                        "periode_annee": {"type": "integer"}
                    },
                    "required": ["periode_mois", "periode_annee"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "detecter_irregularites",
                "description": (
                    "Détecte les anomalies de paie : doublons, incohérences brut/net, "
                    "fiches manquantes du mois courant."
                ),
                "parameters": {"type": "object", "properties": {}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "statistiques_masse_salariale",
                "description": (
                    "Fournit les statistiques complètes sur la masse salariale : "
                    "global, par département, top salaires."
                ),
                "parameters": {"type": "object", "properties": {}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "comparer_mois",
                "description": "Compare la masse salariale entre deux mois.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mois1": {"type": "integer"},
                        "annee1": {"type": "integer"},
                        "mois2": {"type": "integer"},
                        "annee2": {"type": "integer"}
                    },
                    "required": ["mois1", "annee1", "mois2", "annee2"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "supprimer_fiche_paie",
                "description": "Supprime une fiche de paie. Demande confirmation obligatoire avant.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fiche_id": {"type": "string"},
                        "description_fiche": {"type": "string"}
                    },
                    "required": ["fiche_id", "description_fiche"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "envoyer_mail_manuel",
                "description": (
                    "Rédige et envoie un mail professionnel à un employé ou destinataire. "
                    "Affiche un aperçu et demande confirmation avant d'envoyer."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destinataire_email": {"type": "string"},
                        "destinataire_nom": {"type": "string"},
                        "sujet": {"type": "string"},
                        "corps": {"type": "string", "description": "Corps du mail rédigé de manière professionnelle"},
                        "confirme": {"type": "boolean", "description": "True si l'utilisateur a confirmé l'envoi"}
                    },
                    "required": ["destinataire_email", "sujet", "corps", "confirme"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "envoyer_bulletin_employe",
                "description": "Envoie le bulletin de paie d'un mois donné par mail à un employé.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employe_id": {"type": "string"},
                        "nom_employe": {"type": "string"},
                        "periode_mois": {"type": "integer"},
                        "periode_annee": {"type": "integer"}
                    },
                    "required": ["employe_id", "periode_mois", "periode_annee"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "configurer_planning_paie",
                "description": (
                    "Modifie la date et l'heure de déclenchement automatique de la paie. "
                    "Le jour doit être entre 1 et 28."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "jour": {"type": "integer", "description": "Jour du mois (1-28)"},
                        "heure": {"type": "integer", "description": "Heure (0-23)"},
                        "minute": {"type": "integer", "description": "Minutes (0-59)"}
                    },
                    "required": ["jour", "heure", "minute"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "declencher_paie_maintenant",
                "description": (
                    "Déclenche immédiatement la paie pour un mois donné sans attendre le scheduler. "
                    "Utilisé pour les tests ou les lancements manuels urgents. "
                    "Demande confirmation avant d'agir."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "periode_mois": {"type": "integer"},
                        "periode_annee": {"type": "integer"},
                        "envoyer_mails": {"type": "boolean"},
                        "type_exec": {
                            "type": "string",
                            "enum": ["test", "manuelle"],
                            "description": "test = pas de mail, manuelle = avec mails"
                        }
                    },
                    "required": ["periode_mois", "periode_annee"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "creer_rappel",
                "description": (
                    "Crée un rappel ou un envoi automatique programmé. "
                    "Pour un rappel : l'utilisateur reçoit une notification 2 minutes avant. "
                    "Pour un envoi auto : le mail part automatiquement à l'heure dite. "
                    "Demande toujours confirmation avant de créer."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["rappel", "envoi_auto"],
                            "description": "rappel = notif utilisateur, envoi_auto = mail automatique"
                        },
                        "date_heure": {
                            "type": "string",
                            "description": "ISO 8601 ex: 2026-06-07T17:50:00"
                        },
                        "message": {
                            "type": "string",
                            "description": "Message de la notification ou description de l'action"
                        },
                        "destinataire_email": {"type": "string"},
                        "sujet_mail": {"type": "string"},
                        "corps_mail": {"type": "string"}
                    },
                    "required": ["type", "date_heure", "message"]
                }
            }
        }
    ]

    from datetime import datetime as _dt
    date_actuelle = _dt.now().strftime("%d/%m/%Y à %Hh%M")

    #  System prompt 
    system_prompt = (
        f"Tu es l'assistant IA de gestion de la paie pour Jariniou.\n"
        f"Pays configuré : {pays} | Devise : {devise}\n"
        f"Date et heure actuelles du serveur : {date_actuelle}\n\n"
        "CAPACITÉS :\n"
        "- Analyser les fiches de paie et détecter les anomalies\n"
        "- Calculer les salaires nets avec les cotisations officielles du pays (depuis BDD)\n"
        "- Générer des fiches de paie individuelles ou en masse\n"
        "- Envoyer des bulletins par mail ou des mails manuels\n"
        "- Configurer et déclencher le scheduler de paie\n"
        "- Répondre à des questions sur les salaires avec des données temps réel\n"
        "- Analyser un bulletin uploadé et expliquer chaque ligne simplement\n\n"
        "RÈGLES STRICTES :\n"
        "- Toujours demander confirmation avant : supprimer, lancer paie masse, envoyer mails\n"
        "- Pour les mails manuels : rédiger le corps professionnellement, afficher aperçu, attendre OUI explicite\n"
        "- Tableaux Markdown pour les données chiffrées\n"
        "- Répondre en français, sans emojis\n"
        "- Ne jamais inventer de chiffres : toujours utiliser les tools\n"
        "- Pour les analyses, appeler le tool dédié plutôt que de lire le contexte\n\n"
        "RÈGLES DE COMMUNICATION :\n"
        "- Réponses courtes et directes. Maximum 5-6 lignes pour une réponse simple.\n"
        "- Si l'utilisateur pose une question simple, répondre simplement sans expliquer le processus.\n"
        "- Ne jamais afficher les erreurs techniques brutes. En cas d'erreur dire simplement : 'Je n'ai pas pu traiter cette demande, pouvez-vous reformuler ?'\n"
        "- Ne jamais s'excuser excessivement ni répéter les mêmes informations.\n"
        "- Quand tu corriges une erreur, dis-le en une phrase, pas en plusieurs paragraphes.\n"
        "- Si tu n'as pas accès à une info, dis-le en une phrase.\n\n"
        "RAPPELS ET ENVOIS PROGRAMMÉS :\n"
        "- Pour un rappel avec mail : collecter OBLIGATOIREMENT destinataire, sujet et corps AVANT de créer le rappel.\n"
        "- Pour un rappel simple : juste le message suffit.\n"
        "- Ne pas créer le rappel si les infos mail sont manquantes, demander d'abord.\n\n"
        "DOCUMENT UPLOADÉ :\n"
        f"{contexte_fichier if contexte_fichier else 'Aucun document fourni.'}\n\n"
        f"DONNÉES TEMPS RÉEL BDD :\n{contexte_bdd}"
    )

    messages_api = [{"role": "system", "content": system_prompt}]
    for msg in payload.messages:
        messages_api.append(msg.model_dump())

    dernier_message_user = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"), ""
    )

    #  Appel API 
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            reponse = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages_api,
                    "tools": tools,
                    "tool_choice": "auto"
                }
            )

            res_data = reponse.json()
            if "choices" not in res_data:
                return {
                    "reponse": f"Erreur API : {res_data.get('error', {}).get('message', str(res_data))}"
                }

            message_ia = res_data["choices"][0]["message"]

            #  Gestion tool calls 
            if "tool_calls" in message_ia:
                tool_call = message_ia["tool_calls"][0]
                tool_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])

                #  calculer_salaire 
                if tool_name == "calculer_salaire":
                    try:
                        employe_id = args.get("employe_id", "")
                        if not employe_id or employe_id.strip() == "":
                            brut = args.get("salaire_brut_override", 0)
                            if not brut:
                                return {"reponse": "Précisez un salaire brut pour effectuer le calcul."}
                            config = get_config_pays(db)
                            cotisations = config["cotisations"]
                            tranches_ir = config["tranches_ir"]
                            devise = config["devise"]
                            total_sal = sum(c["taux_salarial"] / 100 * brut for c in cotisations)
                            base_ir = max(0, (brut - total_sal) * 0.70)
                            base_ir_annuel = base_ir * 12
                            ir_annuel = 0.0
                            for t in tranches_ir:
                                if base_ir_annuel <= t["min"]: break
                                plafond = t["max"] if t["max"] else float("inf")
                                dans_tranche = min(base_ir_annuel, plafond) - t["min"]
                                if dans_tranche > 0:
                                    ir_annuel += dans_tranche * t["taux"] / 100
                            ir = ir_annuel / 12
                            net = brut - total_sal - ir
                            msg_ia = (
                                f"Calcul pour un salaire brut de **{brut:,.0f} {devise}** :\n\n"
                                f"| Élément | Montant |\n|---|---|\n"
                                f"| Salaire brut | {brut:,.0f} {devise} |\n"
                                f"| Cotisations salariales | -{total_sal:,.0f} {devise} |\n"
                                f"| Impôt sur le Revenu | -{ir:,.0f} {devise} |\n"
                                f"| **Net à payer** | **{net:,.0f} {devise}** |"
                            )
                            return {"action": "CALCUL_SALAIRE", "reponse": msg_ia}
                        calcul = calculer_salaire_complet(
                            db,
                            args["employe_id"],
                            args["periode_mois"],
                            args["periode_annee"],
                            args.get("salaire_brut_override")
                        )
                        mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
                        msg_ia = (
                            f"Calcul de salaire pour **{calcul['prenom']} {calcul['nom']}** "
                            f"— {mois_noms[calcul['periode_mois']-1]} {calcul['periode_annee']}\n\n"
                            f"| Élément | Montant |\n|---|---|\n"
                            f"| Salaire de base | {calcul['salaire_base']:,.0f} {devise} |\n"
                        )
                        if calcul["prime_transport"] > 0:
                            msg_ia += f"| Prime de transport | {calcul['prime_transport']:,.0f} {devise} |\n"
                        if calcul["prime_logement"] > 0:
                            msg_ia += f"| Prime de logement | {calcul['prime_logement']:,.0f} {devise} |\n"
                        if calcul["retenue_absence"] > 0:
                            msg_ia += f"| Retenue absences ({calcul['jours_absence']} j.) | -{calcul['retenue_absence']:,.0f} {devise} |\n"
                        msg_ia += (
                            f"| **Salaire brut** | **{calcul['salaire_brut']:,.0f} {devise}** |\n"
                            f"| IPRES salariale | -{calcul['ipres_salariale']:,.0f} {devise} |\n"
                            f"| Impôt sur le Revenu | -{calcul['ir']:,.0f} {devise} |\n"
                            f"| **Net à payer** | **{calcul['salaire_net']:,.0f} {devise}** |"
                        )
                        return {
                            "action": "CALCUL_SALAIRE",
                            "reponse": msg_ia,
                            "calcul": calcul
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur calcul : {str(e)}"}

                #  generer_fiche_paie 
                elif tool_name == "generer_fiche_paie":
                    try:
                        calcul = calculer_salaire_complet(
                            db,
                            args["employe_id"],
                            args["periode_mois"],
                            args["periode_annee"],
                            args.get("salaire_brut_override")
                        )
                        fiche_id = sauvegarder_fiche_calculee(db, calcul)
                        mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
                        msg_ia = (
                            f"Fiche de paie générée pour **{calcul['prenom']} {calcul['nom']}**"
                            f" — {mois_noms[calcul['periode_mois']-1]} {calcul['periode_annee']}\n\n"
                            f"| Élément | Montant |\n|---|---|\n"
                            f"| Salaire brut | {calcul['salaire_brut']:,.0f} {devise} |\n"
                            f"| Cotisations salariales | -{calcul['total_cotisations_salariales']:,.0f} {devise} |\n"
                            f"| **Net à payer** | **{calcul['salaire_net']:,.0f} {devise}** |"
                        )
                        return {
                            "action": "FICHE_GENEREE",
                            "reponse": msg_ia,
                            "fiche_id": fiche_id,
                            "rafraichir": True
                        }
                    except ValueError as e:
                        return {"reponse": str(e)}
                    except Exception as e:
                        return {"reponse": f"Erreur génération : {str(e)}"}

                #  lancer_paie_masse ─
                elif tool_name == "lancer_paie_masse":
                    try:
                        mois = args["periode_mois"]
                        annee = args["periode_annee"]
                        envoyer_mails = args.get("envoyer_mails", False)

                        resultat = lancer_paie_masse(db, mois, annee)

                        mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

                        msg_ia = (
                            f"Paie de masse lancée pour **{mois_noms[mois-1]} {annee}**.\n\n"
                            f"| Résultat | Nombre |\n|---|---|\n"
                            f"| Fiches générées | {resultat['nb_generes']} |\n"
                            f"| Déjà existantes (ignorées) | {resultat['nb_ignores']} |\n"
                            f"| Erreurs | {resultat['nb_erreurs']} |\n"
                        )

                        # Envoi mails si demandé
                        if envoyer_mails and resultat["nb_generes"] > 0:
                            nb_mails = 0
                            for gen in resultat["detail"]["generes"]:
                                emp_data = db.execute(text("""
                                    SELECT id FROM employe WHERE matricule = :mat
                                """), {"mat": gen["matricule"]}).scalar()
                                if emp_data:
                                    calcul = calculer_salaire_complet(db, str(emp_data), mois, annee)
                                    r = await envoyer_bulletin_employe(calcul)
                                    if r["succes"]:
                                        nb_mails += 1
                            msg_ia += f"\n{nb_mails} bulletin(s) envoyé(s) par mail."

                        return {
                            "action": "PAIE_MASSE_LANCEE",
                            "reponse": msg_ia,
                            "rafraichir": True,
                            "resultat": resultat
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur paie masse : {str(e)}"}

                #  analyser_fiches_mois 
                elif tool_name == "analyser_fiches_mois":
                    try:
                        analyse = analyser_fiches_mois(
                            db,
                            args["periode_mois"],
                            args["periode_annee"]
                        )
                        msg_ia = (
                            f"Analyse des fiches — **{analyse['periode_label']}**\n\n"
                            f"| | Nombre |\n|---|---|\n"
                            f"| Employés actifs | {analyse['total_actifs']} |\n"
                            f"| Avec fiche | {analyse['nb_avec_fiche']} |\n"
                            f"| Sans fiche | {analyse['nb_sans_fiche']} |\n"
                        )
                        if analyse["sans_fiche"]:
                            msg_ia += "\n**Employés sans fiche :**\n"
                            msg_ia += "| Matricule | Nom | Poste | Département |\n|---|---|---|---|\n"
                            for e in analyse["sans_fiche"]:
                                msg_ia += (
                                    f"| {e['matricule']} | {e['prenom']} {e['nom']} "
                                    f"| {e.get('poste', '—')} | {e.get('departement', '—')} |\n"
                                )
                        else:
                            msg_ia += "\nToutes les fiches sont générées pour cette période."
                        return {"action": "ANALYSE_MOIS", "reponse": msg_ia}
                    except Exception as e:
                        return {"reponse": f"Erreur analyse : {str(e)}"}

                #  detecter_irregularites 
                elif tool_name == "detecter_irregularites":
                    try:
                        rapport = detecter_irregularites(db)
                        if rapport["nb_irregularites"] == 0:
                            return {"reponse": "Aucune irrégularité détectée. La paie est cohérente."}

                        msg_ia = f"**{rapport['nb_irregularites']} irrégularité(s) détectée(s)**\n\n"

                        if rapport["hautes"]:
                            msg_ia += "**Sévérité HAUTE :**\n"
                            for ir in rapport["hautes"]:
                                msg_ia += f"- {ir['type']} — {ir['employe']} : {ir['detail']}\n"

                        if rapport["moyennes"]:
                            msg_ia += "\n**Sévérité MOYENNE :**\n"
                            for ir in rapport["moyennes"]:
                                msg_ia += f"- {ir['type']} — {ir['employe']} : {ir['detail']}\n"

                        if rapport["infos"]:
                            msg_ia += "\n**Informations :**\n"
                            for ir in rapport["infos"]:
                                msg_ia += f"- {ir['employe']} : {ir['detail']}\n"

                        return {"action": "IRREGULARITES", "reponse": msg_ia}
                    except Exception as e:
                        return {"reponse": f"Erreur détection : {str(e)}"}

                #  statistiques_masse_salariale 
                elif tool_name == "statistiques_masse_salariale":
                    try:
                        stats = statistiques_masse_salariale(db)
                        g = stats["global"]
                        msg_ia = (
                            f"**Statistiques masse salariale — {pays}**\n\n"
                            f"| Indicateur | Valeur |\n|---|---|\n"
                            f"| Employés actifs | {g['nb_employes']} |\n"
                            f"| Masse salariale base | {g['masse_salariale_base']:,.0f} {devise} |\n"
                            f"| Salaire moyen | {g['salaire_moyen']:,.0f} {devise} |\n"
                            f"| Salaire minimum | {g['salaire_minimum']:,.0f} {devise} |\n"
                            f"| Salaire maximum | {g['salaire_maximum']:,.0f} {devise} |\n\n"
                        )
                        if stats["par_departement"]:
                            msg_ia += "**Par département :**\n"
                            msg_ia += "| Département | Effectif | Masse | Moyenne |\n|---|---|---|---|\n"
                            for d in stats["par_departement"]:
                                msg_ia += (
                                    f"| {d['departement']} | {d['nb_employes']} "
                                    f"| {d['masse']:,.0f} | {d['moyenne']:,.0f} |\n"
                                )
                        if stats["top_salaires"]:
                            msg_ia += "\n**Top 5 salaires :**\n"
                            msg_ia += "| Employé | Poste | Salaire |\n|---|---|---|\n"
                            for t in stats["top_salaires"]:
                                msg_ia += (
                                    f"| {t['prenom']} {t['nom']} ({t['matricule']}) "
                                    f"| {t['poste']} | {t['salaire']:,.0f} {devise} |\n"
                                )
                        return {"action": "STATS_MASSE", "reponse": msg_ia}
                    except Exception as e:
                        return {"reponse": f"Erreur statistiques : {str(e)}"}

                #  comparer_mois ─
                elif tool_name == "comparer_mois":
                    try:
                        comp = comparer_mois(
                            db,
                            args["mois1"], args["annee1"],
                            args["mois2"], args["annee2"]
                        )
                        evolution = "+" if comp["evolution_brut"] >= 0 else ""
                        msg_ia = (
                            f"**Comparaison {comp['periode_1']['label']} vs {comp['periode_2']['label']}**\n\n"
                            f"| | {comp['periode_1']['label']} | {comp['periode_2']['label']} | Évolution |\n"
                            f"|---|---|---|---|\n"
                            f"| Fiches | {comp['periode_1']['nb_fiches']} | {comp['periode_2']['nb_fiches']} | — |\n"
                            f"| Masse brute | {comp['periode_1']['masse_brute']:,.0f} | "
                            f"{comp['periode_2']['masse_brute']:,.0f} | "
                            f"{evolution}{comp['evolution_brut']:,.0f} ({evolution}{comp['evolution_pct']:.1f}%) |\n"
                            f"| Masse nette | {comp['periode_1']['masse_nette']:,.0f} | "
                            f"{comp['periode_2']['masse_nette']:,.0f} | "
                            f"{evolution}{comp['evolution_net']:,.0f} |"
                        )
                        return {"action": "COMPARAISON_MOIS", "reponse": msg_ia}
                    except Exception as e:
                        return {"reponse": f"Erreur comparaison : {str(e)}"}

                #  supprimer_fiche_paie 
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
                        return {"reponse": f"Erreur suppression : {str(e)}"}

                #  envoyer_mail_manuel ─
                elif tool_name == "envoyer_mail_manuel":
                    try:
                        if not args.get("confirme", False):
                            # Afficher aperçu et demander confirmation
                            msg_ia = (
                                f"Voici l'aperçu du mail avant envoi :\n\n"
                                f"**Destinataire :** {args.get('destinataire_nom', '')} "
                                f"<{args['destinataire_email']}>\n"
                                f"**Objet :** {args['sujet']}\n\n"
                                f"---\n{args['corps']}\n---\n\n"
                                f"Confirmez-vous l'envoi de ce mail ? (Répondez OUI pour confirmer)"
                            )
                            return {"action": "APERCU_MAIL", "reponse": msg_ia}

                        # Envoi confirmé
                        resultat = await envoyer_mail_manuel(
                            destinataire=args["destinataire_email"],
                            sujet=args["sujet"],
                            corps=args["corps"]
                        )
                        if resultat["succes"]:
                            return {
                                "action": "MAIL_ENVOYE",
                                "reponse": (
                                    f"Mail envoyé avec succès à "
                                    f"**{args.get('destinataire_nom', args['destinataire_email'])}**."
                                )
                            }
                        else:
                            return {"reponse": f"Échec envoi : {resultat['detail']}"}
                    except Exception as e:
                        return {"reponse": f"Erreur mail : {str(e)}"}

                #  envoyer_bulletin_employe 
                elif tool_name == "envoyer_bulletin_employe":
                    try:
                        calcul = calculer_salaire_complet(
                            db,
                            args["employe_id"],
                            args["periode_mois"],
                            args["periode_annee"]
                        )
                        resultat = await envoyer_bulletin_employe(calcul)
                        if resultat["succes"]:
                            mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                                         'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
                            return {
                                "action": "BULLETIN_ENVOYE",
                                "reponse": (
                                    f"Bulletin de **{calcul['prenom']} {calcul['nom']}** "
                                    f"pour {mois_noms[calcul['periode_mois']-1]} {calcul['periode_annee']} "
                                    f"envoyé à {calcul['email_perso']}."
                                )
                            }
                        else:
                            return {"reponse": f"Échec : {resultat['detail']}"}
                    except Exception as e:
                        return {"reponse": f"Erreur envoi bulletin : {str(e)}"}

                #  configurer_planning_paie 
                elif tool_name == "configurer_planning_paie":
                    try:
                        resultat = await reconfigurer_planning(
                            db,
                            args["jour"],
                            args["heure"],
                            args.get("minute", 0)
                        )
                        return {
                            "action": "PLANNING_CONFIGURE",
                            "reponse": resultat["detail"]
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur configuration : {str(e)}"}

                #  declencher_paie_maintenant 
                elif tool_name == "declencher_paie_maintenant":
                    try:
                        resultat = await declencher_maintenant(
                            db,
                            args["periode_mois"],
                            args["periode_annee"],
                            args.get("type_exec", "test")
                        )
                        mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
                        msg_ia = (
                            f"Paie déclenchée pour **{mois_noms[args['periode_mois']-1]} "
                            f"{args['periode_annee']}**.\n\n"
                            f"| Résultat | Valeur |\n|---|---|\n"
                            f"| Fiches générées | {resultat['nb_generes']} |\n"
                            f"| Mails envoyés | {resultat['nb_mails']} |\n"
                            f"| Erreurs | {resultat['nb_erreurs']} |"
                        )
                        if resultat["nb_erreurs"] > 0:
                            msg_ia += "\n\n**Erreurs :**\n"
                            for err in resultat["details"]["erreurs"]:
                                msg_ia += f"- {err.get('employe_id', '?')} : {err.get('erreur', '?')}\n"
                        return {
                            "action": "PAIE_DECLENCHEE",
                            "reponse": msg_ia,
                            "rafraichir": True
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur déclenchement : {str(e)}"}
                
                #  creer_rappel ─
                elif tool_name == "creer_rappel":
                    try:
                        from datetime import datetime as dt, timedelta
                        import json as _json

                        type_rappel = args["type"]
                        date_heure_str = args["date_heure"]
                        message = args["message"]

                        # Parser la date
                        date_heure = dt.fromisoformat(date_heure_str)

                        # Si rappel → on déclenche 2 minutes avant
                        date_declenchement = date_heure
                        if type_rappel == "rappel":
                            date_declenchement = date_heure - timedelta(minutes=2)

                        # Construire l'action si mail
                        action = None
                        if args.get("destinataire_email"):
                            action = _json.dumps({
                                "destinataire": args["destinataire_email"],
                                "sujet": args.get("sujet_mail", ""),
                                "corps": args.get("corps_mail", "")
                            }, ensure_ascii=False)

                        # Insérer en BDD
                        db.execute(text("""
                            INSERT INTO rappel_ia (type, date_heure, message, action, statut)
                            VALUES (:type, :date_heure, :message, :action, 'en_attente')
                        """), {
                            "type": type_rappel,
                            "date_heure": date_declenchement,
                            "message": message,
                            "action": action
                        })
                        db.commit()

                        print(f"[RAPPEL] Nouveau rappel créé — type={type_rappel} | "
                            f"déclenchement={date_declenchement.strftime('%d/%m/%Y à %Hh%M')}")

                        if type_rappel == "rappel":
                            msg_ia = (
                                f"Rappel créé. Vous recevrez une notification le "
                                f"**{date_declenchement.strftime('%d/%m/%Y à %Hh%M')}** "
                                f"(2 minutes avant {date_heure.strftime('%Hh%M')}) :\n\n"
                                f"> {message}"
                            )
                        else:
                            msg_ia = (
                                f"Envoi automatique programmé le "
                                f"**{date_declenchement.strftime('%d/%m/%Y à %Hh%M')}**.\n\n"
                                f"> {message}"
                            )

                        return {"action": "RAPPEL_CREE", "reponse": msg_ia}

                    except Exception as e:
                        return {"reponse": f"Erreur création rappel : {str(e)}"}

            #  Réponse texte simple 
            return {"reponse": message_ia.get("content", "Pas de réponse.")}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    """
    Retourne les rappels déclenchés non encore lus par le frontend.
    Appelé toutes les 30 secondes par le frontend.
    """
    try:
        rappels = db.execute(text("""
            SELECT id, type, message, action, date_heure
            FROM rappel_ia
            WHERE statut = 'declenche'
            ORDER BY date_heure DESC
            LIMIT 10
        """)).fetchall()

        import json as _json
        notifications = []
        for r in rappels:
            action = None
            if r[3]:
                try:
                    action = r[3] if isinstance(r[3], dict) else _json.loads(r[3])
                except Exception:
                    action = None

            notifications.append({
                "id": str(r[0]),
                "type": r[1],
                "message": r[2],
                "action": action,
                "date_heure": str(r[4])
            })

        return {"notifications": notifications}
    except Exception as e:
        return {"notifications": [], "erreur": str(e)}


@router.post("/notifications/{rappel_id}/lue")
def marquer_notification_lue(rappel_id: str, db: Session = Depends(get_db)):
    """Marque une notification comme lue après confirmation utilisateur."""
    try:
        db.execute(text("""
            UPDATE rappel_ia SET statut = 'lu' WHERE id = :id
        """), {"id": rappel_id})
        db.commit()
        print(f"[RAPPEL] Notification {rappel_id} marquée comme lue.")
        return {"succes": True}
    except Exception as e:
        return {"succes": False, "detail": str(e)}

# ANALYSE FICHIER BULLETIN (OCR)

async def _analyser_fichier_bulletin(
    fichier_base64: str,
    fichier_nom: str,
    api_key: str
) -> str:
    """
    Analyse un bulletin uploadé par l'utilisateur via GPT-4o vision.
    Retourne une explication pédagogique des lignes du bulletin.
    """
    try:
        # Détecter si PDF
        est_pdf = fichier_nom.lower().endswith(".pdf")

        if est_pdf:
            try:
                from pdf2image import convert_from_bytes
                import base64
                from io import BytesIO
                pdf_bytes = base64.b64decode(fichier_base64)
                pages = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
                img_buf = BytesIO()
                pages[0].save(img_buf, format="JPEG")
                image_b64 = base64.b64encode(img_buf.getvalue()).decode("utf-8")
            except Exception:
                return "Document PDF fourni mais conversion impossible."
        else:
            image_b64 = fichier_base64

        payload_vision = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyse ce bulletin de paie et explique chaque ligne "
                                "en langage simple et professionnel. "
                                "Pour chaque élément (salaire de base, primes, cotisations, IR...) :\n"
                                "1. Explique à quoi ça correspond\n"
                                "2. Donne le montant exact visible\n"
                                "3. Signale si quelque chose semble anormal\n"
                                "Réponds en français, sans jargon technique excessif."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        }
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            rep = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload_vision
            )
            data = rep.json()
            if "choices" in data:
                return f"ANALYSE BULLETIN UPLOADÉ :\n{data['choices'][0]['message']['content']}"
            return "Analyse du document impossible."

    except Exception as e:
        return f"Erreur analyse fichier : {str(e)}"