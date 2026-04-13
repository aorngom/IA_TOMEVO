import { useAuth } from '../../context/Context_Auth'

export default function Comp_EnTete() {
  const { utilisateur } = useAuth()

  return (
    <header className="bg-white border-bottom shadow-sm px-4 py-3 d-flex justify-content-between align-items-center">
      <h6 className="mb-0 text-muted fw-semibold">
        <i className="bi bi-grid me-2"></i>Espace Administration
      </h6>
      <div className="d-flex align-items-center gap-2">
        <div className="bg-success rounded-circle d-flex align-items-center justify-content-center text-white fw-bold"
          style={{ width: 36, height: 36, fontSize: 14 }}>
          {utilisateur?.prenom?.[0]}{utilisateur?.nom?.[0]}
        </div>
        <div>
          <div className="fw-semibold small">{utilisateur?.prenom} {utilisateur?.nom}</div>
          <div className="text-muted" style={{ fontSize: 11 }}>
            {utilisateur?.role === 'admin' ? 'Administrateur' : 'RH'}
          </div>
        </div>
      </div>
    </header>
  )
}