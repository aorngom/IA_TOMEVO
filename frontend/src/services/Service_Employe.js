import Service_Api from './Service_Api'

const Service_Employe = {
    listerTous: () => Service_Api.get('/employes/'),
    obtenir: (id) => Service_Api.get(`/employes/${id}`),
    creer: (donnees) => Service_Api.post('/employes/', donnees),
    modifier: (id, donnees) => Service_Api.put(`/employes/${id}`, donnees),
    supprimer: (id) => Service_Api.delete(`/employes/${id}`),
    listerPostes: () => Service_Api.get('/employes/postes/liste'),
    listerDepartements: () => Service_Api.get('/employes/departements/liste'),
}

export default Service_Employe