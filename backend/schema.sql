-- 0. Extensions et Utilitaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 1. AUTHENTIFICATION
CREATE TABLE utilisateur (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    mot_de_passe TEXT NOT NULL, -- Ton hash sera ici
    nom VARCHAR(100),
    prenom VARCHAR(100),
    role VARCHAR(20) CHECK (role IN ('admin', 'client', 'rh')) DEFAULT 'client',
    telephone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. STRUCTURE ORGANISATIONNELLE
CREATE TABLE departement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE poste (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    libelle VARCHAR(100) NOT NULL UNIQUE
);

-- 3. GRH (MODIFIÉ : Champs Entreprise de haut niveau)
CREATE TABLE employe (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    utilisateur_id UUID REFERENCES utilisateur(id) ON DELETE SET NULL,
    matricule VARCHAR(50) UNIQUE NOT NULL,
    
    -- État civil & Identification
    civilite VARCHAR(10) CHECK (civilite IN ('M.', 'Mme', 'Mlle')),
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE NOT NULL,
    lieu_naissance VARCHAR(100),
    nationalite VARCHAR(50) DEFAULT 'Sénégalaise',
    num_cni VARCHAR(50), -- Carte Nationale d'Identité
    num_securite_sociale VARCHAR(50), -- IPRES/CSS
    
    -- Situation Familiale (Pour les formulaires complexes et la paie)
    situation_matrimoniale VARCHAR(50) CHECK (situation_matrimoniale IN ('Célibataire', 'Marié(e)', 'Veuf(ve)', 'Divorcé(e)')),
    nombre_enfants INT DEFAULT 0,
    nombre_parts_fiscales DECIMAL(3,1) DEFAULT 1.0,
    
    -- Contact & Adresse
    adresse_residentielle TEXT NOT NULL,
    ville VARCHAR(100) DEFAULT 'Dakar',
    quartier VARCHAR(100),
    telephone_perso VARCHAR(20),
    email_perso VARCHAR(255),
    
    -- Informations Bancaires
    nom_banque VARCHAR(100),
    rib_iban VARCHAR(100),
    
    -- Détails Professionnels
    poste_id UUID REFERENCES poste(id),
    departement_id UUID REFERENCES departement(id),
    date_embauche DATE NOT NULL,
    salaire_base_contrat DECIMAL(12,2) NOT NULL,
    actif BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. CONTRATS ET ABSENCES
CREATE TABLE contrat (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employe_id UUID REFERENCES employe(id) ON DELETE CASCADE,
    type_contrat VARCHAR(20) CHECK (type_contrat IN ('CDI', 'CDD', 'Stage')),
    date_debut DATE NOT NULL,
    date_fin DATE,
    statut_actif BOOLEAN DEFAULT TRUE
);

CREATE TABLE absence_conge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employe_id UUID REFERENCES employe(id) ON DELETE CASCADE,
    type VARCHAR(50) CHECK (type IN ('conge_paye', 'maladie', 'absence_injustifiee')),
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    statut VARCHAR(20) DEFAULT 'en_attente'
);

-- 5. PAIE
CREATE TABLE fiche_paie (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employe_id UUID REFERENCES employe(id) ON DELETE CASCADE,
    prenom_employe VARCHAR(100) NOT NULL,
    nom_employe VARCHAR(100) NOT NULL,
    periode_mois INT NOT NULL CHECK (periode_mois BETWEEN 1 AND 12),
    periode_annee INT NOT NULL,
    salaire_brut DECIMAL(12,2),
    salaire_net DECIMAL(12,2),
    date_generation TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. BOUTIQUE & OCR
CREATE TABLE categorie (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nom VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE produit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    categorie_id UUID REFERENCES categorie(id) ON DELETE SET NULL,
    nom VARCHAR(150) NOT NULL,
    prix_unitaire DECIMAL(12,2) NOT NULL,
    stock_actuel INT DEFAULT 0
);

CREATE TABLE document_ocr (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    utilisateur_id UUID REFERENCES utilisateur(id) ON DELETE SET NULL,
    nom_fichier VARCHAR(255),
    resultat_json JSONB,
    score_confiance DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS commande (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    utilisateur_id UUID REFERENCES utilisateur(id) ON DELETE SET NULL,
    statut VARCHAR(20) CHECK (statut IN ('en_attente', 'en_cours', 'livree', 'annulee')) DEFAULT 'en_attente',
    montant_total DECIMAL(12,2) NOT NULL,
    mode_paiement VARCHAR(20) CHECK (mode_paiement IN ('wave', 'orange_money', 'sur_place')),
    adresse_livraison TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- TRIGGERS pour updated_at
CREATE TRIGGER trg_upd_user BEFORE UPDATE ON utilisateur FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER trg_upd_emp BEFORE UPDATE ON employe FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();









-- A. UTILISATEURS
INSERT INTO utilisateur (email, mot_de_passe, nom, prenom, role, telephone) VALUES
('admin@poulet.app', '$2a$12$L0mASN1yvp7h4LouBzEq6OS9yymOUQScr77E.mTOk2.z6TK9qbrWG', 'Sarr', 'Moussa', 'admin', '+221771112233'),
('rh@poulet.app', '$2a$12$L0mASN1yvp7h4LouBzEq6OS9yymOUQScr77E.mTOk2.z6TK9qbrWG', 'Diop', 'Aminata', 'rh', '+221774445566');

-- B. STRUCTURE
INSERT INTO departement (nom) VALUES ('Direction'), ('Élevage'), ('Ventes'), ('Logistique');
INSERT INTO poste (libelle) VALUES ('Gérant'), ('Technicien Avicole'), ('Commercial Senior'), ('Livreur');

-- C. EMPLOYÉS (5 profils pour tester différents formulaires)
INSERT INTO employe (
    matricule, civilite, nom, prenom, date_naissance, lieu_naissance, 
    adresse_residentielle, ville, situation_matrimoniale, nombre_enfants, 
    num_securite_sociale, nom_banque, rib_iban, poste_id, 
    departement_id, date_embauche, salaire_base_contrat
) VALUES
(
    'EMP-001', 'M.', 'Sarr', 'Moussa', '1985-06-15', 'Dakar', 
    'Villa 10, Plateau', 'Dakar', 'Marié(e)', 3, 
    'CSS-12345', 'CBAO', 'SN012-00001-0123456789-22', 
    (SELECT id FROM poste WHERE libelle='Gérant'), 
    (SELECT id FROM departement WHERE nom='Direction'), '2024-01-01', 900000.00
),
(
    'EMP-002', 'M.', 'Fall', 'Ibrahima', '1992-03-20', 'Saint-Louis', 
    'HLM Grand Yoff', 'Dakar', 'Célibataire', 0, 
    'CSS-67890', 'BICIS', 'SN012-00001-9876543210-55', 
    (SELECT id FROM poste WHERE libelle='Technicien Avicole'), 
    (SELECT id FROM departement WHERE nom='Élevage'), '2025-02-10', 300000.00
),
(
    'EMP-003', 'Mme', 'Ndiaye', 'Awa', '1995-11-05', 'Thiès', 
    'Cité Keur Gorgui', 'Dakar', 'Marié(e)', 2, 
    'CSS-11223', 'Ecobank', 'SN012-00001-1122334455-88', 
    (SELECT id FROM poste WHERE libelle='Commercial Senior'), 
    (SELECT id FROM departement WHERE nom='Ventes'), '2025-05-15', 450000.00
),
(
    'EMP-004', 'M.', 'Gueye', 'Ousmane', '1988-09-12', 'Kaolack', 
    'Quartier Escale', 'Rufisque', 'Marié(e)', 4, 
    'CSS-44556', 'SGBS', 'SN012-00001-5566778899-11', 
    (SELECT id FROM poste WHERE libelle='Livreur'), 
    (SELECT id FROM departement WHERE nom='Logistique'), '2025-08-01', 250000.00
),
(
    'EMP-005', 'Mlle', 'Sow', 'Fatoumata', '1998-12-30', 'Ziguinchor', 
    'Almadies', 'Dakar', 'Célibataire', 0, 
    'CSS-99887', 'UBA', 'SN012-00001-0099887766-33', 
    (SELECT id FROM poste WHERE libelle='Technicien Avicole'), 
    (SELECT id FROM departement WHERE nom='Élevage'), '2026-01-15', 280000.00
);

-- 1. Ajout de la table RÉUNION
CREATE TABLE reunion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sujet VARCHAR(255) NOT NULL,
    date_heure TIMESTAMP WITH TIME ZONE NOT NULL,
    lieu VARCHAR(255), -- Peut contenir un lien Teams/Zoom ou une salle
    ordre_du_jour TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table de liaison pour les PARTICIPANTS (Many-to-Many)
CREATE TABLE participants_reunion (
    reunion_id UUID REFERENCES reunion(id) ON DELETE CASCADE,
    employe_id UUID REFERENCES employe(id) ON DELETE CASCADE,
    presence_confirmee BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (reunion_id, employe_id)
);

-- 3. Enrichissement de la table EMPLOYE (Champs manquants pour l'ERP)
ALTER TABLE employe 
ADD COLUMN IF NOT EXISTS departement_service VARCHAR(100),
ADD COLUMN IF NOT EXISTS niveau_etude VARCHAR(100),
ADD COLUMN IF NOT EXISTS competences TEXT, -- Stocke les compétences sous forme de liste texte
ADD COLUMN IF NOT EXISTS type_contrat_actuel VARCHAR(50);

-- 4. Ajout d'une table pour l'HISTORIQUE (Promotions/Changements)
CREATE TABLE historique_carriere (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employe_id UUID REFERENCES employe(id) ON DELETE CASCADE,
    ancien_poste VARCHAR(100),
    nouveau_poste VARCHAR(100),
    date_changement DATE DEFAULT CURRENT_DATE,
    motif TEXT
);

-- Index pour accélérer les recherches de l'IA
CREATE INDEX idx_emp_matricule ON employe(matricule);
CREATE INDEX idx_reunion_date ON reunion(date_heure);

-- Une conversation = une session de chat
CREATE TABLE conversation_ia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    titre VARCHAR(255),          -- généré du 1er message user
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Chaque message de la conversation
CREATE TABLE message_ia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversation_ia(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,   -- 'user' ou 'assistant'
    content TEXT NOT NULL,
    action VARCHAR(50),          -- 'OUVRIR_FORMULAIRE', 'REUNION_CREEE', null
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour accélérer les recherches par session
CREATE INDEX IF NOT EXISTS idx_conv_session ON conversation_ia(session_id);
CREATE INDEX IF NOT EXISTS idx_msg_conversation ON message_ia(conversation_id);

-- Trigger pour updated_at
CREATE TRIGGER trg_upd_conv_ia
    BEFORE UPDATE ON conversation_ia
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();



-- Accorder les droits sur les tables de l'historique IA
GRANT ALL PRIVILEGES ON TABLE conversation_ia TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE message_ia TO poulet_admin;

-- Accorder les droits sur les tables de réunions (pour éviter un futur crash)
GRANT ALL PRIVILEGES ON TABLE reunion TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE participants_reunion TO poulet_admin;

-- Important : Accorder les droits sur toutes les séquences 
-- (nécessaire pour l'auto-incrémentation des IDs si présents)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO poulet_admin;


-- Donne les droits sur TOUTES les tables nécessaires
GRANT ALL PRIVILEGES ON TABLE conversation_ia TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE message_ia TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE reunion TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE participants_reunion TO poulet_admin;

-- Donne les droits sur les séquences (indispensable pour l'insertion)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO poulet_admin;




-- Ajout des modifications que Monsieur Christian m'a demandé de rajouter à la base

-- ============================================================
-- 1. TABLES DE RÉFÉRENCE (sans FK d'abord)
-- ============================================================

CREATE TABLE IF NOT EXISTS type_salaire (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS categorie_socioprofessionnelle (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS echelon (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS diplome (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS ville_ref (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code_postal VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS cotisation_ref (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    taux DECIMAL(18,2),
    description TEXT
);

CREATE TABLE IF NOT EXISTS type_contrat_ref (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS categorie_professionnelle (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS classe_legale (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS shift (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS motif (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS type_rupture (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS equipe (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS grade (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS titre (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS statut_contrat (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS zone_residence (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS zone_categorielle (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS lieu (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS plan_analytique (
    id VARCHAR(50) PRIMARY KEY,
    libelle VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS plan_budgetaire (
    id VARCHAR(50) PRIMARY KEY,
    libelle VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS plan_geographique (
    id VARCHAR(50) PRIMARY KEY,
    libelle VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS plan_comptable (
    id VARCHAR(50) PRIMARY KEY,
    libelle VARCHAR(255),
    type VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS plan_convention (
    id VARCHAR(10) PRIMARY KEY,
    libelle VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS plan_categorie (
    id VARCHAR(10) PRIMARY KEY,
    libelle VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS plan_souscategorie (
    id VARCHAR(10) PRIMARY KEY,
    libelle VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS mode_bulletin (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS mode_paiement_ref (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(100) NOT NULL,
    code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS etat_civil (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS chaine_traitement_bulletin (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(255) NOT NULL,
    code VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS element_paie (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) NOT NULL UNIQUE,
    libelle VARCHAR(255) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('gain', 'retenue', 'cotisation', 'information')),
    formule TEXT,
    taux DECIMAL(18,2),
    montant_fixe DECIMAL(18,2),
    est_actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. ENRICHISSEMENT DE LA TABLE EMPLOYE
-- ============================================================

ALTER TABLE employe
    ADD COLUMN IF NOT EXISTS diplome_id INT REFERENCES diplome(id),
    ADD COLUMN IF NOT EXISTS nombre_parts DECIMAL(18,2),
    ADD COLUMN IF NOT EXISTS est_en_detachement BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS est_expatrie BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS est_retraite BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS taux_horaire DECIMAL(18,2),
    ADD COLUMN IF NOT EXISTS type_salaire_id INT REFERENCES type_salaire(id),
    ADD COLUMN IF NOT EXISTS categorie_sociopro_id INT REFERENCES categorie_socioprofessionnelle(id),
    ADD COLUMN IF NOT EXISTS echelon_id INT REFERENCES echelon(id),
    ADD COLUMN IF NOT EXISTS ville_residence_id INT REFERENCES ville_ref(id),
    ADD COLUMN IF NOT EXISTS ville_embauche_id INT REFERENCES ville_ref(id),
    ADD COLUMN IF NOT EXISTS ville_recrutement_id INT REFERENCES ville_ref(id),
    ADD COLUMN IF NOT EXISTS mode_paiement_id INT REFERENCES mode_paiement_ref(id),
    ADD COLUMN IF NOT EXISTS etat_civil_id INT REFERENCES etat_civil(id),
    ADD COLUMN IF NOT EXISTS est_osie BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS charge DECIMAL(18,2),
    ADD COLUMN IF NOT EXISTS fichier VARCHAR(255),
    ADD COLUMN IF NOT EXISTS date_affectation TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS code_postal VARCHAR(20),
    ADD COLUMN IF NOT EXISTS chaine_traitement_bulletin_id INT REFERENCES chaine_traitement_bulletin(id),
    ADD COLUMN IF NOT EXISTS date_depart_retraite TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS carte_travail VARCHAR(13),
    ADD COLUMN IF NOT EXISTS matricule_fonctionnaire VARCHAR(13),
    ADD COLUMN IF NOT EXISTS sexe VARCHAR(6);


-- ============================================================
-- 3. ENRICHISSEMENT DE LA TABLE CONTRAT
-- ============================================================

ALTER TABLE contrat
    ADD COLUMN IF NOT EXISTS numero_contrat VARCHAR(50),
    ADD COLUMN IF NOT EXISTS salaire DECIMAL(18,5),
    ADD COLUMN IF NOT EXISTS netp DECIMAL(18,2),
    ADD COLUMN IF NOT EXISTS mode_bulletin_id INT REFERENCES mode_bulletin(id),
    ADD COLUMN IF NOT EXISTS mode_paiement_id INT REFERENCES mode_paiement_ref(id),
    ADD COLUMN IF NOT EXISTS plan_analytique_id VARCHAR(50) REFERENCES plan_analytique(id),
    ADD COLUMN IF NOT EXISTS plan_budgetaire_id VARCHAR(50) REFERENCES plan_budgetaire(id),
    ADD COLUMN IF NOT EXISTS plan_geographique_id VARCHAR(50) REFERENCES plan_geographique(id),
    ADD COLUMN IF NOT EXISTS plan6_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS plan7_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS plan8_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS financement_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS plan_comptable_brut_id VARCHAR(50) REFERENCES plan_comptable(id),
    ADD COLUMN IF NOT EXISTS plan_comptable_net_id VARCHAR(50) REFERENCES plan_comptable(id),
    ADD COLUMN IF NOT EXISTS solde_conge DECIMAL(18,2),
    ADD COLUMN IF NOT EXISTS date_solde TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS horaire_hebdomadaire DECIMAL(18,2),
    ADD COLUMN IF NOT EXISTS jours_ouvrables DECIMAL(18,2),
    ADD COLUMN IF NOT EXISTS matricule_precedent VARCHAR(50),
    ADD COLUMN IF NOT EXISTS est_rupture BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS est_detachement BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS est_expatrie BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS shift_id INT REFERENCES shift(id),
    ADD COLUMN IF NOT EXISTS categorie_professionnelle_id INT REFERENCES categorie_professionnelle(id),
    ADD COLUMN IF NOT EXISTS classe_legale_id INT REFERENCES classe_legale(id),
    ADD COLUMN IF NOT EXISTS motif_id INT REFERENCES motif(id),
    ADD COLUMN IF NOT EXISTS type_rupture_id INT REFERENCES type_rupture(id),
    ADD COLUMN IF NOT EXISTS equipe_id INT REFERENCES equipe(id),
    ADD COLUMN IF NOT EXISTS grade_id INT REFERENCES grade(id),
    ADD COLUMN IF NOT EXISTS titre_id INT REFERENCES titre(id),
    ADD COLUMN IF NOT EXISTS statut_id INT REFERENCES statut_contrat(id),
    ADD COLUMN IF NOT EXISTS zone_residence_id INT REFERENCES zone_residence(id),
    ADD COLUMN IF NOT EXISTS zone_categorielle_id INT REFERENCES zone_categorielle(id),
    ADD COLUMN IF NOT EXISTS lieu_id INT REFERENCES lieu(id),
    ADD COLUMN IF NOT EXISTS date_confirmation TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS date_decision TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS date_effet TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS commentaire VARCHAR(255),
    ADD COLUMN IF NOT EXISTS poste_id UUID REFERENCES poste(id),
    ADD COLUMN IF NOT EXISTS fonction_id INT,
    ADD COLUMN IF NOT EXISTS ville_id INT REFERENCES ville_ref(id);


-- ============================================================
-- 4. NOUVELLES TABLES PRINCIPALES
-- ============================================================

-- Compte bancaire employé (TPAI_EMPLOYECOMPTE)
CREATE TABLE IF NOT EXISTS employe_compte (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employe_id UUID NOT NULL REFERENCES employe(id) ON DELETE CASCADE,
    banque VARCHAR(255),
    banque_id INT,
    date_cloture TIMESTAMP WITH TIME ZONE,
    date_creation TIMESTAMP WITH TIME ZONE,
    type_compte_id INT,
    libelle VARCHAR(255),
    code_banque VARCHAR(10),
    agence VARCHAR(255),
    guichet VARCHAR(5),
    compte VARCHAR(20),
    clerib VARCHAR(2),
    iban VARCHAR(50),
    swift VARCHAR(50),
    titulaire VARCHAR(255),
    taux DECIMAL(30,9),
    usercre VARCHAR(255),
    usermaj VARCHAR(255),
    datecre TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    datemaj TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Conjoint employé (TPAI_EMPLOYECONJOINT)
CREATE TABLE IF NOT EXISTS employe_conjoint (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employe_id UUID NOT NULL REFERENCES employe(id) ON DELETE CASCADE,
    nom VARCHAR(255),
    numero_ordre INT NOT NULL DEFAULT 1,
    date_naissance TIMESTAMP WITH TIME ZONE,
    emploi VARCHAR(255),
    usercre VARCHAR(255),
    usermaj VARCHAR(255),
    datecre TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    datemaj TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cotisation employé (TPAI_EMPLOYECOTISATION)
CREATE TABLE IF NOT EXISTS employe_cotisation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employe_id UUID NOT NULL REFERENCES employe(id) ON DELETE CASCADE,
    cotisation_id INT NOT NULL REFERENCES cotisation_ref(id),
    numero_affiliation VARCHAR(50),
    est_cotisant BOOLEAN NOT NULL DEFAULT TRUE,
    usercre VARCHAR(255),
    usermaj VARCHAR(255),
    datecre TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    datemaj TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Note employé (TPAI_EMPLOYENOTE)
CREATE TABLE IF NOT EXISTS employe_note (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employe_id UUID NOT NULL REFERENCES employe(id) ON DELETE CASCADE,
    contrat_id UUID REFERENCES contrat(id) ON DELETE SET NULL,
    utilisateurs VARCHAR(50),
    date_avis TIMESTAMP WITH TIME ZONE NOT NULL,
    mois INT,
    annee INT,
    indice INT,
    commentaires VARCHAR(255),
    usercre VARCHAR(255),
    usermaj VARCHAR(255),
    datecre TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    datemaj TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Champ personnalisé employé (TPAI_EMPLOYEXCHAMP)
CREATE TABLE IF NOT EXISTS employe_champ_personnalise (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employe_id UUID NOT NULL REFERENCES employe(id) ON DELETE CASCADE,
    libelle VARCHAR(255) NOT NULL,
    valeur VARCHAR(100),
    type_champ VARCHAR(10) NOT NULL,
    code_composante VARCHAR(15) NOT NULL,
    usercre VARCHAR(255),
    usermaj VARCHAR(255),
    datecre TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    datemaj TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Financement contrat (TPAI_EMPLOYECONTRATFINANCEMENT)
CREATE TABLE IF NOT EXISTS contrat_financement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contrat_id UUID NOT NULL REFERENCES contrat(id) ON DELETE CASCADE,
    taux FLOAT NOT NULL,
    plan_convention_id VARCHAR(10) REFERENCES plan_convention(id),
    plan_categorie_id VARCHAR(10) REFERENCES plan_categorie(id),
    plan_souscategorie_id VARCHAR(10) REFERENCES plan_souscategorie(id),
    usercre VARCHAR(255),
    usermaj VARCHAR(255),
    datecre TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    datemaj TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ligne détail bulletin de paie
CREATE TABLE IF NOT EXISTS ligne_bulletin_paie (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fiche_paie_id UUID NOT NULL REFERENCES fiche_paie(id) ON DELETE CASCADE,
    element_paie_id UUID REFERENCES element_paie(id),
    code VARCHAR(50),
    libelle VARCHAR(255) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('gain', 'retenue', 'cotisation', 'information')),
    base DECIMAL(18,2),
    taux DECIMAL(18,4),
    montant DECIMAL(18,2) NOT NULL,
    ordre INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 5. DONNÉES DE BASE POUR LES TABLES DE RÉFÉRENCE
-- ============================================================

INSERT INTO type_salaire (libelle, code) VALUES
    ('Mensuel', 'MENS'),
    ('Horaire', 'HOR'),
    ('Journalier', 'JOUR')
ON CONFLICT DO NOTHING;

INSERT INTO categorie_socioprofessionnelle (libelle, code) VALUES
    ('Cadre', 'CAD'),
    ('Agent de maîtrise', 'AM'),
    ('Employé', 'EMP'),
    ('Ouvrier', 'OUV')
ON CONFLICT DO NOTHING;

INSERT INTO echelon (libelle, code) VALUES
    ('Échelon 1', 'E1'),
    ('Échelon 2', 'E2'),
    ('Échelon 3', 'E3'),
    ('Échelon 4', 'E4'),
    ('Échelon 5', 'E5')
ON CONFLICT DO NOTHING;

INSERT INTO diplome (libelle, code) VALUES
    ('Aucun diplôme', 'AUCUN'),
    ('BFEM', 'BFEM'),
    ('Baccalauréat', 'BAC'),
    ('BTS / DUT', 'BTS'),
    ('Licence', 'LIC'),
    ('Master', 'MST'),
    ('Doctorat', 'DOC')
ON CONFLICT DO NOTHING;

INSERT INTO cotisation_ref (libelle, code, taux, description) VALUES
    ('IPRES Régime Général', 'IPRES_RG', 14.00, 'Retraite régime général - Part salariale 5.6%, patronale 8.4%'),
    ('IPRES Cadre', 'IPRES_CAD', 6.00, 'Retraite cadres'),
    ('CSS Prestation Familiale', 'CSS_PF', 7.00, 'Caisse de Sécurité Sociale - prestations familiales'),
    ('CSS Accident Travail', 'CSS_AT', 3.00, 'Caisse de Sécurité Sociale - accidents du travail'),
    ('Impôt sur le Revenu', 'IR', 0.00, 'Impôt sur le revenu - taux progressif'),
    ('Contribution Forfaitaire', 'CFE', 3.00, 'Contribution forfaitaire à la charge de l''employeur')
ON CONFLICT DO NOTHING;

INSERT INTO mode_paiement_ref (libelle, code) VALUES
    ('Virement bancaire', 'VIR'),
    ('Espèces', 'ESP'),
    ('Chèque', 'CHQ'),
    ('Mobile Money', 'MOB')
ON CONFLICT DO NOTHING;

INSERT INTO mode_bulletin (libelle) VALUES
    ('Bulletin mensuel'),
    ('Bulletin exceptionnel'),
    ('Solde de tout compte')
ON CONFLICT DO NOTHING;

INSERT INTO etat_civil (libelle) VALUES
    ('Célibataire'),
    ('Marié(e)'),
    ('Veuf(ve)'),
    ('Divorcé(e)')
ON CONFLICT DO NOTHING;

INSERT INTO element_paie (code, libelle, type, montant_fixe) VALUES
    ('SAL_BASE', 'Salaire de base', 'gain', NULL),
    ('PRIME_TRANSP', 'Prime de transport', 'gain', 26000),
    ('PRIME_LOG', 'Prime de logement', 'gain', NULL),
    ('PRIME_RESP', 'Prime de responsabilité', 'gain', NULL),
    ('HEURES_SUP', 'Heures supplémentaires', 'gain', NULL),
    ('IPRES_SAL', 'IPRES part salariale', 'retenue', NULL),
    ('IR', 'Impôt sur le revenu', 'retenue', NULL),
    ('IPRES_PAT', 'IPRES part patronale', 'cotisation', NULL),
    ('CSS_PF', 'CSS Prestations familiales', 'cotisation', NULL),
    ('CSS_AT', 'CSS Accidents du travail', 'cotisation', NULL),
    ('CFE', 'Contribution forfaitaire', 'cotisation', NULL)
ON CONFLICT (code) DO NOTHING;

INSERT INTO ville_ref (libelle, code_postal) VALUES
    ('Dakar', '10000'),
    ('Thiès', '21000'),
    ('Saint-Louis', '32000'),
    ('Kaolack', '72000'),
    ('Ziguinchor', '82000'),
    ('Rufisque', '14000'),
    ('Mbour', '22000')
ON CONFLICT DO NOTHING;


-- ============================================================
-- 6. DROITS POUR poulet_admin
-- ============================================================

GRANT ALL PRIVILEGES ON TABLE type_salaire TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE categorie_socioprofessionnelle TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE echelon TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE diplome TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE ville_ref TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE cotisation_ref TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE type_contrat_ref TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE categorie_professionnelle TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE classe_legale TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE shift TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE motif TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE type_rupture TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE equipe TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE grade TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE titre TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE statut_contrat TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE zone_residence TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE zone_categorielle TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE lieu TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE plan_analytique TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE plan_budgetaire TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE plan_geographique TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE plan_comptable TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE plan_convention TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE plan_categorie TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE plan_souscategorie TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE mode_bulletin TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE mode_paiement_ref TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE etat_civil TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE chaine_traitement_bulletin TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE element_paie TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE employe_compte TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE employe_conjoint TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE employe_cotisation TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE employe_note TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE employe_champ_personnalise TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE contrat_financement TO poulet_admin;
GRANT ALL PRIVILEGES ON TABLE ligne_bulletin_paie TO poulet_admin;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO poulet_admin;


-- ============================================================
-- 7. INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_employe_compte_employe ON employe_compte(employe_id);
CREATE INDEX IF NOT EXISTS idx_employe_conjoint_employe ON employe_conjoint(employe_id);
CREATE INDEX IF NOT EXISTS idx_employe_cotisation_employe ON employe_cotisation(employe_id);
CREATE INDEX IF NOT EXISTS idx_employe_note_employe ON employe_note(employe_id);
CREATE INDEX IF NOT EXISTS idx_employe_champ_employe ON employe_champ_personnalise(employe_id);
CREATE INDEX IF NOT EXISTS idx_contrat_financement_contrat ON contrat_financement(contrat_id);
CREATE INDEX IF NOT EXISTS idx_ligne_bulletin_fiche ON ligne_bulletin_paie(fiche_paie_id);
CREATE INDEX IF NOT EXISTS idx_element_paie_code ON element_paie(code);

ALTER TABLE fiche_paie
ADD COLUMN IF NOT EXISTS fichier_pdf VARCHAR(255),
ADD COLUMN IF NOT EXISTS note_changement TEXT,
ADD COLUMN IF NOT EXISTS est_envoyee BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS date_envoi TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS prime_transport DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS prime_logement DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS prime_autres DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS retenue_absence DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS ipres_salariale DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS ipres_patronale DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS ir DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS css_pf DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS css_at DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS cfe DECIMAL(12,2) DEFAULT 0;

CREATE TABLE IF NOT EXISTS config_paie (
    id SERIAL PRIMARY KEY,
    jour_declenchement INT DEFAULT 28,
    heure_declenchement TIME DEFAULT '23:00:00',
    actif BOOLEAN DEFAULT TRUE,
    derniere_execution TIMESTAMP WITH TIME ZONE,
    prochain_run TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Une seule ligne de config
INSERT INTO config_paie (jour_declenchement, heure_declenchement)
VALUES (28, '23:00:00');

CREATE TABLE IF NOT EXISTS log_paie (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type_execution VARCHAR(20) CHECK (type_execution IN ('automatique', 'manuelle', 'test')),
    periode_mois INT,
    periode_annee INT,
    nb_fiches_generees INT DEFAULT 0,
    nb_mails_envoyes INT DEFAULT 0,
    nb_erreurs INT DEFAULT 0,
    details JSONB,
    declenche_par VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pays (
    id SERIAL PRIMARY KEY,
    code VARCHAR(5) NOT NULL UNIQUE,  -- 'SN', 'CI', 'CM', 'FR'...
    libelle VARCHAR(100) NOT NULL,
    devise VARCHAR(20) DEFAULT 'FCFA',
    symbole_devise VARCHAR(5) DEFAULT 'FCFA'
);

ALTER TABLE cotisation_ref
ADD COLUMN pays_id INT REFERENCES pays(id),
ADD COLUMN taux_salarial DECIMAL(18,4) DEFAULT 0,
ADD COLUMN taux_patronal DECIMAL(18,4) DEFAULT 0,
ADD COLUMN plafond DECIMAL(18,2),
ADD COLUMN base_calcul VARCHAR(50) DEFAULT 'salaire_brut';

CREATE TABLE tranche_ir (
    id SERIAL PRIMARY KEY,
    pays_id INT REFERENCES pays(id),
    montant_min DECIMAL(18,2) NOT NULL,
    montant_max DECIMAL(18,2),  -- NULL = pas de plafond
    taux DECIMAL(5,2) NOT NULL,
    est_annuel BOOLEAN DEFAULT TRUE
);

CREATE TABLE config_entreprise (
    id SERIAL PRIMARY KEY,
    nom_entreprise VARCHAR(255),
    pays_id INT REFERENCES pays(id),
    devise VARCHAR(20),
    jour_paie INT DEFAULT 28,
    heure_paie TIME DEFAULT '23:00:00',
    actif BOOLEAN DEFAULT TRUE
);

UPDATE employe
SET email_perso = 'aminataorngom34@gmail.com'
WHERE matricule = 'EMP-001';

CREATE TABLE rappel_ia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(20) CHECK (type IN ('rappel', 'envoi_auto')),
    date_heure TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT NOT NULL,
    action JSONB,        -- contient les infos du mail à envoyer
    statut VARCHAR(20) DEFAULT 'en_attente',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);