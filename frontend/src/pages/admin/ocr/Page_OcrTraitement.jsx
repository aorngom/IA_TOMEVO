import React, { useState, useRef, useEffect } from 'react';
import Service_Ocr from '../../../services/Service_Ocr';

export default function Page_OcrTraitement() {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: "Bonjour ! Je suis l'IA Jariniou. Je peux analyser vos documents ou répondre à vos questions sur la gestion de l'élevage. Que puis-je faire pour vous ?" }
    ]);
    const [input, setInput] = useState('');
    const [fichier, setFichier] = useState(null);
    const [analyse, setAnalyse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [chatLoading, setChatLoading] = useState(false);
    const chatEndRef = useRef(null);

    // Scroll automatique vers le bas du chat à chaque nouveau message
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Gestion de l'analyse de document (OCR)
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
                content: `Document "${file.name}" analysé avec succès. Les données ont été extraites. Vous pouvez me poser des questions sur ce document.` 
            }]);
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, { role: 'assistant', content: "❌ Désolé, je n'ai pas pu lire ce document." }]);
        } finally {
            setLoading(false);
        }
    };

    // Envoi de message (Chat contextuel)
    const handleSend = async () => {
        if (!input.trim() || chatLoading) return;

        const userMsg = { role: 'user', content: input };
        
        // CORRECTION : On crée la nouvelle liste ici pour l'envoyer immédiatement à l'API
        const nouveauxMessages = [...messages, userMsg];
        
        setMessages(nouveauxMessages);
        setInput('');
        setChatLoading(true);
        
        try {
            // On prépare le contexte sous forme de chaîne de caractères pour le backend
            const contexteData = analyse ? JSON.stringify(analyse) : "Aucun document chargé.";
            
            const res = await Service_Ocr.chat(nouveauxMessages, contexteData);
            
            setMessages(prev => [...prev, { role: 'assistant', content: res.data.reponse }]);
        } catch (err) {
            console.error("Erreur Chat:", err);
            setMessages(prev => [...prev, { role: 'assistant', content: "Erreur de connexion avec l'IA." }]);
        } finally {
            setChatLoading(false);
        }
    };

    return (
        <div className="admin-content fade-in p-4">
            <div className="d-flex align-items-center justify-content-between mb-4">
                <div>
                    <h4 className="fw-bold mb-0">Assistant Intelligent & OCR</h4>
                    <p className="text-muted small">Analyse de documents RH et support IA</p>
                </div>
                {analyse && (
                    <button className="btn btn-outline-danger btn-sm" onClick={() => {setAnalyse(null); setFichier(null);}}>
                        Effacer l'analyse
                    </button>
                )}
            </div>

            <div className="row g-3" style={{ height: 'calc(100vh - 180px)' }}>
                
                {/* ── PANNEAU GAUCHE : DOCUMENTS ── */}
                <div className="col-lg-4 d-flex flex-column">
                    <div className="card flex-grow-1 p-3 overflow-hidden d-flex flex-column border-0 shadow-sm">
                        <div className="fw-bold mb-3" style={{color: 'var(--couleur-sombre)'}}>Document & Données</div>
                        
                        <div className="upload-zone mb-3">
                            <label className="d-flex flex-column align-items-center justify-content-center p-4 border rounded-3 w-100" style={{cursor: 'pointer', border: '2px dashed #ccc', background: '#fafafa'}}>
                                <i className="bi bi-file-earmark-arrow-up fs-2 text-primary mb-2"></i>
                                <span className="small fw-bold text-muted">Charger un document</span>
                                <input type="file" className="d-none" onChange={handleUpload} accept=".pdf,image/*" />
                            </label>
                        </div>

                        {loading && (
                            <div className="text-center p-4">
                                <div className="spinner-border spinner-border-sm text-primary"></div>
                                <p className="small mt-2">Analyse en cours...</p>
                            </div>
                        )}

                        {analyse && (
                            <div className="flex-grow-1 overflow-auto pe-2">
                                <div className="badge bg-light text-primary border border-primary-subtle w-100 p-2 mb-3">
                                    {analyse.type_document?.toUpperCase() || 'DOCUMENT'}
                                </div>
                                
                                {analyse.champs && Object.entries(analyse.champs).map(([key, val]) => (
                                    <div key={key} className="mb-2 p-2 rounded bg-light border-start border-primary border-3">
                                        <div className="d-flex justify-content-between align-items-center">
                                            <span className="text-muted fw-bold" style={{fontSize: '0.65rem'}}>{key.replace('_', ' ').toUpperCase()}</span>
                                            <span className="badge bg-white text-dark border" style={{fontSize: '0.6rem'}}>
                                                {Math.round(val.confiance * 100)}%
                                            </span>
                                        </div>
                                        <div className="fw-bold text-dark" style={{fontSize: '0.85rem'}}>{val.valeur || 'Non détecté'}</div>
                                    </div>
                                ))}
                            </div>
                        )}
                        
                        {!analyse && !loading && (
                            <div className="text-center text-muted m-auto opacity-50">
                                <i className="bi bi-clipboard-data fs-1"></i>
                                <p className="small mt-2">En attente d'analyse</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* ── PANNEAU DROIT : CHAT ── */}
                <div className="col-lg-8 d-flex flex-column">
                    <div className="card flex-grow-1 d-flex flex-column overflow-hidden border-0 shadow-sm">
                        <div className="card-header bg-white py-3 border-bottom d-flex align-items-center justify-content-between">
                            <div className="d-flex align-items-center gap-2">
                                <div className="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center" style={{width: '35px', height: '35px'}}>
                                    <i className="bi bi-robot"></i>
                                </div>
                                <h6 className="mb-0 fw-bold">Jariniou AI</h6>
                            </div>
                            <span className="badge badge-actif">Connecté</span>
                        </div>

                        {/* Zone de conversation */}
                        <div className="flex-grow-1 p-4 overflow-auto bg-light" style={{backgroundImage: 'radial-gradient(#ddd 0.5px, transparent 0.5px)', backgroundSize: '20px 20px'}}>
                            {messages.map((m, i) => (
                                <div key={i} className={`d-flex mb-4 ${m.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}>
                                    <div className={`p-3 rounded-4 shadow-sm ${m.role === 'user' ? 'bg-primary text-white' : 'bg-white text-dark'}`} style={{maxWidth: '80%', fontSize: '0.9rem'}}>
                                        {m.content}
                                    </div>
                                </div>
                            ))}
                            {chatLoading && (
                                <div className="d-flex mb-4">
                                    <div className="bg-white p-3 rounded-4 shadow-sm border">
                                        <div className="dot-flashing"></div>
                                    </div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>

                        {/* Barre de saisie */}
                        <div className="p-3 bg-white border-top">
                            <div className="input-group">
                                <input 
                                    type="text" 
                                    className="form-control border-secondary-subtle py-2" 
                                    placeholder="Posez une question à l'IA..." 
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                />
                                <button className="btn btn-principal px-4" onClick={handleSend} disabled={chatLoading || !input.trim()}>
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