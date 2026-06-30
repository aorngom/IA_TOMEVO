import { useState, useEffect, useRef } from 'react'
import { v4 as uuidv4 } from 'uuid'
import Service_FichePaie from '../../../services/Service_FichePaie'
import Service_Employe from '../../../services/Service_Employe'
import Service_PaieIA from '../../../services/Service_PaieIA'

const MOIS = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
]

//  Composant Agent IA Paie ─
function AgentPaiePanel({ onFermer, onRafraichir }) {
    const [sessionId] = useState(() => uuidv4())
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Bonjour. Je suis l'assistant paie de Jariniou. Je peux calculer des salaires, générer des fiches, détecter des anomalies, envoyer des bulletins et répondre à vos questions sur la paie.\n\nVous pouvez aussi me transmettre un bulletin PDF ou image pour que je l'analyse."
        }
    ])
    const [input, setInput] = useState('')
    const [chargement, setChargement] = useState(false)
    const [fichier, setFichier] = useState(null)
    const [fichierNom, setFichierNom] = useState('')
    const chatEndRef = useRef(null)
    const inputFichierRef = useRef(null)

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleFichier = (e) => {
        const f = e.target.files[0]
        if (!f) return
        setFichier(f)
        setFichierNom(f.name)
    }

    const supprimerFichier = () => {
        setFichier(null)
        setFichierNom('')
        if (inputFichierRef.current) inputFichierRef.current.value = ''
    }

    const envoyer = async () => {
        if ((!input.trim() && !fichier) || chargement) return

        const contenuMessage = input.trim() || `Analyse ce document : ${fichierNom}`
        const userMsg = { role: 'user', content: contenuMessage }
        const nouveauxMessages = [...messages, userMsg]
        setMessages(nouveauxMessages)
        setInput('')
        setChargement(true)

        try {
            let base64 = null
            let nom = null

            if (fichier) {
                base64 = await Service_PaieIA.fichierVersBase64(fichier)
                nom = fichierNom
                supprimerFichier()
            }

            const res = await Service_PaieIA.chat(nouveauxMessages, sessionId, base64, nom)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: res.data.reponse
            }])
            if (res.data.rafraichir) onRafraichir()
        } catch {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "Erreur de connexion avec l'assistant."
            }])
        } finally {
            setChargement(false)
        }
    }

    const suggestions = [
        "Qui a le salaire le plus élevé ?",
        "Y a-t-il des irrégularités dans la paie ?",
        "Analyse les fiches de juin 2026",
        "Déclenche la paie maintenant pour juin 2026",
        "Quelle est la masse salariale par département ?"
    ]

    return (
        <div style={{
            position: 'fixed', bottom: 24, right: 24, width: 680, height: 840,
            zIndex: 1050, display: 'flex', flexDirection: 'column',
            borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
            background: '#fff', border: '1px solid #e0e0e0', overflow: 'hidden'
        }}>
            {/* Header */}
            <div style={{
                background: 'var(--couleur-principale, #0d6efd)', color: '#fff',
                padding: '12px 16px', display: 'flex', alignItems: 'center',
                justifyContent: 'space-between', flexShrink: 0
            }}>
                <div className="d-flex align-items-center gap-2">
                    <i className="bi bi-robot fs-5"></i>
                    <div>
                        <div className="fw-semibold" style={{ fontSize: 14 }}>Assistant Paie IA</div>
                        <div style={{ fontSize: 11, opacity: 0.8 }}>Jariniou · GPT-4o mini</div>
                    </div>
                </div>
                <button onClick={onFermer} style={{
                    background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: 6,
                    color: '#fff', width: 28, height: 28, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                    <i className="bi bi-x" style={{ fontSize: 16 }}></i>
                </button>
            </div>

            {/* Messages */}
            <div style={{
                flex: 1, overflowY: 'auto', padding: '12px 14px',
                background: '#f8f9fa', display: 'flex', flexDirection: 'column', gap: 10
            }}>
                {messages.map((m, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                        <div style={{
                            maxWidth: '85%', padding: '10px 14px',
                            borderRadius: m.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                            background: m.role === 'user' ? 'var(--couleur-principale, #0d6efd)' : '#fff',
                            color: m.role === 'user' ? '#fff' : '#212529',
                            fontSize: 14, lineHeight: 1.6,
                            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                            whiteSpace: 'pre-wrap', wordBreak: 'break-word'
                        }}>
                            {m.content}
                        </div>
                    </div>
                ))}

                {chargement && (
                    <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                        <div style={{
                            padding: '8px 14px', borderRadius: '12px 12px 12px 2px',
                            background: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                            display: 'flex', gap: 4, alignItems: 'center'
                        }}>
                            {[0, 0.2, 0.4].map((d, i) => (
                                <div key={i} style={{
                                    width: 6, height: 6, borderRadius: '50%',
                                    background: '#adb5bd', animation: `pulse 1s infinite ${d}s`
                                }} />
                            ))}
                        </div>
                    </div>
                )}

                {messages.length === 1 && (
                    <div style={{ marginTop: 4 }}>
                        <div style={{ fontSize: 11, color: '#6c757d', marginBottom: 6 }}>Suggestions :</div>
                        {suggestions.map((s, i) => (
                            <button key={i} onClick={() => setInput(s)} style={{
                                display: 'block', width: '100%', textAlign: 'left',
                                background: '#fff', border: '1px solid #dee2e6', borderRadius: 8,
                                padding: '6px 10px', fontSize: 13, color: '#495057',
                                cursor: 'pointer', marginBottom: 4
                            }}>
                                <i className="bi bi-arrow-right me-1 text-primary" style={{ fontSize: 10 }}></i>
                                {s}
                            </button>
                        ))}
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            {/* Fichier sélectionné */}
            {fichierNom && (
                <div style={{
                    padding: '6px 12px', background: '#e8f4fd',
                    borderTop: '1px solid #bee3f8', display: 'flex',
                    alignItems: 'center', justifyContent: 'space-between',
                    fontSize: 13, flexShrink: 0
                }}>
                    <div className="d-flex align-items-center gap-2">
                        <i className="bi bi-file-earmark-text text-primary"></i>
                        <span style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {fichierNom}
                        </span>
                    </div>
                    <button onClick={supprimerFichier} style={{
                        background: 'none', border: 'none', cursor: 'pointer',
                        color: '#6c757d', padding: '0 4px'
                    }}>
                        <i className="bi bi-x-circle"></i>
                    </button>
                </div>
            )}

            {/* Saisie */}
            <div style={{
                padding: '10px 12px', borderTop: '1px solid #e9ecef',
                background: '#fff', flexShrink: 0
            }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <input ref={inputFichierRef} type="file" accept=".pdf,image/*"
                        style={{ display: 'none' }} onChange={handleFichier} />
                    <button onClick={() => inputFichierRef.current?.click()} disabled={chargement}
                        title="Joindre un bulletin (PDF ou image)"
                        style={{
                            background: fichierNom ? '#e8f4fd' : '#f8f9fa',
                            border: `1px solid ${fichierNom ? '#bee3f8' : '#dee2e6'}`,
                            borderRadius: 8, color: fichierNom ? '#0d6efd' : '#6c757d',
                            width: 36, height: 36, cursor: 'pointer',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                        }}>
                        <i className="bi bi-paperclip" style={{ fontSize: 15 }}></i>
                    </button>
                    <input type="text" value={input} onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && envoyer()}
                        placeholder={fichierNom ? "Posez une question sur ce document..." : "Posez une question sur la paie..."}
                        disabled={chargement}
                        style={{
                            flex: 1, border: '1px solid #dee2e6', borderRadius: 8,
                            padding: '9px 12px', fontSize: 14, outline: 'none'
                        }} />
                    <button onClick={envoyer} disabled={chargement || (!input.trim() && !fichier)}
                        style={{
                            background: 'var(--couleur-principale, #0d6efd)', border: 'none',
                            borderRadius: 8, color: '#fff', width: 36, height: 36, cursor: 'pointer',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            opacity: (chargement || (!input.trim() && !fichier)) ? 0.5 : 1, flexShrink: 0
                        }}>
                        <i className="bi bi-send-fill" style={{ fontSize: 13 }}></i>
                    </button>
                </div>
            </div>
        </div>
    )
}

//  Bouton flottant 
function BoutonAgentPaie({ onClick, actif }) {
    return (
        <button
            onClick={onClick}
            title="Assistant Paie IA"
            style={{
                position: 'fixed',
                bottom: 24,
                right: 24,
                width: 60,
                height: 60,
                borderRadius: '50%',
                background: actif ? '#6c757d' : 'var(--couleur-principale, #0d6efd)',
                border: 'none',
                color: '#fff',
                fontSize: 24,
                cursor: 'pointer',
                boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1049,
                transition: 'all 0.2s'
            }}
        >
            <i className={`bi ${actif ? 'bi-x-lg' : 'bi-robot'}`}></i>
        </button>
    )
}

//  Page principale 
export default function Page_ListeFichesPaie() {
    const [fiches, setFiches] = useState([])
    const [chargement, setChargement] = useState(true)
    const [recherche, setRecherche] = useState('')
    const [filtreMois, setFiltreMois] = useState('')
    const [filtreAnnee, setFiltreAnnee] = useState('')
    const [afficherFormulaire, setAfficherFormulaire] = useState(false)
    const [agentOuvert, setAgentOuvert] = useState(false)   
    const [notifications, setNotifications] = useState([])
    const [mailEnAttente, setMailEnAttente] = useState(null)

    const chargerFiches = async () => {
        try {
            const rep = await Service_FichePaie.listerToutes()
            setFiches(rep.data)
        } catch (e) {
            console.error(e)
        } finally {
            setChargement(false)
        }
    }

    useEffect(() => { chargerFiches() }, [])
        // Polling notifications toutes les 30 secondes
    useEffect(() => {
        const verifierNotifications = async () => {
            try {
                const res = await Service_PaieIA.getNotifications()
                const notifs = res.data.notifications || []
                if (notifs.length > 0) {
                    setNotifications(notifs)
                    // Si une notif a une action mail → proposer confirmation
                    const avecAction = notifs.find(n => n.type === 'rappel' && n.action)
                    if (avecAction) setMailEnAttente(avecAction)
                }
            } catch (e) {
                console.error('Erreur notifications:', e)
            }
        }
        verifierNotifications()
        const interval = setInterval(verifierNotifications, 30000)
        return () => clearInterval(interval)
    }, [])

    const filtres = fiches.filter(f => {
        const nom = `${f.employe?.prenom} ${f.employe?.nom} ${f.employe?.matricule}`.toLowerCase()
        const okRecherche = nom.includes(recherche.toLowerCase())
        const okMois = filtreMois ? f.periode_mois === parseInt(filtreMois) : true
        const okAnnee = filtreAnnee ? f.periode_annee === parseInt(filtreAnnee) : true
        return okRecherche && okMois && okAnnee
    })

    const totalBrut = filtres.reduce((s, f) => s + parseFloat(f.salaire_brut || 0), 0)
    const totalNet = filtres.reduce((s, f) => s + parseFloat(f.salaire_net || 0), 0)

    const handleSupprimer = async (id) => {
        if (!confirm('Supprimer cette fiche de paie ?')) return
        await Service_FichePaie.supprimer(id)
        chargerFiches()
    }
    const confirmerEnvoiMail = async (notif) => {
        try {
            // Envoyer le mail via l'agent
            await Service_PaieIA.chat(
                [{ role: 'user', content: `Envoie ce mail : ${JSON.stringify(notif.action)}` }],
                'rappel-auto'
            )
            // Marquer comme lue
            await Service_PaieIA.marquerLue(notif.id)
            setNotifications(prev => prev.filter(n => n.id !== notif.id))
            setMailEnAttente(null)
        } catch (e) {
            console.error('Erreur confirmation mail:', e)
        }
    }
    
    const dismissNotification = async (id) => {
        await Service_PaieIA.marquerLue(id)
        setNotifications(prev => prev.filter(n => n.id !== id))
        setMailEnAttente(null)
    }

    return (
        <div className="fade-in">
                        {/* ── Bannière notifications ── */}
            {notifications.map(notif => (
                <div key={notif.id} style={{
                    background: notif.action ? '#fff8e1' : '#e8f4fd',
                    border: `1px solid ${notif.action ? '#f59e0b' : '#bee3f8'}`,
                    borderRadius: 8, padding: '12px 16px', marginBottom: 12,
                    display: 'flex', alignItems: 'center',
                    justifyContent: 'space-between', gap: 12
                }}>
                    <div className="d-flex align-items-center gap-2">
                        <i className={`bi ${notif.action ? 'bi-bell-fill text-warning' : 'bi-info-circle text-primary'}`}></i>
                        <span style={{ fontSize: 14 }}>{notif.message}</span>
                    </div>
                    <div className="d-flex gap-2">
                        {notif.action && (
                            <button
                                className="btn btn-sm btn-warning"
                                onClick={() => confirmerEnvoiMail(notif)}
                            >
                                <i className="bi bi-send me-1"></i>Confirmer l'envoi
                            </button>
                        )}
                        <button
                            className="btn btn-sm btn-outline-secondary"
                            onClick={() => dismissNotification(notif.id)}
                        >
                            <i className="bi bi-x"></i>
                        </button>
                    </div>
                </div>
            ))}
            {/* En-tête */}
            <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h4 className="fw-bold mb-1">
                        <i className="bi bi-receipt me-2 text-primary"></i>Fiches de Paie
                    </h4>
                    <p className="text-muted small mb-0">{fiches.length} fiche(s) enregistrée(s)</p>
                </div>
                <button className="btn btn-primary" onClick={() => setAfficherFormulaire(true)}>
                    <i className="bi bi-plus-circle me-2"></i>Générer une fiche
                </button>
            </div>

            {/* Cartes stats */}
            <div className="row g-3 mb-4">
                <div className="col-md-4">
                    <div className="stat-card">
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <p className="text-muted small mb-1">Total fiches</p>
                                <h4 className="fw-bold mb-0">{filtres.length}</h4>
                            </div>
                            <i className="bi bi-file-earmark-text fs-2 text-primary opacity-50"></i>
                        </div>
                    </div>
                </div>
                <div className="col-md-4">
                    <div className="stat-card">
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <p className="text-muted small mb-1">Masse salariale brute</p>
                                <h4 className="fw-bold mb-0">{totalBrut.toLocaleString('fr-FR')} <small className="fs-6">FCFA</small></h4>
                            </div>
                            <i className="bi bi-cash-stack fs-2 text-primary opacity-50"></i>
                        </div>
                    </div>
                </div>
                <div className="col-md-4">
                    <div className="stat-card">
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <p className="text-muted small mb-1">Masse salariale nette</p>
                                <h4 className="fw-bold mb-0">{totalNet.toLocaleString('fr-FR')} <small className="fs-6">FCFA</small></h4>
                            </div>
                            <i className="bi bi-wallet2 fs-2 text-primary opacity-50"></i>
                        </div>
                    </div>
                </div>
            </div>

            {/* Filtres */}
            <div className="card mb-4">
                <div className="card-body py-3">
                    <div className="row g-2">
                        <div className="col-md-6">
                            <div className="input-group">
                                <span className="input-group-text bg-white border-end-0">
                                    <i className="bi bi-search text-muted"></i>
                                </span>
                                <input
                                    type="text"
                                    className="form-control border-start-0"
                                    placeholder="Rechercher un employé..."
                                    value={recherche}
                                    onChange={e => setRecherche(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="col-md-3">
                            <select className="form-select" value={filtreMois} onChange={e => setFiltreMois(e.target.value)}>
                                <option value="">Tous les mois</option>
                                {MOIS.map((m, i) => (
                                    <option key={i} value={i + 1}>{m}</option>
                                ))}
                            </select>
                        </div>
                        <div className="col-md-3">
                            <select className="form-select" value={filtreAnnee} onChange={e => setFiltreAnnee(e.target.value)}>
                                <option value="">Toutes les années</option>
                                <option value="2024">2024</option>
                                <option value="2025">2025</option>
                                <option value="2026">2026</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tableau */}
            <div className="card">
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
                                        <th>Employé</th>
                                        <th>Matricule</th>
                                        <th>Période</th>
                                        <th>Salaire brut</th>
                                        <th>Salaire net</th>
                                        <th>Cotisations</th>
                                        <th>Généré le</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtres.length === 0 ? (
                                        <tr>
                                            <td colSpan="8" className="text-center py-4 text-muted">
                                                Aucune fiche trouvée
                                            </td>
                                        </tr>
                                    ) : filtres.map(f => {
                                        const cotisations = parseFloat(f.salaire_brut) - parseFloat(f.salaire_net)
                                        return (
                                            <tr key={f.id}>
                                                <td>
                                                    <div className="d-flex align-items-center gap-2">
                                                        <div className="avatar" style={{ width: 34, height: 34, fontSize: 12 }}>
                                                            {f.employe?.prenom?.[0]}{f.employe?.nom?.[0]}
                                                        </div>
                                                        <div className="fw-semibold">
                                                            {f.employe?.prenom} {f.employe?.nom}
                                                        </div>
                                                    </div>
                                                </td>
                                                <td>
                                                    <span className="badge bg-light text-dark border">
                                                        {f.employe?.matricule}
                                                    </span>
                                                </td>
                                                <td>
                                                    <span className="fw-semibold">
                                                        {MOIS[f.periode_mois - 1]} {f.periode_annee}
                                                    </span>
                                                </td>
                                                <td>{parseFloat(f.salaire_brut).toLocaleString('fr-FR')} FCFA</td>
                                                <td className="fw-bold text-success">
                                                    {parseFloat(f.salaire_net).toLocaleString('fr-FR')} FCFA
                                                </td>
                                                <td className="text-danger">
                                                    -{cotisations.toLocaleString('fr-FR')} FCFA
                                                </td>
                                                <td className="text-muted small">
                                                    {f.date_generation
                                                        ? new Date(f.date_generation).toLocaleDateString('fr-FR')
                                                        : '—'}
                                                </td>
                                                <td>
                                                    <button
                                                        className="btn btn-sm btn-outline-danger"
                                                        onClick={() => handleSupprimer(f.id)}
                                                        title="Supprimer"
                                                    >
                                                        <i className="bi bi-trash"></i>
                                                    </button>
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* Formulaire ajout */}
            {afficherFormulaire && (
                <Form_AjoutFiche
                    onFermer={() => setAfficherFormulaire(false)}
                    onSuccess={() => {
                        setAfficherFormulaire(false)
                        chargerFiches()
                    }}
                />
            )}

            {/* ── Agent IA Paie ── */}
            {agentOuvert ? (
                <AgentPaiePanel
                    onFermer={() => setAgentOuvert(false)}
                    onRafraichir={chargerFiches}
                />
            ) : (
                <BoutonAgentPaie
                    onClick={() => setAgentOuvert(true)}
                    actif={false}
                />
            )}
        </div>
    )
}

//  Formulaire d'ajout (identique à l'original) ─
function Form_AjoutFiche({ onFermer, onSuccess }) {
    const [employes, setEmployes] = useState([])
    const [erreur, setErreur] = useState('')
    const [chargement, setChargement] = useState(false)
    const [employeSelectionne, setEmployeSelectionne] = useState(null)

    const [form, setForm] = useState({
        employe_id: '',
        periode_mois: new Date().getMonth() + 1,
        periode_annee: new Date().getFullYear(),
    })

    useEffect(() => {
        Service_Employe.listerTous().then(r => setEmployes(r.data))
    }, [])

    const handleChange = e => {
        const { name, value } = e.target
        setForm(prev => ({ ...prev, [name]: value }))
    
        if (name === 'employe_id') {
            const emp = employes.find(e => e.id === value)
            if (emp) setEmployeSelectionne(emp)
        }
    }
    
    const handleSubmit = async e => {
        e.preventDefault()
        setErreur('')
        setChargement(true)
        try {
            await Service_FichePaie.creer({
                employe_id: form.employe_id,
                periode_mois: parseInt(form.periode_mois),
                periode_annee: parseInt(form.periode_annee)
            })
            onSuccess()
        } catch (err) {
            setErreur(err.response?.data?.detail || 'Erreur lors de la création')
        } finally {
            setChargement(false)
        }
    }

    return (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1050 }}>
            <div className="modal-dialog modal-lg modal-dialog-scrollable">
                <div className="modal-content">
                    <div className="modal-header text-white" style={{ background: 'var(--couleur-principale)' }}>
                        <h5 className="modal-title">
                            <i className="bi bi-plus-circle me-2"></i>Générer une fiche de paie
                        </h5>
                        <button className="btn-close btn-close-white" onClick={onFermer}></button>
                    </div>

                    <div className="modal-body">
                        {erreur && (
                            <div className="alert alert-danger py-2">
                                <i className="bi bi-exclamation-triangle me-2"></i>{erreur}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} id="form-fiche">
                            <h6 className="fw-bold text-primary border-bottom pb-2 mb-3">
                                <i className="bi bi-person me-2"></i>Employé
                            </h6>
                            <div className="mb-4">
                                <label className="form-label">Sélectionner un employé *</label>
                                <select name="employe_id" className="form-select" value={form.employe_id} onChange={handleChange} required>
                                    <option value="">-- Choisir un employé --</option>
                                    {employes.map(e => (
                                        <option key={e.id} value={e.id}>
                                            {e.matricule} — {e.prenom} {e.nom}
                                        </option>
                                    ))}
                                </select>
                                {employeSelectionne && (
                                    <div className="alert alert-light border mt-2 py-2 small">
                                        <i className="bi bi-info-circle me-2 text-primary"></i>
                                        Salaire de base contractuel :
                                        <strong className="ms-1">
                                            {parseFloat(employeSelectionne.salaire_base_contrat).toLocaleString('fr-FR')} FCFA
                                        </strong>
                                    </div>
                                )}
                            </div>

                            <h6 className="fw-bold text-primary border-bottom pb-2 mb-3">
                                <i className="bi bi-calendar me-2"></i>Période
                            </h6>
                            <div className="row g-3 mb-4">
                                <div className="col-md-6">
                                    <label className="form-label">Mois *</label>
                                    <select name="periode_mois" className="form-select" value={form.periode_mois} onChange={handleChange} required>
                                        {MOIS.map((m, i) => (
                                            <option key={i} value={i + 1}>{m}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="col-md-6">
                                    <label className="form-label">Année *</label>
                                    <select name="periode_annee" className="form-select" value={form.periode_annee} onChange={handleChange} required>
                                        <option value="2024">2024</option>
                                        <option value="2025">2025</option>
                                        <option value="2026">2026</option>
                                    </select>
                                </div>
                            </div>
                        </form>
                    </div>

                    <div className="modal-footer">
                        <button className="btn btn-secondary" onClick={onFermer}>
                            <i className="bi bi-x me-2"></i>Annuler
                        </button>
                        <button type="submit" form="form-fiche" className="btn btn-primary" disabled={chargement}>
                            {chargement
                                ? <><span className="spinner-border spinner-border-sm me-2"></span>Génération...</>
                                : <><i className="bi bi-check2 me-2"></i>Générer la fiche</>
                            }
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}