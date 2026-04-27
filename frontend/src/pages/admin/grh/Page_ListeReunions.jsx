import { useState, useEffect } from 'react'
import Service_Reunion from '../../../services/Service_Reunion'
import Service_Employe from '../../../services/Service_Employe'

//  UTILITAIRES 
const formatDate = (iso) => {
    if (!iso) return '—'
    const d = new Date(iso)
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' })
}
const formatHeure = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}
const estPassee = (iso) => new Date(iso) < new Date()
const initiales = (prenom, nom) => `${prenom?.[0] || ''}${nom?.[0] || ''}`.toUpperCase()

const BADGE_COULEURS = [
    'bg-primary', 'bg-success', 'bg-info', 'bg-warning',
    'bg-danger', 'bg-secondary', 'bg-dark'
]
const couleurParIndex = (i) => BADGE_COULEURS[i % BADGE_COULEURS.length]

//  COMPOSANT CARTE RÉUNION 
function CarteReunion({ reunion, onSupprimer, onOuvrir }) {
    const passee = estPassee(reunion.date_heure)
    const nbConfirmes = reunion.participants.filter(p => p.presence_confirmee).length

    return (
        <div
            className={`card border-0 shadow-sm mb-3 cursor-pointer ${passee ? 'opacity-75' : ''}`}
            style={{ borderLeft: `4px solid ${passee ? '#6c757d' : '#0d6efd'}`, cursor: 'pointer' }}
            onClick={() => onOuvrir(reunion)}
        >
            <div className="card-body py-3">
                <div className="d-flex justify-content-between align-items-start">
                    <div className="flex-grow-1">
                        {/* Sujet */}
                        <div className="d-flex align-items-center gap-2 mb-1">
                            {passee
                                ? <span className="badge bg-secondary">Passée</span>
                                : <span className="badge bg-primary">À venir</span>
                            }
                            <h6 className="mb-0 fw-bold">{reunion.sujet}</h6>
                        </div>

                        {/* Date & lieu */}
                        <div className="d-flex gap-3 text-muted small mb-2">
                            <span>
                                <i className="bi bi-calendar3 me-1"></i>
                                {formatDate(reunion.date_heure)} à {formatHeure(reunion.date_heure)}
                            </span>
                            {reunion.lieu && (
                                <span>
                                    <i className="bi bi-geo-alt me-1"></i>
                                    {reunion.lieu}
                                </span>
                            )}
                        </div>

                        {/* Participants avatars */}
                        <div className="d-flex align-items-center gap-1">
                            <div className="d-flex">
                                {reunion.participants.slice(0, 5).map((p, i) => (
                                    <div
                                        key={i}
                                        className={`rounded-circle d-flex align-items-center justify-content-center text-white fw-bold ${couleurParIndex(i)}`}
                                        style={{ width: 28, height: 28, fontSize: 11, marginLeft: i > 0 ? -8 : 0, border: '2px solid white', zIndex: 5 - i }}
                                        title={`${p.prenom} ${p.nom}`}
                                    >
                                        {initiales(p.prenom, p.nom)}
                                    </div>
                                ))}
                                {reunion.participants.length > 5 && (
                                    <div
                                        className="rounded-circle d-flex align-items-center justify-content-center bg-light text-muted fw-bold"
                                        style={{ width: 28, height: 28, fontSize: 10, marginLeft: -8, border: '2px solid white' }}
                                    >
                                        +{reunion.participants.length - 5}
                                    </div>
                                )}
                            </div>
                            <span className="text-muted small ms-2">
                                {reunion.participants.length} participant(s) · {nbConfirmes} confirmé(s)
                            </span>
                        </div>
                    </div>

                    {/* Bouton supprimer */}
                    <button
                        className="btn btn-sm btn-outline-danger ms-2"
                        title="Supprimer"
                        onClick={e => { e.stopPropagation(); onSupprimer(reunion.id) }}
                    >
                        <i className="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    )
}

//  MODAL DÉTAIL RÉUNION 
function ModalDetailReunion({ reunion, onFermer, onRefresh }) {
    if (!reunion) return null

    const passee = estPassee(reunion.date_heure)

    const confirmerPresence = async (reunionId, employeId) => {
        try {
            await Service_Reunion.confirmerPresence(reunionId, employeId)
            onRefresh()
        } catch (e) {
            console.error(e)
        }
    }

    return (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1055 }}>
            <div className="modal-dialog modal-lg modal-dialog-scrollable">
                <div className="modal-content border-0 shadow">
                    {/* Header */}
                    <div className={`modal-header ${passee ? 'bg-secondary' : 'bg-primary'} text-white`}>
                        <div>
                            <h5 className="modal-title mb-0">
                                <i className="bi bi-camera-video me-2"></i>{reunion.sujet}
                            </h5>
                            <small className="opacity-75">
                                {formatDate(reunion.date_heure)} à {formatHeure(reunion.date_heure)}
                                {reunion.lieu && ` · ${reunion.lieu}`}
                            </small>
                        </div>
                        <button className="btn-close btn-close-white" onClick={onFermer}></button>
                    </div>

                    <div className="modal-body">
                        {/* Ordre du jour */}
                        {reunion.ordre_du_jour && (
                            <div className="mb-4">
                                <h6 className="fw-bold text-primary border-bottom pb-2">
                                    <i className="bi bi-list-ul me-2"></i>Ordre du jour
                                </h6>
                                <p className="text-muted" style={{ whiteSpace: 'pre-line' }}>
                                    {reunion.ordre_du_jour}
                                </p>
                            </div>
                        )}

                        {/* Participants */}
                        <h6 className="fw-bold text-primary border-bottom pb-2 mb-3">
                            <i className="bi bi-people me-2"></i>
                            Participants ({reunion.participants.length})
                        </h6>
                        <div className="row g-2">
                            {reunion.participants.map((p, i) => (
                                <div key={i} className="col-md-6">
                                    <div className={`d-flex align-items-center gap-2 p-2 rounded border ${p.presence_confirmee ? 'border-success bg-success bg-opacity-10' : 'border-light'}`}>
                                        <div
                                            className={`rounded-circle d-flex align-items-center justify-content-center text-white fw-bold flex-shrink-0 ${couleurParIndex(i)}`}
                                            style={{ width: 36, height: 36, fontSize: 13 }}
                                        >
                                            {initiales(p.prenom, p.nom)}
                                        </div>
                                        <div className="flex-grow-1">
                                            <div className="fw-semibold small">{p.prenom} {p.nom}</div>
                                            <div className="text-muted" style={{ fontSize: 11 }}>{p.poste || '—'}</div>
                                        </div>
                                        {p.presence_confirmee
                                            ? <span className="badge bg-success"><i className="bi bi-check2"></i> Confirmé</span>
                                            : (
                                                <button
                                                    className="btn btn-sm btn-outline-success py-0"
                                                    style={{ fontSize: 11 }}
                                                    onClick={() => confirmerPresence(reunion.id, p.employe_id)}
                                                >
                                                    Confirmer
                                                </button>
                                            )
                                        }
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="modal-footer">
                        <button className="btn btn-secondary" onClick={onFermer}>Fermer</button>
                    </div>
                </div>
            </div>
        </div>
    )
}

//  MODAL CRÉATION MANUELLE 
function ModalCreerReunion({ onFermer, onSuccess }) {
    const [employes, setEmployes] = useState([])
    const [form, setForm] = useState({
        sujet: '', date_heure: '', lieu: '', ordre_du_jour: '', employe_ids: []
    })
    const [chargement, setChargement] = useState(false)
    const [erreur, setErreur] = useState('')

    useEffect(() => {
        Service_Employe.listerTous().then(r => setEmployes(r.data)).catch(() => {})
    }, [])

    const toggleEmploye = (id) => {
        setForm(prev => ({
            ...prev,
            employe_ids: prev.employe_ids.includes(id)
                ? prev.employe_ids.filter(i => i !== id)
                : [...prev.employe_ids, id]
        }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!form.sujet || !form.date_heure) return
        setChargement(true)
        setErreur('')
        try {
            await Service_Reunion.creer({
                ...form,
                date_heure: new Date(form.date_heure).toISOString()
            })
            onSuccess()
        } catch (err) {
            setErreur(err.response?.data?.detail || 'Erreur lors de la création')
        } finally {
            setChargement(false)
        }
    }

    return (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1055 }}>
            <div className="modal-dialog modal-lg modal-dialog-scrollable">
                <div className="modal-content border-0 shadow">
                    <div className="modal-header bg-primary text-white">
                        <h5 className="modal-title">
                            <i className="bi bi-camera-video-fill me-2"></i>Planifier une réunion
                        </h5>
                        <button className="btn-close btn-close-white" onClick={onFermer}></button>
                    </div>
                    <div className="modal-body">
                        {erreur && <div className="alert alert-danger">{erreur}</div>}
                        <form onSubmit={handleSubmit} id="form-reunion">
                            <div className="row g-3">
                                <div className="col-12">
                                    <label className="form-label fw-semibold">Sujet *</label>
                                    <input
                                        className="form-control"
                                        value={form.sujet}
                                        onChange={e => setForm(p => ({ ...p, sujet: e.target.value }))}
                                        required
                                        placeholder="Ex: Revue trimestrielle des objectifs"
                                    />
                                </div>
                                <div className="col-md-6">
                                    <label className="form-label fw-semibold">Date et heure *</label>
                                    <input
                                        type="datetime-local"
                                        className="form-control"
                                        value={form.date_heure}
                                        onChange={e => setForm(p => ({ ...p, date_heure: e.target.value }))}
                                        required
                                    />
                                </div>
                                <div className="col-md-6">
                                    <label className="form-label fw-semibold">Lieu / Lien</label>
                                    <input
                                        className="form-control"
                                        value={form.lieu}
                                        onChange={e => setForm(p => ({ ...p, lieu: e.target.value }))}
                                        placeholder="Salle de conférence ou lien Teams..."
                                    />
                                </div>
                                <div className="col-12">
                                    <label className="form-label fw-semibold">Ordre du jour</label>
                                    <textarea
                                        className="form-control"
                                        rows={3}
                                        value={form.ordre_du_jour}
                                        onChange={e => setForm(p => ({ ...p, ordre_du_jour: e.target.value }))}
                                        placeholder="Points à aborder..."
                                    />
                                </div>

                                {/* Sélection des participants */}
                                <div className="col-12">
                                    <label className="form-label fw-semibold">
                                        Participants ({form.employe_ids.length} sélectionné(s))
                                    </label>
                                    <div className="border rounded p-2" style={{ maxHeight: 200, overflowY: 'auto' }}>
                                        {employes.map(e => (
                                            <div
                                                key={e.id}
                                                className={`d-flex align-items-center gap-2 p-2 rounded mb-1 cursor-pointer ${form.employe_ids.includes(e.id) ? 'bg-primary bg-opacity-10 border border-primary' : 'hover-bg'}`}
                                                style={{ cursor: 'pointer' }}
                                                onClick={() => toggleEmploye(e.id)}
                                            >
                                                <div
                                                    className={`rounded-circle d-flex align-items-center justify-content-center text-white fw-bold flex-shrink-0 ${form.employe_ids.includes(e.id) ? 'bg-primary' : 'bg-secondary'}`}
                                                    style={{ width: 30, height: 30, fontSize: 11 }}
                                                >
                                                    {initiales(e.prenom, e.nom)}
                                                </div>
                                                <div>
                                                    <div className="fw-semibold small">{e.civilite} {e.prenom} {e.nom}</div>
                                                    <div className="text-muted" style={{ fontSize: 11 }}>{e.matricule}</div>
                                                </div>
                                                {form.employe_ids.includes(e.id) && (
                                                    <i className="bi bi-check-circle-fill text-primary ms-auto"></i>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div className="modal-footer">
                        <button className="btn btn-secondary" onClick={onFermer}>Annuler</button>
                        <button
                            type="submit"
                            form="form-reunion"
                            className="btn btn-primary"
                            disabled={chargement || !form.sujet || !form.date_heure}
                        >
                            {chargement
                                ? <><span className="spinner-border spinner-border-sm me-2"></span>Création...</>
                                : <><i className="bi bi-check2 me-2"></i>Créer la réunion</>
                            }
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

//  PAGE PRINCIPALE 
export default function Page_ListeReunions() {
    const [reunions, setReunions] = useState([])
    const [chargement, setChargement] = useState(true)
    const [recherche, setRecherche] = useState('')
    const [filtre, setFiltre] = useState('toutes') // 'toutes' | 'avenir' | 'passees'
    const [reunionSelectionnee, setReunionSelectionnee] = useState(null)
    const [afficherCreation, setAfficherCreation] = useState(false)

    const charger = async () => {
        setChargement(true)
        try {
            const r = await Service_Reunion.listerToutes()
            setReunions(r.data)
        } catch (e) {
            console.error(e)
        } finally {
            setChargement(false)
        }
    }

    useEffect(() => { charger() }, [])

    const supprimer = async (id) => {
        if (!window.confirm('Supprimer cette réunion ?')) return
        try {
            await Service_Reunion.supprimer(id)
            charger()
        } catch (e) {
            console.error(e)
        }
    }

    const filtrees = reunions
        .filter(r => {
            if (filtre === 'avenir') return !estPassee(r.date_heure)
            if (filtre === 'passees') return estPassee(r.date_heure)
            return true
        })
        .filter(r => r.sujet.toLowerCase().includes(recherche.toLowerCase()))

    const nbAvenir = reunions.filter(r => !estPassee(r.date_heure)).length

    return (
        <div>
            {/* En-tête */}
            <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h4 className="fw-bold mb-1">
                        <i className="bi bi-camera-video me-2 text-primary"></i>Gestion des Réunions
                    </h4>
                    <p className="text-muted small mb-0">
                        {reunions.length} réunion(s) · <span className="text-primary fw-semibold">{nbAvenir} à venir</span>
                    </p>
                </div>
                <button className="btn btn-primary" onClick={() => setAfficherCreation(true)}>
                    <i className="bi bi-plus-lg me-2"></i>Planifier une réunion
                </button>
            </div>

            {/* Stats rapides */}
            <div className="row g-3 mb-4">
                {[
                    { label: 'Total', valeur: reunions.length, icon: 'bi-camera-video', couleur: 'primary' },
                    { label: 'À venir', valeur: nbAvenir, icon: 'bi-clock', couleur: 'success' },
                    { label: 'Passées', valeur: reunions.length - nbAvenir, icon: 'bi-check-circle', couleur: 'secondary' },
                    {
                        label: 'Participants total',
                        valeur: reunions.reduce((acc, r) => acc + r.participants.length, 0),
                        icon: 'bi-people',
                        couleur: 'info'
                    }
                ].map((s, i) => (
                    <div key={i} className="col-md-3">
                        <div className="card border-0 shadow-sm text-center py-3">
                            <i className={`bi ${s.icon} text-${s.couleur} fs-4 mb-1`}></i>
                            <div className="fw-bold fs-5">{s.valeur}</div>
                            <div className="text-muted small">{s.label}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Filtres + Recherche */}
            <div className="card border-0 shadow-sm mb-4">
                <div className="card-body py-2 d-flex gap-3 align-items-center flex-wrap">
                    <div className="input-group" style={{ maxWidth: 300 }}>
                        <span className="input-group-text bg-white border-end-0">
                            <i className="bi bi-search text-muted"></i>
                        </span>
                        <input
                            type="text"
                            className="form-control border-start-0"
                            placeholder="Rechercher..."
                            value={recherche}
                            onChange={e => setRecherche(e.target.value)}
                        />
                    </div>
                    <div className="btn-group">
                        {[
                            { val: 'toutes', label: 'Toutes' },
                            { val: 'avenir', label: 'À venir' },
                            { val: 'passees', label: 'Passées' }
                        ].map(f => (
                            <button
                                key={f.val}
                                className={`btn btn-sm ${filtre === f.val ? 'btn-primary' : 'btn-outline-primary'}`}
                                onClick={() => setFiltre(f.val)}
                            >
                                {f.label}
                            </button>
                        ))}
                    </div>
                    <span className="text-muted small ms-auto">{filtrees.length} résultat(s)</span>
                </div>
            </div>

            {/* Liste */}
            {chargement ? (
                <div className="text-center py-5">
                    <div className="spinner-border text-primary"></div>
                    <p className="mt-2 text-muted">Chargement...</p>
                </div>
            ) : filtrees.length === 0 ? (
                <div className="text-center py-5 text-muted">
                    <i className="bi bi-camera-video-off fs-1 d-block mb-2 opacity-25"></i>
                    Aucune réunion trouvée
                </div>
            ) : (
                filtrees.map(r => (
                    <CarteReunion
                        key={r.id}
                        reunion={r}
                        onSupprimer={supprimer}
                        onOuvrir={setReunionSelectionnee}
                    />
                ))
            )}

            {/* Modals */}
            {reunionSelectionnee && (
                <ModalDetailReunion
                    reunion={reunionSelectionnee}
                    onFermer={() => setReunionSelectionnee(null)}
                    onRefresh={() => {
                        charger()
                        setReunionSelectionnee(null)
                    }}
                />
            )}
            {afficherCreation && (
                <ModalCreerReunion
                    onFermer={() => setAfficherCreation(false)}
                    onSuccess={() => { setAfficherCreation(false); charger() }}
                />
            )}
        </div>
    )
}