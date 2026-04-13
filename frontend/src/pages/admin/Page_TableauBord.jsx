import { useAuth } from '../../context/Context_Auth'
import { Link } from 'react-router-dom'

const raccourcis = [
  { label: 'Employés', icon: 'bi-people-fill', path: '/admin/grh/employes', couleur: 'primary' },
  { label: 'Fiches de paie', icon: 'bi-receipt', path: '/admin/paie/fiches', couleur: 'success' },
  { label: 'Absences', icon: 'bi-calendar-x', path: '/admin/grh/absences', couleur: 'warning' },
  { label: 'Commandes', icon: 'bi-bag-check', path: '/admin/commandes', couleur: 'info' },
  { label: 'OCR / IA', icon: 'bi-file-earmark-medical', path: '/admin/ocr/traitement', couleur: 'danger' },
  { label: 'Config paie', icon: 'bi-sliders', path: '/admin/paie/config', couleur: 'secondary' },
]

export default function Page_TableauBord() {
  const { utilisateur } = useAuth()

  return (
    <div>
      {/* Titre */}
      <div className="mb-4">
        <h4 className="fw-bold mb-1">
          Bonjour, {utilisateur?.prenom} {utilisateur?.nom} 👋
        </h4>
        <p className="text-muted">Voici un aperçu de votre espace d'administration.</p>
      </div>

      {/* Raccourcis */}
      <div className="row g-3 mb-4">
        {raccourcis.map((item, i) => (
          <div key={i} className="col-6 col-md-4 col-lg-2">
            <Link to={item.path} className="text-decoration-none">
              <div className={`card border-0 shadow-sm text-center p-3 h-100 border-top border-4 border-${item.couleur}`}>
                <i className={`bi ${item.icon} text-${item.couleur} fs-2 mb-2`}></i>
                <div className="small fw-semibold text-dark">{item.label}</div>
              </div>
            </Link>
          </div>
        ))}
      </div>

      {/* Info */}
      <div className="alert alert-success d-flex align-items-center gap-2">
        <i className="bi bi-info-circle-fill fs-5"></i>
        <div>
          Système opérationnel. Les modules <strong>GRH</strong> et <strong>Paie</strong> sont prêts à être utilisés.
        </div>
      </div>
    </div>
  )
}