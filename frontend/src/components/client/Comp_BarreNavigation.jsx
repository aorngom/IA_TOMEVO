import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/Context_Auth'

export default function Comp_BarreNavigation() {
  const { utilisateur, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/connexion')
  }

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-success shadow-sm">
      <div className="container">
        <Link className="navbar-brand d-flex align-items-center gap-2" to="/">
        <img src="/jariniou.png" alt="Jariniou" style={{ height: 38, objectFit: 'contain' }} />
        </Link>

        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navClient">
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navClient">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link className="nav-link" to="/"><i className="bi bi-house me-1"></i>Accueil</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/presentation"><i className="bi bi-info-circle me-1"></i>Présentation</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/notre-elevage"><i className="bi bi-tree me-1"></i>Notre Élevage</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/boutique"><i className="bi bi-shop me-1"></i>Boutique</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/contact"><i className="bi bi-telephone me-1"></i>Contact</Link>
            </li>
          </ul>

          <div className="d-flex align-items-center gap-3">
            <Link to="/panier" className="btn btn-outline-light btn-sm">
              <i className="bi bi-cart3 me-1"></i>Panier
            </Link>
            <span className="text-white-50 small">
              {utilisateur?.prenom} {utilisateur?.nom}
            </span>
            <button onClick={handleLogout} className="btn btn-light btn-sm text-success fw-semibold">
              <i className="bi bi-box-arrow-right me-1"></i>Déconnexion
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}