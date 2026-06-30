from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date
from typing import Optional
import json
import uuid as _uuid

# 1. CONFIGURATION PAYS & COTISATIONS (lecture BDD)

def get_config_pays(db: Session) -> dict:
    """
    Lit la configuration de l'entreprise et les règles du pays depuis la BDD.
    Retourne un dict complet avec cotisations + tranches IR.
    """
    # Config entreprise
    config = db.execute(text("""
        SELECT ce.nom_entreprise, ce.devise, ce.jour_paie,
               p.id as pays_id, p.code as pays_code, p.libelle as pays_nom
        FROM config_entreprise ce
        LEFT JOIN pays p ON ce.pays_id = p.id
        WHERE ce.actif = TRUE
        LIMIT 1
    """)).fetchone()

    if not config:
        raise ValueError("Aucune configuration d'entreprise trouvée en BDD.")

    pays_id = config[3]

    # Cotisations du pays
    cotisations_raw = db.execute(text("""
        SELECT libelle, code, taux_salarial, taux_patronal,
               plafond, base_calcul, description
        FROM cotisation_ref
        WHERE pays_id = :pays_id
    """), {"pays_id": pays_id}).fetchall()

    cotisations = [
        {
            "libelle": r[0], "code": r[1],
            "taux_salarial": float(r[2]) if r[2] else 0,
            "taux_patronal": float(r[3]) if r[3] else 0,
            "plafond": float(r[4]) if r[4] else None,
            "base_calcul": r[5] or "salaire_brut",
            "description": r[6]
        }
        for r in cotisations_raw
    ]

    # Tranches IR du pays
    tranches_raw = db.execute(text("""
        SELECT montant_min, montant_max, taux, est_annuel
        FROM tranche_ir
        WHERE pays_id = :pays_id
        ORDER BY montant_min
    """), {"pays_id": pays_id}).fetchall()

    tranches_ir = [
        {
            "min": float(r[0]),
            "max": float(r[1]) if r[1] else None,
            "taux": float(r[2]),
            "est_annuel": r[3]
        }
        for r in tranches_raw
    ]

    return {
        "nom_entreprise": config[0],
        "devise": config[1],
        "jour_paie": config[2],
        "pays_id": pays_id,
        "pays_code": config[4],
        "pays_nom": config[5],
        "cotisations": cotisations,
        "tranches_ir": tranches_ir
    }


# 2. MOTEUR DE CALCUL PRINCIPAL

def _resoudre_employe_id(db: Session, employe_id: str) -> str:
    if not employe_id or str(employe_id).strip() == "":
        raise ValueError("Identifiant employé manquant.")
    try:
        _uuid.UUID(str(employe_id))
        return str(employe_id)
    except ValueError:
        pass
    result = db.execute(text("""
        SELECT id FROM employe
        WHERE LOWER(nom) = LOWER(:val)
           OR LOWER(prenom) = LOWER(:val)
           OR LOWER(CONCAT(prenom, ' ', nom)) = LOWER(:val)
           OR LOWER(CONCAT(nom, ' ', prenom)) = LOWER(:val)
           OR matricule = :val
        LIMIT 1
    """), {"val": str(employe_id).strip()}).scalar()
    if result:
        return str(result)
    raise ValueError(f"Employé '{employe_id}' introuvable.")


def calculer_salaire_complet(
    db: Session,
    employe_id: str,
    mois: int,
    annee: int,
    salaire_brut_override: Optional[float] = None
) -> dict:
    """
    Calcule le salaire net complet d'un employé pour un mois donné.
    Prend en compte : absences, primes, cotisations BDD, tranches IR du pays.
    Retourne un dict détaillé utilisable pour générer le bulletin.
    """

    #  Données employé 
    employe_id = _resoudre_employe_id(db, employe_id)
    emp = db.execute(text("""
        SELECT e.id, e.matricule, e.nom, e.prenom,
               e.salaire_base_contrat, e.situation_matrimoniale,
               e.nombre_enfants, e.nombre_parts_fiscales,
               e.email_perso, e.date_embauche,
               p.libelle as poste, d.nom as departement,
               c.type_contrat
        FROM employe e
        LEFT JOIN poste p ON e.poste_id = p.id
        LEFT JOIN departement d ON e.departement_id = d.id
        LEFT JOIN contrat c ON c.employe_id = e.id AND c.statut_actif = TRUE
        WHERE e.id = :id
        LIMIT 1
    """), {"id": employe_id}).fetchone()

    if not emp:
        raise ValueError(f"Employé introuvable : {employe_id}")

    salaire_base = salaire_brut_override if salaire_brut_override else float(emp[4] or 0)
    nombre_parts = float(emp[7] or 1.0)

    #  Primes depuis element_paie ─
    prime_transport = 0.0
    prime_logement = 0.0
    prime_autres = 0.0

    primes_raw = db.execute(text("""
        SELECT code, libelle, montant_fixe, taux
        FROM element_paie
        WHERE type = 'gain' AND est_actif = TRUE AND code != 'SAL_BASE'
    """)).fetchall()

    for prime in primes_raw:
        code, libelle, montant_fixe, taux = prime[0], prime[1], prime[2], prime[3]
        montant = float(montant_fixe) if montant_fixe else 0.0
        if taux and montant == 0:
            montant = salaire_base * float(taux) / 100

        if code == 'PRIME_TRANSP':
            prime_transport = montant
        elif code == 'PRIME_LOG':
            prime_logement = montant
        else:
            prime_autres += montant

    #  Absences du mois ─
    absences = db.execute(text("""
        SELECT type, date_debut, date_fin, statut
        FROM absence_conge
        WHERE employe_id = :emp_id
          AND statut = 'approuve'
          AND EXTRACT(MONTH FROM date_debut) = :mois
          AND EXTRACT(YEAR FROM date_debut) = :annee
    """), {"emp_id": employe_id, "mois": mois, "annee": annee}).fetchall()

    jours_absence_injustifiee = 0
    jours_conge_non_paye = 0

    for abs in absences:
        type_abs = abs[0]
        debut = abs[1]
        fin = abs[2]
        nb_jours = (fin - debut).days + 1 if isinstance(debut, date) else 0

        if type_abs == 'absence_injustifiee':
            jours_absence_injustifiee += nb_jours
        elif type_abs == 'conge_non_paye':
            jours_conge_non_paye += nb_jours

    # Déduction absences (base 26 jours ouvrables/mois)
    jours_ouvrables = 26
    taux_journalier = salaire_base / jours_ouvrables
    retenue_absence = (jours_absence_injustifiee + jours_conge_non_paye) * taux_journalier

    #  Salaire brut total ─
    salaire_brut_total = (
        salaire_base
        + prime_transport
        + prime_logement
        + prime_autres
        - retenue_absence
    )

    #  Config pays & cotisations 
    config = get_config_pays(db)
    cotisations = config["cotisations"]
    tranches_ir = config["tranches_ir"]
    devise = config["devise"]

    #  Calcul cotisations salariales 
    total_cotisations_salariales = 0.0
    total_cotisations_patronales = 0.0
    detail_cotisations = []

    ipres_salariale = 0.0
    css_pf = 0.0
    css_at = 0.0
    cfe = 0.0

    for cot in cotisations:
        base = salaire_brut_total
        if cot["plafond"]:
            base = min(base, cot["plafond"])

        montant_salarial = base * cot["taux_salarial"] / 100
        montant_patronal = base * cot["taux_patronal"] / 100

        total_cotisations_salariales += montant_salarial
        total_cotisations_patronales += montant_patronal

        # Identifier pour les colonnes dédiées
        code = cot["code"]
        if "IPRES" in code and cot["taux_salarial"] > 0:
            ipres_salariale += montant_salarial
        if code == "CSS_PF":
            css_pf = montant_patronal
        if code == "CSS_AT":
            css_at = montant_patronal
        if code == "CFE":
            cfe = montant_patronal

        detail_cotisations.append({
            "libelle": cot["libelle"],
            "code": code,
            "base": round(base, 2),
            "taux_salarial": cot["taux_salarial"],
            "taux_patronal": cot["taux_patronal"],
            "montant_salarial": round(montant_salarial, 2),
            "montant_patronal": round(montant_patronal, 2)
        })

    #  Calcul IR (tranches progressives) 
    # Base imposable = brut - cotisations salariales - abattement 30% plafonné
    base_imposable_mensuelle = salaire_brut_total - total_cotisations_salariales
    abattement = min(base_imposable_mensuelle * 0.30, 750000 / 12)
    base_ir_mensuelle = max(0, base_imposable_mensuelle - abattement)

    # Calcul annuel puis ramené au mois
    base_ir_annuelle = base_ir_mensuelle * 12

    ir_annuel = 0.0
    for tranche in tranches_ir:
        if base_ir_annuelle <= tranche["min"]:
            break
        plafond = tranche["max"] if tranche["max"] else float("inf")
        montant_dans_tranche = min(base_ir_annuelle, plafond) - tranche["min"]
        if montant_dans_tranche > 0:
            ir_annuel += montant_dans_tranche * tranche["taux"] / 100

    # Ajustement parts fiscales (réduction IR)
    if nombre_parts > 1:
        reduction = (nombre_parts - 1) * 0.10
        ir_annuel = ir_annuel * max(0, 1 - reduction)

    ir_mensuel = ir_annuel / 12

    #  Salaire net 
    salaire_net = salaire_brut_total - total_cotisations_salariales - ir_mensuel

    #  Résultat complet ─
    return {
        # Identification
        "employe_id": employe_id,
        "matricule": emp[1],
        "nom": emp[2],
        "prenom": emp[3],
        "poste": emp[10],
        "departement": emp[11],
        "email_perso": emp[8],
        "type_contrat": emp[12],
        "periode_mois": mois,
        "periode_annee": annee,

        # Gains
        "salaire_base": round(salaire_base, 2),
        "prime_transport": round(prime_transport, 2),
        "prime_logement": round(prime_logement, 2),
        "prime_autres": round(prime_autres, 2),
        "retenue_absence": round(retenue_absence, 2),
        "jours_absence": jours_absence_injustifiee + jours_conge_non_paye,
        "salaire_brut": round(salaire_brut_total, 2),

        # Cotisations
        "ipres_salariale": round(ipres_salariale, 2),
        "ir": round(ir_mensuel, 2),
        "total_cotisations_salariales": round(total_cotisations_salariales, 2),
        "ipres_patronale": round(
            sum(c["montant_patronal"] for c in detail_cotisations if "IPRES" in c["code"]), 2
        ),
        "css_pf": round(css_pf, 2),
        "css_at": round(css_at, 2),
        "cfe": round(cfe, 2),
        "total_cotisations_patronales": round(total_cotisations_patronales, 2),
        "detail_cotisations": detail_cotisations,

        # Net
        "salaire_net": round(salaire_net, 2),
        "devise": devise,
        "pays": config["pays_nom"]
    }

def calculer_salaire_generique(db: Session, salaire_brut: float) -> dict:
    config = get_config_pays(db)
    cotisations = config["cotisations"]
    tranches_ir = config["tranches_ir"]
    devise = config["devise"]

    total_sal = 0.0
    for cot in cotisations:
        base = salaire_brut
        if cot["plafond"]:
            base = min(base, cot["plafond"])
        total_sal += base * cot["taux_salarial"] / 100

    base_imposable = salaire_brut - total_sal
    abattement = min(base_imposable * 0.30, 750000 / 12)
    base_ir = max(0, base_imposable - abattement)
    base_ir_annuel = base_ir * 12

    ir_annuel = 0.0
    for t in tranches_ir:
        if base_ir_annuel <= t["min"]:
            break
        plafond = t["max"] if t["max"] else float("inf")
        dans_tranche = min(base_ir_annuel, plafond) - t["min"]
        if dans_tranche > 0:
            ir_annuel += dans_tranche * t["taux"] / 100

    ir = ir_annuel / 12
    net = salaire_brut - total_sal - ir

    return {
        "salaire_brut": round(salaire_brut, 2),
        "cotisations_salariales": round(total_sal, 2),
        "ir": round(ir, 2),
        "salaire_net": round(net, 2),
        "devise": devise
    }
# 3. ANALYSES PAIE (données réelles BDD)

def analyser_fiches_mois(db: Session, mois: int, annee: int) -> dict:
    """
    Retourne qui a eu une fiche et qui n'en a pas eu pour un mois donné.
    """
    # Tous les employés actifs
    employes_actifs = db.execute(text("""
        SELECT e.id, e.matricule, e.nom, e.prenom,
               p.libelle as poste, d.nom as departement,
               e.salaire_base_contrat
        FROM employe e
        LEFT JOIN poste p ON e.poste_id = p.id
        LEFT JOIN departement d ON e.departement_id = d.id
        WHERE e.actif = TRUE
        ORDER BY e.nom
    """)).fetchall()

    # Fiches existantes pour ce mois
    fiches_mois = db.execute(text("""
        SELECT employe_id, salaire_brut, salaire_net
        FROM fiche_paie
        WHERE periode_mois = :mois AND periode_annee = :annee
    """), {"mois": mois, "annee": annee}).fetchall()

    ids_avec_fiche = {str(f[0]): {"brut": float(f[1] or 0), "net": float(f[2] or 0)}
                      for f in fiches_mois}

    avec_fiche = []
    sans_fiche = []

    for e in employes_actifs:
        emp_id = str(e[0])
        info = {
            "id": emp_id,
            "matricule": e[1],
            "nom": e[2],
            "prenom": e[3],
            "poste": e[4],
            "departement": e[5],
            "salaire_base": float(e[6] or 0)
        }
        if emp_id in ids_avec_fiche:
            info.update(ids_avec_fiche[emp_id])
            avec_fiche.append(info)
        else:
            sans_fiche.append(info)

    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    return {
        "mois": mois,
        "annee": annee,
        "periode_label": f"{mois_noms[mois - 1]} {annee}",
        "total_actifs": len(employes_actifs),
        "avec_fiche": avec_fiche,
        "sans_fiche": sans_fiche,
        "nb_avec_fiche": len(avec_fiche),
        "nb_sans_fiche": len(sans_fiche),
        "complet": len(sans_fiche) == 0
    }


def detecter_irregularites(db: Session) -> dict:
    """
    Détecte les anomalies : doublons, incohérences brut/net, fiches mois courant manquantes.
    """
    irregularites = []

    # 1. Doublons (même employé, même mois, même année)
    doublons = db.execute(text("""
        SELECT employe_id, periode_mois, periode_annee, COUNT(*) as nb
        FROM fiche_paie
        GROUP BY employe_id, periode_mois, periode_annee
        HAVING COUNT(*) > 1
    """)).fetchall()

    for d in doublons:
        emp = db.execute(text(
            "SELECT nom, prenom, matricule FROM employe WHERE id = :id"
        ), {"id": d[0]}).fetchone()
        if emp:
            mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                         'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
            irregularites.append({
                "type": "DOUBLON",
                "severite": "HAUTE",
                "employe": f"{emp[1]} {emp[0]} ({emp[2]})",
                "detail": f"{d[3]} fiches pour {mois_noms[d[1]-1]} {d[2]}"
            })

    # 2. Incohérences brut/net (net > brut ou net < 50% du brut)
    incoherences = db.execute(text("""
        SELECT f.id, e.nom, e.prenom, e.matricule,
               f.salaire_brut, f.salaire_net,
               f.periode_mois, f.periode_annee
        FROM fiche_paie f
        LEFT JOIN employe e ON f.employe_id = e.id
        WHERE f.salaire_net > f.salaire_brut
           OR f.salaire_net < f.salaire_brut * 0.5
    """)).fetchall()

    for inc in incoherences:
        mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        irregularites.append({
            "type": "INCOHERENCE_SALAIRE",
            "severite": "MOYENNE",
            "employe": f"{inc[2]} {inc[1]} ({inc[3]})",
            "detail": (
                f"Brut: {float(inc[4]):,.0f} / Net: {float(inc[5]):,.0f} "
                f"pour {mois_noms[inc[6]-1]} {inc[7]}"
            )
        })

    # 3. Fiches mois courant manquantes
    now = datetime.now()
    analyse_mois = analyser_fiches_mois(db, now.month, now.year)
    if analyse_mois["sans_fiche"]:
        for emp in analyse_mois["sans_fiche"]:
            irregularites.append({
                "type": "FICHE_MANQUANTE",
                "severite": "INFO",
                "employe": f"{emp['prenom']} {emp['nom']} ({emp['matricule']})",
                "detail": f"Pas de fiche pour {analyse_mois['periode_label']}"
            })

    return {
        "nb_irregularites": len(irregularites),
        "irregularites": irregularites,
        "hautes": [i for i in irregularites if i["severite"] == "HAUTE"],
        "moyennes": [i for i in irregularites if i["severite"] == "MOYENNE"],
        "infos": [i for i in irregularites if i["severite"] == "INFO"]
    }


def statistiques_masse_salariale(db: Session) -> dict:
    """
    Statistiques complètes sur la masse salariale par département et globale.
    """
    # Global
    global_stats = db.execute(text("""
        SELECT
            COUNT(*) as nb_employes,
            SUM(salaire_base_contrat) as masse_base,
            AVG(salaire_base_contrat) as moyenne,
            MIN(salaire_base_contrat) as minimum,
            MAX(salaire_base_contrat) as maximum
        FROM employe WHERE actif = TRUE
    """)).fetchone()

    # Par département
    par_dept = db.execute(text("""
        SELECT d.nom, COUNT(e.id) as nb,
               SUM(e.salaire_base_contrat) as masse,
               AVG(e.salaire_base_contrat) as moyenne
        FROM employe e
        LEFT JOIN departement d ON e.departement_id = d.id
        WHERE e.actif = TRUE
        GROUP BY d.nom
        ORDER BY masse DESC
    """)).fetchall()

    # Employé avec le salaire le plus élevé
    top_salaire = db.execute(text("""
        SELECT e.nom, e.prenom, e.matricule, e.salaire_base_contrat,
               p.libelle as poste, d.nom as departement
        FROM employe e
        LEFT JOIN poste p ON e.poste_id = p.id
        LEFT JOIN departement d ON e.departement_id = d.id
        WHERE e.actif = TRUE
        ORDER BY e.salaire_base_contrat DESC
        LIMIT 5
    """)).fetchall()

    config = get_config_pays(db)

    return {
        "devise": config["devise"],
        "global": {
            "nb_employes": global_stats[0],
            "masse_salariale_base": round(float(global_stats[1] or 0), 2),
            "salaire_moyen": round(float(global_stats[2] or 0), 2),
            "salaire_minimum": round(float(global_stats[3] or 0), 2),
            "salaire_maximum": round(float(global_stats[4] or 0), 2)
        },
        "par_departement": [
            {
                "departement": r[0] or "Non défini",
                "nb_employes": r[1],
                "masse": round(float(r[2] or 0), 2),
                "moyenne": round(float(r[3] or 0), 2)
            }
            for r in par_dept
        ],
        "top_salaires": [
            {
                "nom": r[0], "prenom": r[1], "matricule": r[2],
                "salaire": round(float(r[3] or 0), 2),
                "poste": r[4], "departement": r[5]
            }
            for r in top_salaire
        ]
    }


def comparer_mois(db: Session, mois1: int, annee1: int, mois2: int, annee2: int) -> dict:
    """
    Compare la masse salariale et les fiches entre deux mois.
    """
    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    def get_stats_mois(mois, annee):
        r = db.execute(text("""
            SELECT COUNT(*), SUM(salaire_brut), SUM(salaire_net)
            FROM fiche_paie
            WHERE periode_mois = :mois AND periode_annee = :annee
        """), {"mois": mois, "annee": annee}).fetchone()
        return {
            "label": f"{mois_noms[mois-1]} {annee}",
            "nb_fiches": r[0] or 0,
            "masse_brute": round(float(r[1] or 0), 2),
            "masse_nette": round(float(r[2] or 0), 2)
        }

    stats1 = get_stats_mois(mois1, annee1)
    stats2 = get_stats_mois(mois2, annee2)

    evolution_brut = stats2["masse_brute"] - stats1["masse_brute"]
    evolution_net = stats2["masse_nette"] - stats1["masse_nette"]
    pct_brut = (evolution_brut / stats1["masse_brute"] * 100) if stats1["masse_brute"] > 0 else 0

    return {
        "periode_1": stats1,
        "periode_2": stats2,
        "evolution_brut": round(evolution_brut, 2),
        "evolution_net": round(evolution_net, 2),
        "evolution_pct": round(pct_brut, 2)
    }


# 4. SAUVEGARDE FICHE EN BDD

def sauvegarder_fiche_calculee(db: Session, calcul: dict) -> str:
    """
    Sauvegarde le résultat du moteur de calcul dans fiche_paie + lignes détail.
    Retourne l'ID de la fiche créée.
    """
    # Vérifier doublon
    existant = db.execute(text("""
        SELECT id FROM fiche_paie
        WHERE employe_id = :emp_id
          AND periode_mois = :mois
          AND periode_annee = :annee
        LIMIT 1
    """), {
        "emp_id": calcul["employe_id"],
        "mois": calcul["periode_mois"],
        "annee": calcul["periode_annee"]
    }).fetchone()

    if existant:
        raise ValueError(
            f"Une fiche existe déjà pour {calcul['prenom']} {calcul['nom']} "
            f"pour {calcul['periode_mois']}/{calcul['periode_annee']}."
        )

    # Insertion fiche principale
    result = db.execute(text("""
        INSERT INTO fiche_paie (
            employe_id, prenom_employe, nom_employe,
            periode_mois, periode_annee,
            salaire_brut, salaire_net,
            prime_transport, prime_logement, prime_autres,
            retenue_absence, ipres_salariale, ipres_patronale,
            ir, css_pf, css_at, cfe,
            est_envoyee
        ) VALUES (
            :emp_id, :prenom, :nom,
            :mois, :annee,
            :brut, :net,
            :prime_transport, :prime_logement, :prime_autres,
            :retenue_absence, :ipres_sal, :ipres_pat,
            :ir, :css_pf, :css_at, :cfe,
            FALSE
        ) RETURNING id
    """), {
        "emp_id": calcul["employe_id"],
        "prenom": calcul["prenom"],
        "nom": calcul["nom"],
        "mois": calcul["periode_mois"],
        "annee": calcul["periode_annee"],
        "brut": calcul["salaire_brut"],
        "net": calcul["salaire_net"],
        "prime_transport": calcul["prime_transport"],
        "prime_logement": calcul["prime_logement"],
        "prime_autres": calcul["prime_autres"],
        "retenue_absence": calcul["retenue_absence"],
        "ipres_sal": calcul["ipres_salariale"],
        "ipres_pat": calcul["ipres_patronale"],
        "ir": calcul["ir"],
        "css_pf": calcul["css_pf"],
        "css_at": calcul["css_at"],
        "cfe": calcul["cfe"]
    })

    fiche_id = str(result.fetchone()[0])

    # Insertion lignes détail (ligne_bulletin_paie)
    lignes = [
        ("SAL_BASE", "Salaire de base", "gain", calcul["salaire_base"], None, calcul["salaire_base"]),
    ]
    if calcul["prime_transport"] > 0:
        lignes.append(("PRIME_TRANSP", "Prime de transport", "gain", None, None, calcul["prime_transport"]))
    if calcul["prime_logement"] > 0:
        lignes.append(("PRIME_LOG", "Prime de logement", "gain", None, None, calcul["prime_logement"]))
    if calcul["prime_autres"] > 0:
        lignes.append(("PRIME_AUTRES", "Autres primes", "gain", None, None, calcul["prime_autres"]))
    if calcul["retenue_absence"] > 0:
        lignes.append(("RET_ABS", "Retenue absences", "retenue", None, None, -calcul["retenue_absence"]))
    if calcul["ipres_salariale"] > 0:
        lignes.append(("IPRES_SAL", "IPRES part salariale", "retenue",
                       calcul["salaire_brut"], None, -calcul["ipres_salariale"]))
    if calcul["ir"] > 0:
        lignes.append(("IR", "Impôt sur le Revenu", "retenue",
                       calcul["salaire_brut"], None, -calcul["ir"]))
    if calcul["ipres_patronale"] > 0:
        lignes.append(("IPRES_PAT", "IPRES part patronale", "cotisation",
                       calcul["salaire_brut"], None, calcul["ipres_patronale"]))
    if calcul["css_pf"] > 0:
        lignes.append(("CSS_PF", "CSS Prestations familiales", "cotisation",
                       calcul["salaire_brut"], None, calcul["css_pf"]))
    if calcul["css_at"] > 0:
        lignes.append(("CSS_AT", "CSS Accidents du travail", "cotisation",
                       calcul["salaire_brut"], None, calcul["css_at"]))
    if calcul["cfe"] > 0:
        lignes.append(("CFE", "Contribution forfaitaire", "cotisation",
                       calcul["salaire_brut"], None, calcul["cfe"]))

    for ordre, (code, libelle, type_l, base, taux, montant) in enumerate(lignes):
        db.execute(text("""
            INSERT INTO ligne_bulletin_paie
                (fiche_paie_id, code, libelle, type, base, taux, montant, ordre)
            VALUES
                (:fiche_id, :code, :libelle, :type, :base, :taux, :montant, :ordre)
        """), {
            "fiche_id": fiche_id, "code": code, "libelle": libelle,
            "type": type_l, "base": base, "taux": taux,
            "montant": montant, "ordre": ordre
        })

    db.commit()
    return fiche_id


# 5. LANCEMENT PAIE MASSE (tous les employés actifs)

def lancer_paie_masse(db: Session, mois: int, annee: int) -> dict:
    """
    Génère les fiches de paie pour tous les employés actifs d'un mois donné.
    Ignore les employés qui ont déjà une fiche.
    """
    employes_actifs = db.execute(text("""
        SELECT id FROM employe WHERE actif = TRUE
    """)).fetchall()

    resultats = {"generes": [], "ignores": [], "erreurs": []}

    for emp in employes_actifs:
        emp_id = str(emp[0])
        try:
            calcul = calculer_salaire_complet(db, emp_id, mois, annee)
            fiche_id = sauvegarder_fiche_calculee(db, calcul)
            resultats["generes"].append({
                "employe": f"{calcul['prenom']} {calcul['nom']}",
                "matricule": calcul["matricule"],
                "fiche_id": fiche_id,
                "salaire_net": calcul["salaire_net"]
            })
        except ValueError as e:
            if "existe déjà" in str(e):
                resultats["ignores"].append(emp_id)
            else:
                resultats["erreurs"].append({"employe_id": emp_id, "erreur": str(e)})
        except Exception as e:
            resultats["erreurs"].append({"employe_id": emp_id, "erreur": str(e)})

    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    return {
        "periode": f"{mois_noms[mois - 1]} {annee}",
        "nb_generes": len(resultats["generes"]),
        "nb_ignores": len(resultats["ignores"]),
        "nb_erreurs": len(resultats["erreurs"]),
        "detail": resultats
    }