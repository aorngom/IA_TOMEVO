import Service_Api from './Service_Api'

const Service_Auth = {
  // Appel login vers le backend
  login: async (email, mot_de_passe) => {
    const reponse = await Service_Api.post('/auth/login', { email, mot_de_passe })
    return reponse.data
  },

  // Déconnexion : vide le localStorage
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('utilisateur')
  },

  // Récupère l'utilisateur stocké
  getUtilisateur: () => {
    const data = localStorage.getItem('utilisateur')
    return data ? JSON.parse(data) : null
  },

  // Vérifie si connecté
  estConnecte: () => !!localStorage.getItem('token'),

  // Vérifie le rôle
  estAdmin: () => {
    const u = Service_Auth.getUtilisateur()
    return u?.role === 'admin' || u?.role === 'rh'
  }
}

export default Service_Auth