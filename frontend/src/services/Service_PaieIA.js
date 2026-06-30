import Service_Api from './Service_Api'

const Service_PaieIA = {
    // Chat principal
    chat: (messages, sessionId, fichierBase64 = null, fichierNom = null) =>
        Service_Api.post('/paie-ia/chat', {
            messages,
            session_id: sessionId ?? null,
            fichier_base64: fichierBase64,
            fichier_nom: fichierNom
        }),

    // Convertir fichier en base64
    fichierVersBase64: (fichier) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => resolve(reader.result.split(',')[1])
            reader.onerror = () => reject(new Error('Erreur lecture fichier'))
            reader.readAsDataURL(fichier)
        })
    },

    // Récupérer les notifications en attente
    getNotifications: () =>
        Service_Api.get('/paie-ia/notifications'),

    // Marquer une notification comme lue
    marquerLue: (rappelId) =>
        Service_Api.post(`/paie-ia/notifications/${rappelId}/lue`),
}

export default Service_PaieIA