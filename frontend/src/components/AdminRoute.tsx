import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function AdminRoute() {
  const { user } = useAuth()

  if (user?.role !== 'admin' && user?.role !== 'moderator') {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
