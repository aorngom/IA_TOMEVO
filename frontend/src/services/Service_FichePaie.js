import Service_Api from './Service_Api'

const Service_FichePaie = {
    listerToutes: () => Service_Api.get('/paie/'),
    obtenir: (id) => Service_Api.get(`/paie/${id}`),
    parEmploye: (employeId) => Service_Api.get(`/paie/employe/${employeId}`),
    creer: (donnees) => Service_Api.post('/paie/', donnees),
    supprimer: (id) => Service_Api.delete(`/paie/${id}`),
}

export default Service_FichePaie