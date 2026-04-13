import { createContext, useContext, useState, useEffect } from 'react'
import Service_Auth from '../services/Service_Auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [utilisateur, setUtilisateur] = useState(null)
  const [chargement, setChargement] = useState(true)

  useEffect(() => {
    // Au démarrage, récupère l'utilisateur depuis le localStorage
    const u = Service_Auth.getUtilisateur()
    if (u) setUtilisateur(u)
    setChargement(false)
  }, [])

  const login = async (email, mot_de_passe) => {
    const data = await Service_Auth.login(email, mot_de_passe)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('utilisateur', JSON.stringify(data.utilisateur))
    setUtilisateur(data.utilisateur)
    return data.utilisateur
  }

  const logout = () => {
    Service_Auth.logout()
    setUtilisateur(null)
  }

  return (
    <AuthContext.Provider value={{ utilisateur, login, logout, chargement }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}