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

