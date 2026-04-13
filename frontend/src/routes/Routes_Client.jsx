import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '../context/Context_Auth'
import Layout_Client from '../layouts/Layout_Client'
import Page_Accueil from '../pages/client/Page_Accueil'
import Page_Presentation from '../pages/client/Page_Presentation'
import Page_NotreElevage from '../pages/client/Page_NotreElevage'
import Page_Boutique from '../pages/client/Page_Boutique'
import Page_Contact from '../pages/client/Page_Contact'
import Page_Panier from '../pages/client/Page_Panier'
import Page_Paiement from '../pages/client/Page_Paiement'
import Page_ConfirmationCommande from '../pages/client/Page_ConfirmationCommande'
import Page_DetailProduit from '../pages/client/Page_DetailProduit'

// Protège les routes client : redirige vers connexion si pas connecté
function RouteProtegeeClient({ children }) {
  const { utilisateur, chargement } = useAuth()
  if (chargement) return <div className="text-center mt-5">Chargement...</div>
  if (!utilisateur) return <Navigate to="/connexion" replace />
  if (utilisateur.role === 'admin' || utilisateur.role === 'rh')
    return <Navigate to="/admin" replace />
  return children
}

export default function Routes_Client() {
  return (
    <Routes>
      <Route path="/" element={
        <RouteProtegeeClient>
          <Layout_Client />
        </RouteProtegeeClient>
      }>
        <Route index element={<Page_Accueil />} />
        <Route path="presentation" element={<Page_Presentation />} />
        <Route path="notre-elevage" element={<Page_NotreElevage />} />
        <Route path="boutique" element={<Page_Boutique />} />
        <Route path="boutique/:id" element={<Page_DetailProduit />} />
        <Route path="panier" element={<Page_Panier />} />
        <Route path="paiement" element={<Page_Paiement />} />
        <Route path="confirmation" element={<Page_ConfirmationCommande />} />
        <Route path="contact" element={<Page_Contact />} />
      </Route>
    </Routes>
  )
}