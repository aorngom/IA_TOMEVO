-- =============================================
-- UTILISATEURS CLIENTS
-- =============================================
INSERT INTO utilisateur (email, mot_de_passe, nom, prenom, role, telephone) VALUES
('client1@gmail.com', '$2a$12$.MCS6nCQQ95/FDA1nyzgKOB6vGVeJgsisiBCQVkBbNxX.wW86C5k.', 'Diallo', 'Amadou', 'client', '+221771234567'),
('client2@gmail.com', '$2a$12$.MCS6nCQQ95/FDA1nyzgKOB6vGVeJgsisiBCQVkBbNxX.wW86C5k.', 'Ba', 'Mariama', 'client', '+221772345678'),
('client3@gmail.com', '$2a$12$.MCS6nCQQ95/FDA1nyzgKOB6vGVeJgsisiBCQVkBbNxX.wW86C5k.', 'Mbaye', 'Cheikh', 'client', '+221773456789'),
('client4@gmail.com', '$2a$12$.MCS6nCQQ95/FDA1nyzgKOB6vGVeJgsisiBCQVkBbNxX.wW86C5k.', 'Cissé', 'Rokhaya', 'client', '+221774567890'),
('client5@gmail.com', '$2a$12$.MCS6nCQQ95/FDA1nyzgKOB6vGVeJgsisiBCQVkBbNxX.wW86C5k.', 'Diouf', 'Pape', 'client', '+221775678901');

-- =============================================
-- CATÉGORIES PRODUITS
-- =============================================
INSERT INTO categorie (nom, description) VALUES
('Poulet entier', 'Poulets entiers prêts à cuisiner'),
('Découpes', 'Morceaux de poulet variés'),
('Abats', 'Foies, gésiers et cœurs de poulet'),
('Œufs', 'Œufs frais de poules pondeuses'),
('Produits transformés', 'Saucisses et nuggets de poulet maison');

-- =============================================
-- PRODUITS
-- =============================================
INSERT INTO produit (categorie_id, nom, prix_unitaire, stock_actuel) VALUES
((SELECT id FROM categorie WHERE nom='Poulet entier'), 'Poulet entier 1.5kg', 4500.00, 50),
((SELECT id FROM categorie WHERE nom='Poulet entier'), 'Poulet entier 2kg', 6000.00, 40),
((SELECT id FROM categorie WHERE nom='Poulet entier'), 'Poulet entier 2.5kg', 7500.00, 30),
((SELECT id FROM categorie WHERE nom='Découpes'), 'Cuisses de poulet x4', 3500.00, 60),
((SELECT id FROM categorie WHERE nom='Découpes'), 'Blanc de poulet x2', 4000.00, 45),
((SELECT id FROM categorie WHERE nom='Découpes'), 'Ailes de poulet x6', 2500.00, 70),
((SELECT id FROM categorie WHERE nom='Découpes'), 'Pilons x4', 2800.00, 55),
((SELECT id FROM categorie WHERE nom='Abats'), 'Foies de poulet 500g', 1500.00, 80),
((SELECT id FROM categorie WHERE nom='Abats'), 'Gésiers de poulet 500g', 1200.00, 75),
((SELECT id FROM categorie WHERE nom='Œufs'), 'Œufs frais x12', 2000.00, 100),
((SELECT id FROM categorie WHERE nom='Œufs'), 'Œufs frais x30', 4500.00, 60),
((SELECT id FROM categorie WHERE nom='Produits transformés'), 'Nuggets maison 500g', 3500.00, 40),
((SELECT id FROM categorie WHERE nom='Produits transformés'), 'Saucisses poulet x6', 3000.00, 35);

-- =============================================
-- CONTRATS EMPLOYÉS
-- =============================================
INSERT INTO contrat (employe_id, type_contrat, date_debut, date_fin, statut_actif) VALUES
((SELECT id FROM employe WHERE matricule='EMP-001'), 'CDI', '2024-01-01', NULL, TRUE),
((SELECT id FROM employe WHERE matricule='EMP-002'), 'CDD', '2025-02-10', '2026-02-09', TRUE),
((SELECT id FROM employe WHERE matricule='EMP-003'), 'CDI', '2025-05-15', NULL, TRUE),
((SELECT id FROM employe WHERE matricule='EMP-004'), 'CDD', '2025-08-01', '2026-07-31', TRUE),
((SELECT id FROM employe WHERE matricule='EMP-005'), 'Stage', '2026-01-15', '2026-07-15', TRUE);

-- =============================================
-- ABSENCES ET CONGÉS
-- =============================================
INSERT INTO absence_conge (employe_id, type, date_debut, date_fin, statut) VALUES
((SELECT id FROM employe WHERE matricule='EMP-001'), 'conge_paye', '2025-08-01', '2025-08-15', 'approuve'),
((SELECT id FROM employe WHERE matricule='EMP-002'), 'maladie', '2025-10-05', '2025-10-07', 'approuve'),
((SELECT id FROM employe WHERE matricule='EMP-003'), 'conge_paye', '2025-12-24', '2026-01-02', 'approuve'),
((SELECT id FROM employe WHERE matricule='EMP-004'), 'absence_injustifiee', '2025-11-15', '2025-11-15', 'refuse'),
((SELECT id FROM employe WHERE matricule='EMP-005'), 'maladie', '2026-02-10', '2026-02-12', 'en_attente'),
((SELECT id FROM employe WHERE matricule='EMP-001'), 'conge_paye', '2026-03-01', '2026-03-10', 'en_attente'),
((SELECT id FROM employe WHERE matricule='EMP-003'), 'maladie', '2026-01-20', '2026-01-21', 'approuve');

-- =============================================
-- FICHES DE PAIE
-- =============================================
INSERT INTO fiche_paie (employe_id, periode_mois, periode_annee, salaire_brut, salaire_net) VALUES
-- EMP-001 (Gérant - 900 000 FCFA)
((SELECT id FROM employe WHERE matricule='EMP-001'), 1, 2026, 900000.00, 756000.00),
((SELECT id FROM employe WHERE matricule='EMP-001'), 2, 2026, 900000.00, 756000.00),
((SELECT id FROM employe WHERE matricule='EMP-001'), 3, 2026, 900000.00, 756000.00),
-- EMP-002 (Technicien - 300 000 FCFA)
((SELECT id FROM employe WHERE matricule='EMP-002'), 1, 2026, 300000.00, 255000.00),
((SELECT id FROM employe WHERE matricule='EMP-002'), 2, 2026, 300000.00, 255000.00),
((SELECT id FROM employe WHERE matricule='EMP-002'), 3, 2026, 300000.00, 255000.00),
-- EMP-003 (Commercial - 450 000 FCFA)
((SELECT id FROM employe WHERE matricule='EMP-003'), 1, 2026, 450000.00, 382500.00),
((SELECT id FROM employe WHERE matricule='EMP-003'), 2, 2026, 450000.00, 382500.00),
((SELECT id FROM employe WHERE matricule='EMP-003'), 3, 2026, 450000.00, 382500.00),
-- EMP-004 (Livreur - 250 000 FCFA)
((SELECT id FROM employe WHERE matricule='EMP-004'), 1, 2026, 250000.00, 212500.00),
((SELECT id FROM employe WHERE matricule='EMP-004'), 2, 2026, 250000.00, 212500.00),
((SELECT id FROM employe WHERE matricule='EMP-004'), 3, 2026, 265000.00, 225250.00),
-- EMP-005 (Stagiaire - 280 000 FCFA)
((SELECT id FROM employe WHERE matricule='EMP-005'), 1, 2026, 280000.00, 238000.00),
((SELECT id FROM employe WHERE matricule='EMP-005'), 2, 2026, 280000.00, 238000.00),
((SELECT id FROM employe WHERE matricule='EMP-005'), 3, 2026, 280000.00, 238000.00);

-- =============================================
-- COMMANDES
-- =============================================
INSERT INTO commande (utilisateur_id, statut, montant_total, mode_paiement, adresse_livraison)
SELECT 
    u.id,
    statut,
    montant_total,
    mode_paiement,
    adresse_livraison
FROM (VALUES
    ('client1@gmail.com', 'livree', 10500.00, 'wave', 'Villa 12, Almadies, Dakar'),
    ('client2@gmail.com', 'en_cours', 6000.00, 'orange_money', 'HLM Grand Yoff, Dakar'),
    ('client3@gmail.com', 'livree', 4500.00, 'sur_place', NULL),
    ('client4@gmail.com', 'en_attente', 8500.00, 'wave', 'Cité Keur Gorgui, Dakar'),
    ('client5@gmail.com', 'annulee', 3500.00, 'orange_money', 'Plateau, Dakar'),
    ('client1@gmail.com', 'livree', 13500.00, 'wave', 'Villa 12, Almadies, Dakar'),
    ('client2@gmail.com', 'en_cours', 7500.00, 'sur_place', NULL),
    ('client3@gmail.com', 'en_attente', 5500.00, 'orange_money', 'Médina, Dakar')
) AS v(email, statut, montant_total, mode_paiement, adresse_livraison)
JOIN utilisateur u ON u.email = v.email;



INSERT INTO reunion (sujet, date_heure, lieu, ordre_du_jour) VALUES 
('Point Hebdomadaire Logistique', '2026-04-22 09:00:00+00', 'Salle de Conférence A', 'Suivi des livraisons, gestion des stocks et planning des chauffeurs.'),
('Comité de Direction - Stratégie Q3', '2026-04-25 14:30:00+00', 'Lien Teams: teams.microsoft.com/l/meetup-join/abc123...', 'Analyse des performances du trimestre, validation des budgets recrutement.');

-- On invite Abdoulaye Diallo (EMP-2026-009) à la réunion logistique
INSERT INTO participants_reunion (reunion_id, employe_id, presence_confirmee)
VALUES (
    (SELECT id FROM reunion WHERE sujet = 'Point Hebdomadaire Logistique' LIMIT 1),
    (SELECT id FROM employe WHERE matricule = 'EMP-2026-009' LIMIT 1),
    TRUE
);

-- On invite Mamadou Ndiaye (EMP-2026-005) à la même réunion
INSERT INTO participants_reunion (reunion_id, employe_id, presence_confirmee)
VALUES (
    (SELECT id FROM reunion WHERE sujet = 'Point Hebdomadaire Logistique' LIMIT 1),
    (SELECT id FROM employe WHERE matricule = 'EMP-2026-005' LIMIT 1),
    FALSE
);

UPDATE employe 
SET 
    departement_service = 'Opérations Terrain',
    niveau_etude = 'Baccalauréat',
    competences = 'Conduite poids lourd, Logistique urbaine, Maintenance préventive',
    type_contrat_actuel = 'CDI'
WHERE matricule = 'EMP-2026-009';

UPDATE employe 
SET 
    departement_service = 'Support Technique',
    niveau_etude = 'Licence Professionnelle',
    competences = 'Maintenance avicole, Gestion sanitaire, Audit de ferme',
    type_contrat_actuel = 'CDD'
WHERE matricule = 'EMP-2026-005';

-- Promotion pour Mamadou Ndiaye
INSERT INTO historique_carriere (employe_id, ancien_poste, nouveau_poste, date_changement, motif)
VALUES (
    (SELECT id FROM employe WHERE matricule = 'EMP-2026-005' LIMIT 1),
    'Stagiaire Avicole',
    'Technicien Avicole',
    '2026-01-15',
    'Validation de la période de stage avec félicitations du jury technique.'
);

-- Mutation pour un autre employé
INSERT INTO historique_carriere (employe_id, ancien_poste, nouveau_poste, date_changement, motif)
VALUES (
    (SELECT id FROM employe WHERE matricule = 'EMP-2026-009' LIMIT 1),
    'Chauffeur Junior',
    'Livreur',
    '2026-03-01',
    'Réorganisation du département Logistique pour le secteur Dakar-Plateau.'
);