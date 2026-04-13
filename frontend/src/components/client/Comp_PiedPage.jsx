export default function Comp_PiedPage() {
    return (
      <footer className="bg-dark text-white py-4 mt-auto">
        <div className="container text-center">
          <p className="mb-1 fw-semibold">
            <i className="bi bi-egg-fried me-2 text-success"></i>Jariniou
          </p>
          <p className="text-muted small mb-0">
            © {new Date().getFullYear()} — Élevage de volailles au Sénégal
          </p>
        </div>
      </footer>
    )
  }