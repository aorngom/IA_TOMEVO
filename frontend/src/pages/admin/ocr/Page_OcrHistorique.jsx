import { useState, useEffect } from 'react'
import Service_ConversationIA from '../../../services/Service_ConversationIA'

//  UTILITAIRES 
const formatDate = (iso) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('fr-FR', {
        day: '2-digit', month: 'short', year: 'numeric'
    })
}

const formatDateHeure = (iso) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleString('fr-FR', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    })
}

const tempsRelatif = (iso) => {
    if (!iso) return ''
    const diff = Date.now() - new Date(iso).getTime()
    const minutes = Math.floor(diff / 60000)
    const heures = Math.floor(diff / 3600000)
    const jours = Math.floor(diff / 86400000)
    if (minutes < 1) return "À l'instant"
    if (minutes < 60) return `Il y a ${minutes} min`
    if (heures < 24) return `Il y a ${heures}h`
    if (jours < 7) return `Il y a ${jours}j`
    return formatDate(iso)
}

const BADGE_ACTION = {
    OUVRIR_FORMULAIRE: { label: 'Formulaire', classe: 'bg-primary' },
    REUNION_CREEE: { label: 'Réunion', classe: 'bg-success' },
}

//  MODAL DÉTAIL CONVERSATION 
function ModalDetailConversation({ conversationId, onFermer }) {
    const [conversation, setConversation] = useState(null)
    const [chargement, setChargement] = useState(true)

    useEffect(() => {
        if (!conversationId) return
        setChargement(true)
        Service_ConversationIA.detail(conversationId)
            .then(r => setConversation(r.data))
            .catch(() => setConversation(null))
            .finally(() => setChargement(false))
    }, [conversationId])

    return (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1055 }}>
            <div className="modal-dialog modal-lg modal-dialog-scrollable">
                <div className="modal-content border-0 shadow">
                    <div className="modal-header bg-primary text-white">
                        <div>
                            <h5 className="modal-title mb-0">
                                <i className="bi bi-chat-text me-2"></i>
                                {conversation?.titre || 'Conversation'}
                            </h5>
                            {conversation && (
                                <small className="opacity-75">
                                    {formatDateHeure(conversation.created_at)} · {conversation.messages?.length || 0} messages
                                </small>
                            )}
                        </div>
                        <button className="btn-close btn-close-white" onClick={onFermer}></button>
                    </div>

                    <div className="modal-body" style={{ backgroundColor: '#f8f9fa' }}>
                        {chargement ? (
                            <div className="text-center py-4">
                                <div className="spinner-border text-primary spinner-border-sm"></div>
                                <p className="small text-muted mt-2">Chargement...</p>
                            </div>
                        ) : !conversation ? (
                            <div className="text-center text-muted py-4">Conversation introuvable</div>
                        ) : (
                            <div>
                                {conversation.messages.map((m, i) => (
                                    <div key={i} className={`mb-3 d-flex ${m.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}>
                                        <div style={{ maxWidth: '80%' }}>
                                            {m.action && BADGE_ACTION[m.action] && (
                                                <div className={`mb-1 ${m.role === 'user' ? 'text-end' : 'text-start'}`}>
                                                    <span className={`badge ${BADGE_ACTION[m.action].classe}`} style={{ fontSize: 10 }}>
                                                        <i className="bi bi-lightning-fill me-1"></i>
                                                        {BADGE_ACTION[m.action].label}
                                                    </span>
                                                </div>
                                            )}

                                            {/* Bulle */}
                                            <div
                                                className={`p-2 px-3 rounded-3 ${m.role === 'user'
                                                    ? 'bg-primary text-white'
                                                    : 'bg-white border shadow-sm text-dark'
                                                }`}
                                                style={{ fontSize: '0.88rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
                                            >
                                                {m.content}
                                            </div>

                                            {/* Heure */}
                                            <div className={`text-muted mt-1 ${m.role === 'user' ? 'text-end' : 'text-start'}`}
                                                style={{ fontSize: 10 }}>
                                                {formatDateHeure(m.created_at)}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="modal-footer">
                        <button className="btn btn-secondary" onClick={onFermer}>Fermer</button>
                    </div>
                </div>
            </div>
        </div>
    )
}

//  PAGE PRINCIPALE 
export default function Page_OcrHistorique() {
    const [conversations, setConversations] = useState([])
    const [chargement, setChargement] = useState(true)
    const [recherche, setRecherche] = useState('')
    const [conversationSelectionnee, setConversationSelectionnee] = useState(null)

    const charger = async () => {
        setChargement(true)
        try {
            const r = await Service_ConversationIA.listerToutes()
            setConversations(r.data)
        } catch (e) {
            console.error(e)
        } finally {
            setChargement(false)
        }
    }

    useEffect(() => { charger() }, [])

    const supprimer = async (e, id) => {
        e.stopPropagation()
        if (!window.confirm('Supprimer cette conversation ?')) return
        try {
            await Service_ConversationIA.supprimer(id)
            charger()
        } catch (err) {
            console.error(err)
        }
    }

    const filtrees = conversations.filter(c =>
        (c.titre || '').toLowerCase().includes(recherche.toLowerCase())
    )

    // Grouper par date
    const groupesParDate = filtrees.reduce((acc, conv) => {
        const date = formatDate(conv.updated_at)
        if (!acc[date]) acc[date] = []
        acc[date].push(conv)
        return acc
    }, {})

    return (
        <div>
            {/* En-tête */}
            <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h4 className="fw-bold mb-1">
                        <i className="bi bi-clock-history me-2 text-primary"></i>Historique des conversations
                    </h4>
                    <p className="text-muted small mb-0">{conversations.length} conversation(s) enregistrée(s)</p>
                </div>
            </div>

            {/* Stats */}
            <div className="row g-3 mb-4">
                {[
                    {
                        label: 'Conversations',
                        valeur: conversations.length,
                        icon: 'bi-chat-text',
                        couleur: 'primary'
                    },
                    {
                        label: 'Messages total',
                        valeur: conversations.reduce((a, c) => a + (c.nombre_messages || 0), 0),
                        icon: 'bi-chat-dots',
                        couleur: 'info'
                    },
                    {
                        label: 'Formulaires ouverts',
                        valeur: conversations.filter(c => c.titre?.toLowerCase().includes('formulaire') || false).length,
                        icon: 'bi-person-plus',
                        couleur: 'success'
                    },
                    {
                        label: 'Aujourd\'hui',
                        valeur: conversations.filter(c => {
                            const d = new Date(c.updated_at)
                            const auj = new Date()
                            return d.toDateString() === auj.toDateString()
                        }).length,
                        icon: 'bi-calendar-check',
                        couleur: 'warning'
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
                            placeholder="Rechercher dans les conversations..."
                            value={recherche}
                            onChange={e => setRecherche(e.target.value)}
                        />
                        {recherche && (
                            <button className="btn btn-outline-secondary" onClick={() => setRecherche('')}>
                                <i className="bi bi-x"></i>
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Liste groupée par date */}
            {chargement ? (
                <div className="text-center py-5">
                    <div className="spinner-border text-primary"></div>
                    <p className="mt-2 text-muted">Chargement de l'historique...</p>
                </div>
            ) : filtrees.length === 0 ? (
                <div className="text-center py-5 text-muted">
                    <i className="bi bi-chat-square-text fs-1 d-block mb-2 opacity-25"></i>
                    {recherche ? 'Aucune conversation trouvée' : 'Aucune conversation enregistrée'}
                    {!recherche && (
                        <p className="small mt-2">
                            Les conversations apparaîtront ici dès que vous utiliserez l'assistant IA.
                        </p>
                    )}
                </div>
            ) : (
                Object.entries(groupesParDate).map(([date, convs]) => (
                    <div key={date} className="mb-4">
                        {/* Séparateur de date */}
                        <div className="d-flex align-items-center gap-2 mb-3">
                            <div className="flex-grow-1 border-top"></div>
                            <span className="badge bg-light text-muted border fw-normal px-3">
                                <i className="bi bi-calendar3 me-1"></i>{date}
                            </span>
                            <div className="flex-grow-1 border-top"></div>
                        </div>

                        {/* Conversations du groupe */}
                        <div className="card border-0 shadow-sm">
                            {convs.map((conv, i) => (
                                <div
                                    key={conv.id}
                                    className={`d-flex align-items-center gap-3 p-3 cursor-pointer hover-bg-light ${i < convs.length - 1 ? 'border-bottom' : ''}`}
                                    style={{ cursor: 'pointer', transition: 'background 0.15s' }}
                                    onClick={() => setConversationSelectionnee(conv.id)}
                                    onMouseEnter={e => e.currentTarget.style.backgroundColor = '#f8f9fa'}
                                    onMouseLeave={e => e.currentTarget.style.backgroundColor = ''}
                                >
                                    {/* Icône */}
                                    <div
                                        className="rounded-circle bg-primary bg-opacity-10 d-flex align-items-center justify-content-center flex-shrink-0"
                                        style={{ width: 42, height: 42 }}
                                    >
                                        <i className="bi bi-chat-text text-primary"></i>
                                    </div>

                                    {/* Contenu */}
                                    <div className="flex-grow-1 min-w-0">
                                        <div className="d-flex align-items-center gap-2 mb-1">
                                            <span className="fw-semibold text-truncate" style={{ maxWidth: 400 }}>
                                                {conv.titre || 'Conversation sans titre'}
                                            </span>
                                        </div>
                                        <div className="d-flex align-items-center gap-2 text-muted small">
                                            <span>
                                                <i className="bi bi-chat-dots me-1"></i>
                                                {conv.nombre_messages} message(s)
                                            </span>
                                            <span>·</span>
                                            <span>{tempsRelatif(conv.updated_at)}</span>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="d-flex gap-2 flex-shrink-0">
                                        <button
                                            className="btn btn-sm btn-outline-primary"
                                            title="Voir la conversation"
                                            onClick={e => { e.stopPropagation(); setConversationSelectionnee(conv.id) }}
                                        >
                                            <i className="bi bi-eye"></i>
                                        </button>
                                        <button
                                            className="btn btn-sm btn-outline-danger"
                                            title="Supprimer"
                                            onClick={e => supprimer(e, conv.id)}
                                        >
                                            <i className="bi bi-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))
            )}

            {/* Modal */}
            {conversationSelectionnee && (
                <ModalDetailConversation
                    conversationId={conversationSelectionnee}
                    onFermer={() => setConversationSelectionnee(null)}
                />
            )}
        </div>
    )
}