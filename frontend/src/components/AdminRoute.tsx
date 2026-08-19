import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface AdminRouteProps {
  requiredRole?: 'admin'
}

export function AdminRoute({ requiredRole }: AdminRouteProps) {
  const { user } = useAuth()

  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate to="/" replace />
  }

  if (user?.role !== 'admin' && user?.role !== 'moderator') {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
