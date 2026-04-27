import api from './Service_Api'

const Service_ConversationIA = {
    listerToutes: () => api.get('/conversations-ia/'),
    detail: (id) => api.get(`/conversations-ia/${id}`),
    parSession: (sessionId) => api.get(`/conversations-ia/session/${sessionId}`),
    supprimer: (id) => api.delete(`/conversations-ia/${id}`),
}

export default Service_ConversationIA