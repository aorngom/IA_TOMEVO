import api from './Service_Api'

const Service_Reunion = {
    listerToutes: () => api.get('/reunions/'),
    detail: (id) => api.get(`/reunions/${id}`),
    creer: (donnees) => api.post('/reunions/', donnees),
    modifier: (id, donnees) => api.put(`/reunions/${id}`, donnees),
    supprimer: (id) => api.delete(`/reunions/${id}`),
    confirmerPresence: (reunionId, employeId) =>
        api.patch(`/reunions/${reunionId}/presence/${employeId}`),
}

export default Service_Reunion