import { Link } from 'react-router-dom'
import { useAuth } from '../../context/Context_Auth'

export default function Page_Accueil() {
  const { utilisateur } = useAuth()

  return (
    <div>
      {/* Hero */}
      <section className="bg-success text-white py-5">
        <div className="container py-4 text-center">
          <h1 className="display-4 fw-bold mb-3">
            Bienvenue{utilisateur?.prenom ? `, ${utilisateur.prenom}` : ''} 👋
          </h1>
          <p className="lead mb-4">
            Des poulets élevés naturellement au Sénégal, livrés frais chez vous.
          </p>
          <div className="d-flex gap-3 justify-content-center">
            <Link to="/boutique" className="btn btn-light btn-lg fw-semibold text-success">
              <i className="bi bi-shop me-2"></i>Voir la boutique
            </Link>
            <Link to="/notre-elevage" className="btn btn-outline-light btn-lg">
              <i className="bi bi-tree me-2"></i>Notre élevage
            </Link>
          </div>
        </div>
      </section>

      {/* Points forts */}
      <section className="py-5 bg-light">
        <div className="container">
          <h2 className="text-center fw-bold mb-5">Pourquoi choisir Jariniou ?</h2>
          <div className="row g-4">
            {[
              { icon: 'bi-heart-fill', titre: 'Élevage naturel', texte: 'Nos poulets sont élevés sans antibiotiques dans un environnement sain.', couleur: 'text-danger' },
              { icon: 'bi-truck', titre: 'Livraison rapide', texte: 'Livraison à domicile ou retrait sur place selon votre convenance.', couleur: 'text-primary' },
              { icon: 'bi-shield-check', titre: 'Qualité garantie', texte: 'Chaque produit est contrôlé avant livraison pour votre satisfaction.', couleur: 'text-success' },
            ].map((item, i) => (
              <div key={i} className="col-md-4">
                <div className="card border-0 shadow-sm h-100 text-center p-4">
                  <i className={`bi ${item.icon} ${item.couleur} fs-1 mb-3`}></i>
                  <h5 className="fw-bold">{item.titre}</h5>
                  <p className="text-muted">{item.texte}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-5 bg-success text-white text-center">
        <div className="container">
          <h3 className="fw-bold mb-3">Prêt à commander ?</h3>
          <p className="mb-4">Paiement via Wave, Orange Money ou sur place.</p>
          <Link to="/boutique" className="btn btn-light btn-lg fw-semibold text-success">
            <i className="bi bi-cart-plus me-2"></i>Commander maintenant
          </Link>
        </div>
      </section>
    </div>
  )
}