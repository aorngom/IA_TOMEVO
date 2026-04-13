import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/Context_Auth'

const menus = [
  { label: 'Tableau de bord', icon: 'bi-speedometer2', path: '/admin' },
  { label: 'Commandes', icon: 'bi-bag-check', path: '/admin/commandes' },
  { label: 'Produits', icon: 'bi-box-seam', path: '/admin/produits' },
  { titre: 'GRH', items: [
    { label: 'Vue générale', icon: 'bi-people', path: '/admin/grh' },
    { label: 'Employés', icon: 'bi-person-badge', path: '/admin/grh/employes' },
    { label: 'Contrats', icon: 'bi-file-earmark-text', path: '/admin/grh/contrats' },
    { label: 'Absences', icon: 'bi-calendar-x', path: '/admin/grh/absences' },
    { label: 'Congés', icon: 'bi-calendar-check', path: '/admin/grh/conges' },
  ]},
  { titre: 'Paie', items: [
    { label: 'Vue générale', icon: 'bi-cash-stack', path: '/admin/paie' },
    { label: 'Fiches de paie', icon: 'bi-receipt', path: '/admin/paie/fiches' },
    { label: 'Config salaires', icon: 'bi-sliders', path: '/admin/paie/config' },
    { label: 'Lancer la paie', icon: 'bi-play-circle', path: '/admin/paie/lancer' },
  ]},
  { titre: 'OCR / IA', items: [
    { label: 'Traitement', icon: 'bi-file-earmark-medical', path: '/admin/ocr/traitement' },
    { label: 'Historique', icon: 'bi-clock-history', path: '/admin/ocr/historique' },
  ]},
]

export default function Comp_BarreLaterale() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/connexion') }

  return (
    <div className="bg-dark text-white d-flex flex-column position-fixed top-0 start-0 h-100"
      style={{ width: '260px', zIndex: 100, overflowY: 'auto' }}>

      {/* Logo */}
        <div className="sidebar-logo d-flex align-items-center gap-3">
        <img src="/jariniou.png" alt="Jariniou" style={{ height: 38, objectFit: 'contain' }} />
        <div>
            <div className="fw-bold text-white" style={{ fontSize: 15 }}>Jariniou</div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>Administration</div>
        </div>
        </div>

      {/* Navigation */}
      <nav className="flex-grow-1 p-3">
        {menus.map((item, i) => (
          item.titre ? (
            <div key={i} className="mb-2">
              <div className="text-uppercase text-muted small fw-semibold px-2 mb-1 mt-3">
                {item.titre}
              </div>
              {item.items.map((sub, j) => (
                <NavLink key={j} to={sub.path} end={sub.path === '/admin'}
                  className={({ isActive }) =>
                    `d-flex align-items-center gap-2 px-3 py-2 rounded text-decoration-none mb-1 small
                    ${isActive ? 'bg-success text-white' : 'text-secondary'}`
                  }>
                  <i className={`bi ${sub.icon}`}></i>{sub.label}
                </NavLink>
              ))}
            </div>
          ) : (
            <NavLink key={i} to={item.path} end={item.path === '/admin'}
              className={({ isActive }) =>
                `d-flex align-items-center gap-2 px-3 py-2 rounded text-decoration-none mb-1
                ${isActive ? 'bg-success text-white' : 'text-secondary'}`
              }>
              <i className={`bi ${item.icon}`}></i>{item.label}
            </NavLink>
          )
        ))}
      </nav>

      {/* Déconnexion */}
      <div className="p-3 border-top border-secondary">
        <button onClick={handleLogout}
          className="btn btn-outline-danger btn-sm w-100">
          <i className="bi bi-box-arrow-right me-2"></i>Déconnexion
        </button>
      </div>
    </div>
  )
}