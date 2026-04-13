import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/Context_Auth'
import Routes_Client from './routes/Routes_Client'
import Routes_Admin from './routes/Routes_Admin'
import Page_Connexion from './pages/admin/auth/Page_Connexion'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Page de connexion */}
          <Route path="/connexion" element={<Page_Connexion />} />

          {/* Routes client */}
          <Route path="/*" element={<Routes_Client />} />

          {/* Routes admin */}
          <Route path="/admin/*" element={<Routes_Admin />} />

          {/* Redirection racine → connexion */}
          <Route path="/" element={<Navigate to="/connexion" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}