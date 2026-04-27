import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import Service_Ocr from '../../../services/Service_Ocr';
import { Form_AjoutEmploye } from '../grh/Page_ListeEmployes';

const formatDate = (iso) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('fr-FR', {
        day: '2-digit', month: 'long', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    })
}

function CarteReunionIA({ reunion }) {
    return (
        <div className="card border-success border-2 mt-2 mb-1 shadow-sm" style={{ maxWidth: 420 }}>
            <div className="card-header bg-success text-white py-2">
                <i className="bi bi-check-circle me-2"></i>
                <strong>Réunion créée avec succès</strong>
            </div>
            <div className="card-body py-2 px-3">
                <div className="fw-bold mb-1">{reunion.sujet}</div>
                <div className="text-muted small mb-1">
                    <i className="bi bi-calendar3 me-1"></i>{formatDate(reunion.date_heure)}
                </div>
                {reunion.lieu && (
                    <div className="text-muted small mb-1">
                        <i className="bi bi-geo-alt me-1"></i>{reunion.lieu}
                    </div>
                )}
                <div className="small mt-2">
                    <span className="text-muted">Participants : </span>
                    {reunion.participants.length > 0
                        ? reunion.participants.map((p, i) => (
                            <span key={i} className="badge bg-light text-dark border me-1">{p}</span>
                        ))
                        : <span className="text-muted">Aucun</span>
                    }
                </div>
            </div>
        </div>
    )
}

export default function Page_OcrTraitement() {
    const navigate = useNavigate()
    const [sessionId] = useState(() => uuidv4())   // ← Généré une fois au montage

    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Bonjour ! Je suis l'assistant IA Jariniou. Je peux analyser vos documents RH et organiser des réunions entre vos employés. Comment puis-je vous aider ?"
        }
    ]);
    const [metadonnees, setMetadonnees] = useState({})
    const [input, setInput] = useState('');
    const [fichier, setFichier] = useState(null);
    const [analyse, setAnalyse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [chatLoading, setChatLoading] = useState(false);
    const chatEndRef = useRef(null);
    const [afficherFormulaire, setAfficherFormulaire] = useState(false);
    const [donneesPreRemplies, setDonneesPreRemplies] = useState(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setFichier(file);
        setLoading(true);
        try {
            const res = await Service_Ocr.analyser(file);
            setAnalyse(res.data);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `Document "${file.name}" analysé avec succès. Posez-moi vos questions ou dites "Remplis le formulaire".`
            }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Erreur de lecture du document." }]);
        } finally { setLoading(false); }
    };

    const handleSend = async () => {
        if (!input.trim() || chatLoading) return;
        const userMsg = { role: 'user', content: input };
        const nouveauxMessages = [...messages, userMsg];
        setMessages(nouveauxMessages);
        setInput('');
        setChatLoading(true);

        try {
            const contexteData = analyse ? JSON.stringify(analyse) : "Aucun document chargé.";
            const res = await Service_Ocr.chat(nouveauxMessages, contexteData, sessionId); // ← session_id envoyé

            if (res.data.action === "OUVRIR_FORMULAIRE") {
                setDonneesPreRemplies(res.data.donnees);
                setAfficherFormulaire(true);
                setMessages(prev => [...prev, { role: 'assistant', content: res.data.reponse }]);
            }
            else if (res.data.action === "REUNION_CREEE") {
                const indexMsg = nouveauxMessages.length
                setMessages(prev => [...prev, { role: 'assistant', content: res.data.reponse }]);
                setMetadonnees(prev => ({
                    ...prev,
                    [indexMsg]: { type: 'REUNION_CREEE', reunion: res.data.reunion }
                }));
            }
            else {
                setMessages(prev => [...prev, { role: 'assistant', content: res.data.reponse }]);
            }
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Erreur de connexion avec l'IA." }]);
        } finally { setChatLoading(false); }
    };

    return (
        <div className="admin-content fade-in p-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h4 className="fw-bold mb-0">Assistant Intelligent & OCR</h4>
                    <p className="text-muted small mb-0">Analyse de documents · Formulaires · Organisation de réunions</p>
                </div>
                <div className="d-flex gap-2">
                    <button className="btn btn-outline-secondary btn-sm" onClick={() => navigate('/admin/ocr/historique')}>
                        <i className="bi bi-clock-history me-2"></i>Historique
                    </button>
                    <button className="btn btn-outline-primary btn-sm" onClick={() => navigate('/admin/grh/reunions')}>
                        <i className="bi bi-camera-video me-2"></i>Réunions
                    </button>
                </div>
            </div>

            {afficherFormulaire && (
                <Form_AjoutEmploye
                    onFermer={() => { setAfficherFormulaire(false); setDonneesPreRemplies(null); }}
                    onSuccess={() => {
                        setAfficherFormulaire(false);
                        setMessages(prev => [...prev, { role: 'assistant', content: "L'employé a été enregistré avec succès." }]);
                    }}
                    donneesIA={donneesPreRemplies}
                />
            )}

            <div className="row g-3" style={{ height: 'calc(100vh - 200px)' }}>
                {/* Panneau gauche */}
                <div className="col-md-4">
                    <div className="card h-100 shadow-sm border-0 p-3 d-flex flex-column">
                        <div className="fw-bold mb-3">
                            <i className="bi bi-file-earmark-text me-2 text-primary"></i>Document & Analyse
                        </div>
                        <label className="btn btn-outline-primary w-100 mb-3">
                            <i className="bi bi-upload me-2"></i>
                            {fichier ? fichier.name : 'Charger un document'}
                            <input type="file" className="d-none" onChange={handleUpload} accept="image/*,.pdf" />
                        </label>

                        {loading && (
                            <div className="text-center mt-2">
                                <div className="spinner-border text-primary spinner-border-sm"></div>
                                <p className="small text-muted mt-1">Analyse en cours...</p>
                            </div>
                        )}

                        {analyse && !loading && (
                            <div className="flex-grow-1 overflow-auto">
                                <div className="alert alert-success py-2 small mb-2">
                                    <i className="bi bi-check-circle me-1"></i>Document analysé
                                </div>
                                <div className="bg-light rounded p-2">
                                    <pre className="mb-0" style={{ fontSize: '0.75rem', whiteSpace: 'pre-wrap' }}>
                                        {typeof analyse.texte === 'string' ? analyse.texte : JSON.stringify(analyse, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        )}

                        {!analyse && !loading && (
                            <div className="flex-grow-1 d-flex flex-column align-items-center justify-content-center text-muted text-center">
                                <i className="bi bi-file-earmark-arrow-up fs-1 opacity-25 mb-2"></i>
                                <p className="small">Chargez un document pour l'analyser</p>
                            </div>
                        )}

                        <div className="mt-3 border-top pt-3">
                            <div className="text-muted small mb-2 fw-semibold">Suggestions :</div>
                            {[
                                "Organise une réunion demain à 10h avec Moussa et Awa",
                                "Remplis le formulaire avec ce document",
                                "Liste les employés du département Élevage"
                            ].map((s, i) => (
                                <button key={i} className="btn btn-sm btn-light border w-100 text-start mb-1"
                                    style={{ fontSize: 11, whiteSpace: 'normal' }} onClick={() => setInput(s)}>
                                    <i className="bi bi-arrow-right me-1 text-primary"></i>{s}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Panneau droit : Chat */}
                <div className="col-md-8">
                    <div className="card h-100 shadow-sm border-0 d-flex flex-column">
                        <div className="flex-grow-1 p-3 overflow-auto" style={{ backgroundColor: '#f8f9fa' }}>
                            {messages.map((m, i) => (
                                <div key={i} className={`mb-3 d-flex ${m.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}>
                                    <div>
                                        <div className={`d-inline-block p-2 px-3 rounded-3 ${m.role === 'user' ? 'bg-primary text-white' : 'bg-white border shadow-sm text-dark'}`}
                                            style={{ maxWidth: 480, fontSize: '0.9rem', whiteSpace: 'pre-wrap' }}>
                                            {m.content}
                                        </div>
                                        {metadonnees[i]?.type === 'REUNION_CREEE' && (
                                            <div>
                                                <CarteReunionIA reunion={metadonnees[i].reunion} />
                                                <button className="btn btn-sm btn-success mt-1" onClick={() => navigate('/admin/grh/reunions')}>
                                                    <i className="bi bi-arrow-right me-1"></i>Voir la réunion
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {chatLoading && (
                                <div className="d-flex justify-content-start mb-3">
                                    <div className="bg-white border shadow-sm rounded-3 p-2 px-3">
                                        <div className="d-flex gap-1 align-items-center">
                                            {[0, 0.2, 0.4].map((delay, i) => (
                                                <div key={i} className="rounded-circle bg-secondary"
                                                    style={{ width: 6, height: 6, animation: `pulse 1s infinite ${delay}s` }}></div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>
                        <div className="p-3 border-top bg-white">
                            <div className="input-group">
                                <input type="text" className="form-control border-end-0" value={input}
                                    onChange={e => setInput(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleSend()}
                                    placeholder="Posez une question ou demandez d'organiser une réunion..."
                                    disabled={chatLoading} />
                                <button className="btn btn-primary" onClick={handleSend} disabled={chatLoading || !input.trim()}>
                                    <i className="bi bi-send-fill"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}