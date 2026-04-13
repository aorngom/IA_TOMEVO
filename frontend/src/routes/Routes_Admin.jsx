import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '../context/Context_Auth'
import Layout_Admin from '../layouts/Layout_Admin'
import Page_TableauBord from '../pages/admin/Page_TableauBord'
import Page_TableauBordGRH from '../pages/admin/grh/Page_TableauBordGRH'
import Page_ListeEmployes from '../pages/admin/grh/Page_ListeEmployes'
import Page_DetailEmploye from '../pages/admin/grh/Page_DetailEmploye'
import Page_ListeContrats from '../pages/admin/grh/Page_ListeContrats'
import Page_ListeAbsences from '../pages/admin/grh/Page_ListeAbsences'
import Page_ListeConges from '../pages/admin/grh/Page_ListeConges'
import Page_TableauBordPaie from '../pages/admin/paie/Page_TableauBordPaie'
import Page_ListeFichesPaie from '../pages/admin/paie/Page_ListeFichesPaie'
import Page_DetailFichePaie from '../pages/admin/paie/Page_DetailFichePaie'
import Page_ConfigSalaires from '../pages/admin/paie/Page_ConfigSalaires'
import Page_LancerCalculPaie from '../pages/admin/paie/Page_LancerCalculPaie'
import Page_OcrAccueil from '../pages/admin/ocr/Page_OcrAccueil'
import Page_OcrTraitement from '../pages/admin/ocr/Page_OcrTraitement'
import Page_OcrHistorique from '../pages/admin/ocr/Page_OcrHistorique'
import Page_ListeCommandes from '../pages/admin/commandes/Page_ListeCommandes'
import Page_GestionProduits from '../pages/admin/contenu/Page_GestionProduits'

// Protège les routes admin
function RouteProtegeeAdmin({ children }) {
  const { utilisateur, chargement } = useAuth()
  if (chargement) return <div className="text-center mt-5">Chargement...</div>
  if (!utilisateur) return <Navigate to="/connexion" replace />
  if (utilisateur.role === 'client') return <Navigate to="/" replace />
  return children
}

export default function Routes_Admin() {
  return (
    <Routes>
      <Route path="/" element={
        <RouteProtegeeAdmin>
          <Layout_Admin />
        </RouteProtegeeAdmin>
      }>
        <Route index element={<Page_TableauBord />} />

        {/* GRH */}
        <Route path="grh" element={<Page_TableauBordGRH />} />
        <Route path="grh/employes" element={<Page_ListeEmployes />} />
        <Route path="grh/employes/:id" element={<Page_DetailEmploye />} />
        <Route path="grh/contrats" element={<Page_ListeContrats />} />
        <Route path="grh/absences" element={<Page_ListeAbsences />} />
        <Route path="grh/conges" element={<Page_ListeConges />} />

        {/* Paie */}
        <Route path="paie" element={<Page_TableauBordPaie />} />
        <Route path="paie/fiches" element={<Page_ListeFichesPaie />} />
        <Route path="paie/fiches/:id" element={<Page_DetailFichePaie />} />
        <Route path="paie/config" element={<Page_ConfigSalaires />} />
        <Route path="paie/lancer" element={<Page_LancerCalculPaie />} />

        {/* OCR */}
        <Route path="ocr" element={<Page_OcrAccueil />} />
        <Route path="ocr/traitement" element={<Page_OcrTraitement />} />
        <Route path="ocr/historique" element={<Page_OcrHistorique />} />

        {/* Commandes & Produits */}
        <Route path="commandes" element={<Page_ListeCommandes />} />
        <Route path="produits" element={<Page_GestionProduits />} />
      </Route>
    </Routes>
  )
}