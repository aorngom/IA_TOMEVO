import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../context/Context_Auth'

export default function Page_Connexion() {
  const { login, utilisateur } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [motDePasse, setMotDePasse] = useState('')
  const [erreur, setErreur] = useState('')
  const [chargement, setChargement] = useState(false)

  if (utilisateur) {
    if (utilisateur.role === 'admin' || utilisateur.role === 'rh')
      navigate('/admin', { replace: true })
    else navigate('/', { replace: true })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErreur('')
    setChargement(true)
    try {
      const u = await login(email, motDePasse)
      if (u.role === 'admin' || u.role === 'rh') navigate('/admin', { replace: true })
      else navigate('/', { replace: true })
    } catch (err) {
      setErreur(err.response?.data?.detail || 'Email ou mot de passe incorrect')
    } finally {
      setChargement(false)
    }
  }

  return (
    <div
      className="min-vh-100 d-flex align-items-center justify-content-center"
      style={{
        background: 'linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%)',
      }}
    >
      {/* Cercles décoratifs en arrière-plan */}
      <div style={{
        position: 'fixed', top: '-100px', right: '-100px',
        width: '400px', height: '400px', borderRadius: '50%',
        background: 'rgba(230,57,70,0.08)', pointerEvents: 'none'
      }} />
      <div style={{
        position: 'fixed', bottom: '-80px', left: '-80px',
        width: '300px', height: '300px', borderRadius: '50%',
        background: 'rgba(230,57,70,0.06)', pointerEvents: 'none'
      }} />

      <div
        className="card shadow-lg border-0 fade-in"
        style={{ width: '440px', borderRadius: 'var(--bordure-radius)' }}
      >
        <div className="card-body p-5">

          {/* Logo */}
          <div className="text-center mb-4">
            <img
              src="/jariniou.png"
              alt="Jariniou"
              style={{ height: 64, objectFit: 'contain' }}
              className="mb-3"
            />
            <h5 className="fw-bold text-dark mb-1">Bienvenue</h5>
            <p className="text-muted small mb-0">
              Connectez-vous à votre espace
            </p>
          </div>

          {/* Ligne décorative */}
          <div style={{
            height: 3, borderRadius: 10, marginBottom: 28,
            background: 'linear-gradient(90deg, var(--couleur-principale), var(--couleur-principale-light))'
          }} />

          {/* Erreur */}
          {erreur && (
            <div className="alert alert-danger d-flex align-items-center gap-2 py-2 mb-3"
              style={{ borderRadius: 'var(--bordure-radius-sm)', fontSize: '0.88rem' }}>
              <i className="bi bi-exclamation-triangle-fill"></i>
              <span>{erreur}</span>
            </div>
          )}

          {/* Formulaire */}
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label fw-semibold small text-dark">
                Adresse email
              </label>
              <div className="input-group">
                <span className="input-group-text bg-white border-end-0"
                  style={{ borderRadius: 'var(--bordure-radius-sm) 0 0 var(--bordure-radius-sm)' }}>
                  <i className="bi bi-envelope text-muted"></i>
                </span>
                <input
                  type="email"
                  className="form-control border-start-0 ps-0"
                  placeholder="exemple@jariniou.sn"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{ borderRadius: '0 var(--bordure-radius-sm) var(--bordure-radius-sm) 0' }}
                  required
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="form-label fw-semibold small text-dark">
                Mot de passe
              </label>
              <div className="input-group">
                <span className="input-group-text bg-white border-end-0"
                  style={{ borderRadius: 'var(--bordure-radius-sm) 0 0 var(--bordure-radius-sm)' }}>
                  <i className="bi bi-lock text-muted"></i>
                </span>
                <input
                  type="password"
                  className="form-control border-start-0 ps-0"
                  placeholder="••••••••"
                  value={motDePasse}
                  onChange={(e) => setMotDePasse(e.target.value)}
                  style={{ borderRadius: '0 var(--bordure-radius-sm) var(--bordure-radius-sm) 0' }}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn w-100 py-2 fw-semibold text-white"
              disabled={chargement}
              style={{
                background: 'linear-gradient(135deg, var(--couleur-principale), var(--couleur-principale-dark))',
                border: 'none',
                borderRadius: 'var(--bordure-radius-sm)',
                boxShadow: '0 4px 15px rgba(230,57,70,0.35)',
                transition: 'var(--transition)'
              }}
            >
              {chargement ? (
                <><span className="spinner-border spinner-border-sm me-2"></span>Connexion en cours...</>
              ) : (
                <><i className="bi bi-box-arrow-in-right me-2"></i>Se connecter</>
              )}
            </button>
          </form>

          {/* Footer carte */}
          <p className="text-center text-muted mt-4 mb-0" style={{ fontSize: '0.78rem' }}>
            © {new Date().getFullYear()} Jariniou — Tous droits réservés
          </p>
        </div>
      </div>
    </div>
  )
}