import { Outlet } from 'react-router-dom'
import Comp_BarreLaterale from '../components/admin/Comp_BarreLaterale'
import Comp_EnTete from '../components/admin/Comp_EnTete'

export default function Layout_Admin() {
  return (
    <div className="d-flex min-vh-100 bg-light">
      <Comp_BarreLaterale />
      <div className="flex-grow-1 d-flex flex-column" style={{ marginLeft: '260px' }}>
        <Comp_EnTete />
        <main className="flex-grow-1 p-4">
          <Outlet />
        </main>
      </div>
    </div>
  )
}