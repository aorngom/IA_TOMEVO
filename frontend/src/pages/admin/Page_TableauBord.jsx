import { useAuth } from '../../context/Context_Auth'
import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Service_Reunion from '../../services/Service_Reunion'

const raccourcis = [
    { label: 'Employés',    icon: 'bi-people-fill',          path: '/admin/grh/employes',      couleur: 'primary'   },
    { label: 'Fiches de paie', icon: 'bi-receipt',           path: '/admin/paie/fiches',       couleur: 'success'   },
    { label: 'Absences',    icon: 'bi-calendar-x',           path: '/admin/grh/absences',      couleur: 'warning'   },
    { label: 'Commandes',   icon: 'bi-bag-check',            path: '/admin/commandes',         couleur: 'info'      },
    { label: 'OCR / IA',    icon: 'bi-file-earmark-medical', path: '/admin/ocr/traitement',    couleur: 'danger'    },
    { label: 'Config paie', icon: 'bi-sliders',              path: '/admin/paie/config',       couleur: 'secondary' },
]

// Utilitaires 
const estPassee = (iso) => new Date(iso) < new Date()

const formatDateCourte = (iso) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('fr-FR', {
        day: '2-digit', month: 'short', year: 'numeric'
    })
}
const formatHeure = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}
const initiales = (prenom, nom) => `${prenom?.[0] || ''}${nom?.[0] || ''}`.toUpperCase()

const BADGE_COULEURS = ['bg-primary', 'bg-success', 'bg-info', 'bg-warning', 'bg-danger', 'bg-secondary']
const couleurParIndex = (i) => BADGE_COULEURS[i % BADGE_COULEURS.length]

//  Widget réunions à venir 
function WidgetReunions() {
    const [reunions, setReunions] = useState([])
    const [chargement, setChargement] = useState(true)

    useEffect(() => {
        Service_Reunion.listerToutes()
            .then(r => {
                // Garder uniquement les réunions à venir, triées par date
                const avenir = (r.data || [])
                    .filter(r => !estPassee(r.date_heure))
                    .sort((a, b) => new Date(a.date_heure) - new Date(b.date_heure))
                    .slice(0, 4)
                setReunions(avenir)
            })
            .catch(() => setReunions([]))
            .finally(() => setChargement(false))
    }, [])

    return (
        <div className="card border-0 shadow-sm mb-4">
            <div className="card-header bg-white border-bottom d-flex justify-content-between align-items-center py-3">
                <div className="fw-bold">
                    <i className="bi bi-camera-video me-2 text-primary"></i>
                    Réunions à venir
                </div>
                <Link to="/admin/grh/reunions" className="btn btn-sm btn-outline-primary">
                    Voir tout
                </Link>
            </div>

            <div className="card-body p-0">
                {chargement ? (
                    <div className="text-center py-4">
                        <div className="spinner-border spinner-border-sm text-primary"></div>
                    </div>
                ) : reunions.length === 0 ? (
                    <div className="text-center py-4 text-muted">
                        <i className="bi bi-camera-video-off fs-3 d-block mb-2 opacity-25"></i>
                        <p className="small mb-2">Aucune réunion planifiée</p>
                        <Link to="/admin/ocr/traitement" className="btn btn-sm btn-outline-primary">
                            <i className="bi bi-robot me-1"></i>Demander à l'IA
                        </Link>
                    </div>
                ) : (
                    <ul className="list-group list-group-flush">
                        {reunions.map((r, i) => (
                            <li key={r.id} className="list-group-item px-3 py-2">
                                <div className="d-flex align-items-center gap-3">
                                    {/* Icône colorée */}
                                    <div
                                        className="rounded d-flex align-items-center justify-content-center bg-primary bg-opacity-10 flex-shrink-0"
                                        style={{ width: 40, height: 40 }}
                                    >
                                        <i className="bi bi-camera-video text-primary"></i>
                                    </div>

                                    {/* Infos */}
                                    <div className="flex-grow-1 min-w-0">
                                        <div className="fw-semibold text-truncate small">{r.sujet}</div>
                                        <div className="text-muted d-flex gap-2" style={{ fontSize: 11 }}>
                                            <span>
                                                <i className="bi bi-calendar3 me-1"></i>
                                                {formatDateCourte(r.date_heure)} à {formatHeure(r.date_heure)}
                                            </span>
                                            {r.lieu && (
                                                <span className="text-truncate">
                                                    <i className="bi bi-geo-alt me-1"></i>{r.lieu}
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Avatars participants */}
                                    <div className="d-flex flex-shrink-0">
                                        {r.participants.slice(0, 3).map((p, j) => (
                                            <div
                                                key={j}
                                                className={`rounded-circle d-flex align-items-center justify-content-center text-white fw-bold ${couleurParIndex(j)}`}
                                                style={{
                                                    width: 24, height: 24, fontSize: 9,
                                                    marginLeft: j > 0 ? -6 : 0,
                                                    border: '2px solid white'
                                                }}
                                                title={`${p.prenom} ${p.nom}`}
                                            >
                                                {initiales(p.prenom, p.nom)}
                                            </div>
                                        ))}
                                        {r.participants.length > 3 && (
                                            <div
                                                className="rounded-circle d-flex align-items-center justify-content-center bg-light text-muted fw-bold"
                                                style={{ width: 24, height: 24, fontSize: 9, marginLeft: -6, border: '2px solid white' }}
                                            >
                                                +{r.participants.length - 3}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* Footer : lien vers l'IA pour organiser */}
            <div className="card-footer bg-white border-top py-2 text-center">
                <Link to="/admin/ocr/traitement" className="text-decoration-none text-muted small">
                    <i className="bi bi-robot me-1"></i>
                    Organiser une réunion avec l'assistant IA
                </Link>
            </div>
        </div>
    )
}

// Page principale 
export default function Page_TableauBord() {
    const { utilisateur } = useAuth()

    return (
        <div>
            {/* Titre */}
            <div className="mb-4">
                <h4 className="fw-bold mb-1">
                    Bonjour, {utilisateur?.prenom} {utilisateur?.nom} 👋
                </h4>
                <p className="text-muted">Voici un aperçu de votre espace d'administration.</p>
            </div>

            {/* Raccourcis */}
            <div className="row g-3 mb-4">
                {raccourcis.map((item, i) => (
                    <div key={i} className="col-6 col-md-4 col-lg-2">
                        <Link to={item.path} className="text-decoration-none">
                            <div className={`card border-0 shadow-sm text-center p-3 h-100 border-top border-4 border-${item.couleur}`}>
                                <i className={`bi ${item.icon} text-${item.couleur} fs-2 mb-2`}></i>
                                <div className="small fw-semibold text-dark">{item.label}</div>
                            </div>
                        </Link>
                    </div>
                ))}
            </div>

            {/* Widget réunions */}
            <WidgetReunions />

            {/* Info */}
            <div className="alert alert-success d-flex align-items-center gap-2">
                <i className="bi bi-info-circle-fill fs-5"></i>
                <div>
                    Système opérationnel. Les modules <strong>GRH</strong> et <strong>Paie</strong> sont prêts à être utilisés.
                </div>
            </div>
        </div>
    )
}