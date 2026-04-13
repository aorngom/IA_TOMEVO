import { Outlet } from 'react-router-dom'
import Comp_BarreNavigation from '../components/client/Comp_BarreNavigation'
import Comp_PiedPage from '../components/client/Comp_PiedPage'

export default function Layout_Client() {
  return (
    <div className="d-flex flex-column min-vh-100">
      <Comp_BarreNavigation />
      <main className="flex-grow-1">
        <Outlet />
      </main>
      <Comp_PiedPage />
    </div>
  )
}