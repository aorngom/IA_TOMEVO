import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Service_Employe from '../../../services/Service_Employe'

export default function Page_ListeEmployes() {
    const [employes, setEmployes] = useState([])
    const [chargement, setChargement] = useState(true)
    const [recherche, setRecherche] = useState('')
    const [afficherFormulaire, setAfficherFormulaire] = useState(false)

    const chargerEmployes = async () => {
        try {
            const rep = await Service_Employe.listerTous()
            setEmployes(rep.data)
        } catch (e) {
            console.error(e)
        } finally {
            setChargement(false)
        }
    }

    useEffect(() => { chargerEmployes() }, [])

    const filtres = employes.filter(e =>
        `${e.nom} ${e.prenom} ${e.matricule}`.toLowerCase().includes(recherche.toLowerCase())
    )

    return (
        <div>
            {/* En-tête */}
            <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h4 className="fw-bold mb-1">
                        <i className="bi bi-people me-2 text-primary"></i>Gestion des Employés
                    </h4>
                    <p className="text-muted small mb-0">{employes.length} employé(s) enregistré(s)</p>
                </div>
                <button
                    className="btn btn-primary"
                    onClick={() => setAfficherFormulaire(true)}
                >
                    <i className="bi bi-person-plus me-2"></i>Ajouter un employé
                </button>
            </div>

            {/* Barre de recherche */}
            <div className="card border-0 shadow-sm mb-4">
                <div className="card-body py-2">
                    <div className="input-group">
                        <span className="input-group-text bg-white border-end-0">
                            <i className="bi bi-search text-muted"></i>
                        </span>
                        <input
                            type="text"
                            className="form-control border-start-0"
                            placeholder="Rechercher par nom, prénom ou matricule..."
                            value={recherche}
                            onChange={e => setRecherche(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            {/* Tableau */}
            <div className="card border-0 shadow-sm">
                <div className="card-body p-0">
                    {chargement ? (
                        <div className="text-center py-5">
                            <div className="spinner-border text-primary"></div>
                            <p className="mt-2 text-muted">Chargement...</p>
                        </div>
                    ) : (
                        <div className="table-responsive">
                            <table className="table table-hover align-middle mb-0">
                                <thead className="table-light">
                                    <tr>
                                        <th>Matricule</th>
                                        <th>Employé</th>
                                        <th>Poste</th>
                                        <th>Département</th>
                                        <th>Date d'embauche</th>
                                        <th>Salaire base</th>
                                        <th>Statut</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtres.length === 0 ? (
                                        <tr>
                                            <td colSpan="8" className="text-center py-4 text-muted">
                                                Aucun employé trouvé
                                            </td>
                                        </tr>
                                    ) : filtres.map(e => (
                                        <tr key={e.id}>
                                            <td>
                                                <span className="badge bg-light text-dark border fw-semibold">
                                                    {e.matricule}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="d-flex align-items-center gap-2">
                                                    <div className="bg-primary rounded-circle d-flex align-items-center justify-content-center text-white fw-bold"
                                                        style={{ width: 36, height: 36, fontSize: 13 }}>
                                                        {e.prenom?.[0]}{e.nom?.[0]}
                                                    </div>
                                                    <div>
                                                        <div className="fw-semibold">{e.civilite} {e.prenom} {e.nom}</div>
                                                        <div className="text-muted small">{e.email_perso || '—'}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td>{e.poste?.libelle || <span className="text-muted">—</span>}</td>
                                            <td>{e.departement?.nom || <span className="text-muted">—</span>}</td>
                                            <td>{new Date(e.date_embauche).toLocaleDateString('fr-FR')}</td>
                                            <td className="fw-semibold">
                                                {Number(e.salaire_base_contrat).toLocaleString('fr-FR')} FCFA
                                            </td>
                                            <td>
                                                <span className={`badge ${e.actif ? 'bg-success' : 'bg-secondary'}`}>
                                                    {e.actif ? 'Actif' : 'Inactif'}
                                                </span>
                                            </td>
                                            <td>
                                                <Link
                                                    to={`/admin/grh/employes/${e.id}`}
                                                    className="btn btn-sm btn-outline-primary me-1"
                                                >
                                                    <i className="bi bi-eye"></i>
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* Modal formulaire ajout */}
            {afficherFormulaire && (
                <Form_AjoutEmploye
                    onFermer={() => setAfficherFormulaire(false)}
                    onSuccess={() => {
                        setAfficherFormulaire(false)
                        chargerEmployes()
                    }}
                />
            )}
        </div>
    )
}

// ─── Formulaire d'ajout intégré ───────────────────────────────
function Form_AjoutEmploye({ onFermer, onSuccess }) {
    const [postes, setPostes] = useState([])
    const [departements, setDepartements] = useState([])
    const [erreur, setErreur] = useState('')
    const [chargement, setChargement] = useState(false)

    const [form, setForm] = useState({
        matricule: '', civilite: 'M.', nom: '', prenom: '',
        date_naissance: '', lieu_naissance: '', nationalite: 'Sénégalaise',
        num_cni: '', num_securite_sociale: '',
        situation_matrimoniale: 'Célibataire', nombre_enfants: 0,
        adresse_residentielle: '', ville: 'Dakar', quartier: '',
        telephone_perso: '', email_perso: '',
        nom_banque: '', rib_iban: '',
        poste_id: '', departement_id: '',
        date_embauche: '', salaire_base_contrat: ''
    })

    useEffect(() => {
        Service_Employe.listerPostes().then(r => setPostes(r.data))
        Service_Employe.listerDepartements().then(r => setDepartements(r.data))
    }, [])

    const handleChange = e => {
        const { name, value } = e.target
        setForm(prev => ({ ...prev, [name]: value }))
    }

    const handleSubmit = async e => {
        e.preventDefault()
        setErreur('')
        setChargement(true)
        try {
            const payload = {
                ...form,
                nombre_enfants: parseInt(form.nombre_enfants) || 0,
                salaire_base_contrat: parseFloat(form.salaire_base_contrat),
                poste_id: form.poste_id || null,
                departement_id: form.departement_id || null,
            }
            await Service_Employe.creer(payload)
            onSuccess()
        } catch (err) {
            setErreur(err.response?.data?.detail || 'Erreur lors de la création')
        } finally {
            setChargement(false)
        }
    }

    return (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1050 }}>
            <div className="modal-dialog modal-xl modal-dialog-scrollable">
                <div className="modal-content">
                    <div className="modal-header bg-primary text-white">
                        <h5 className="modal-title">
                            <i className="bi bi-person-plus me-2"></i>Ajouter un employé
                        </h5>
                        <button className="btn-close btn-close-white" onClick={onFermer}></button>
                    </div>
                    <div className="modal-body">
                        {erreur && (
                            <div className="alert alert-danger">
                                <i className="bi bi-exclamation-triangle me-2"></i>{erreur}
                            </div>
                        )}
                        <form onSubmit={handleSubmit} id="form-employe">
                            {/* Identité */}
                            <h6 className="fw-bold text-primary border-bottom pb-2 mb-3">
                                <i className="bi bi-person me-2"></i>Identité
                            </h6>
                            <div className="row g-3 mb-4">
                                <div className="col-md-2">
                                    <label className="form-label">Civilité *</label>
                                    <select name="civilite" className="form-select" value={form.civilite} onChange={handleChange} required>
                                        <option>M.</option>
                                        <option>Mme</option>
                                        <option>Mlle</option>
                                    </select>
                                </div>
                                <div className="col-md-2">
                                    <label className="form-label">Matricule *</label>
                                    <input name="matricule" className="form-control" value={form.matricule} onChange={handleChange} required placeholder="EMP-006" />
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Nom *</label>
                                    <input name="nom" className="form-control" value={form.nom} onChange={handleChange} required />
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Prénom *</label>
                                    <input name="prenom" className="form-control" value={form.prenom} onChange={handleChange} required />
                                </div>
                                <div className="col-md-3">
                                    <label className="form-label">Date de naissance *</label>
                                    <input type="date" name="date_naissance" className="form-control" value={form.date_naissance} onChange={handleChange} required />
                                </div>
                                <div className="col-md-3">
                                    <label className="form-label">Lieu de naissance</label>
                                    <input name="lieu_naissance" className="form-control" value={form.lieu_naissance} onChange={handleChange} />
                                </div>
                                <div className="col-md-3">
                                    <label className="form-label">Numéro CNI</label>
                                    <input name="num_cni" className="form-control" value={form.num_cni} onChange={handleChange} />
                                </div>
                                <div className="col-md-3">
                                    <label className="form-label">N° Sécurité sociale</label>
                                    <input name="num_securite_sociale" className="form-control" value={form.num_securite_sociale} onChange={handleChange} />
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Situation matrimoniale</label>
                                    <select name="situation_matrimoniale" className="form-select" value={form.situation_matrimoniale} onChange={handleChange}>
                                        <option>Célibataire</option>
                                        <option>Marié(e)</option>
                                        <option>Veuf(ve)</option>
                                        <option>Divorcé(e)</option>
                                    </select>
                                </div>
                                <div className="col-md-2">
                                    <label className="form-label">Nb enfants</label>
                                    <input type="number" name="nombre_enfants" className="form-control" value={form.nombre_enfants} onChange={handleChange} min="0" />
                                </div>
                            </div>

                            {/* Contact */}
                            <h6 className="fw-bold text-primary border-bottom pb-2 mb-3">
                                <i className="bi bi-geo-alt me-2"></i>Contact & Adresse
                            </h6>
                            <div className="row g-3 mb-4">
                                <div className="col-md-6">
                                    <label className="form-label">Adresse résidentielle *</label>
                                    <input name="adresse_residentielle" className="form-control" value={form.adresse_residentielle} onChange={handleChange} required />
                                </div>
                                <div className="col-md-3">
                                    <label className="form-label">Ville</label>
                                    <input name="ville" className="form-control" value={form.ville} onChange={handleChange} />
                                </div>
                                <div className="col-md-3">
                                    <label className="form-label">Quartier</label>
                                    <input name="quartier" className="form-control" value={form.quartier} onChange={handleChange} />
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Téléphone</label>
                                    <input name="telephone_perso" className="form-control" value={form.telephone_perso} onChange={handleChange} placeholder="+221 77 000 00 00" />
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Email personnel</label>
                                    <input type="email" name="email_perso" className="form-control" value={form.email_perso} onChange={handleChange} />
                                </div>
                            </div>

                            {/* Informations professionnelles */}
                            <h6 className="fw-bold text-primary border-bottom pb-2 mb-3">
                                <i className="bi bi-briefcase me-2"></i>Informations professionnelles
                            </h6>
                            <div className="row g-3 mb-4">
                                <div className="col-md-4">
                                    <label className="form-label">Poste</label>
                                    <select name="poste_id" className="form-select" value={form.poste_id} onChange={handleChange}>
                                        <option value="">-- Sélectionner --</option>
                                        {postes.map(p => (
                                            <option key={p.id} value={p.id}>{p.libelle}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Département</label>
                                    <select name="departement_id" className="form-select" value={form.departement_id} onChange={handleChange}>
                                        <option value="">-- Sélectionner --</option>
                                        {departements.map(d => (
                                            <option key={d.id} value={d.id}>{d.nom}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Date d'embauche *</label>
                                    <input type="date" name="date_embauche" className="form-control" value={form.date_embauche} onChange={handleChange} required />
                                </div>
                                <div className="col-md-4">
                                    <label className="form-label">Salaire de base (FCFA) *</label>
                                    <input type="number" name="salaire_base_contrat" className="form-control" value={form.salaire_base_contrat} onChange={handleChange} required min="0" />
                                </div>
                            </div>

                            {/* Banque */}
                            <h6 className="fw-bold text-primary border-bottom pb-2 mb-3">
                                <i className="bi bi-bank me-2"></i>Informations bancaires
                            </h6>
                            <div className="row g-3">
                                <div className="col-md-4">
                                    <label className="form-label">Banque</label>
                                    <input name="nom_banque" className="form-control" value={form.nom_banque} onChange={handleChange} />
                                </div>
                                <div className="col-md-8">
                                    <label className="form-label">RIB / IBAN</label>
                                    <input name="rib_iban" className="form-control" value={form.rib_iban} onChange={handleChange} />
                                </div>
                            </div>
                        </form>
                    </div>
                    <div className="modal-footer">
                        <button className="btn btn-secondary" onClick={onFermer}>
                            <i className="bi bi-x me-2"></i>Annuler
                        </button>
                        <button
                            type="submit"
                            form="form-employe"
                            className="btn btn-primary"
                            disabled={chargement}
                        >
                            {chargement
                                ? <><span className="spinner-border spinner-border-sm me-2"></span>Enregistrement...</>
                                : <><i className="bi bi-check2 me-2"></i>Enregistrer l'employé</>
                            }
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}