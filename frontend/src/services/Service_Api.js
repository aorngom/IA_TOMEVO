import axios from 'axios'

const Service_Api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: { 'Content-Type': 'application/json' }
})

// Injecte automatiquement le token JWT dans chaque requête
Service_Api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirige vers /connexion si le token est expiré
Service_Api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('utilisateur')
      window.location.href = '/connexion'
    }
    return Promise.reject(error)
  }
)

export default Service_Api