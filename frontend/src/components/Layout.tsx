import { Link, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LiveToasts } from './LiveToasts'
import { NotificationBell } from './NotificationBell'

export function Layout() {
  const { user } = useAuth()

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
      {user && (
        <header className="border-b border-slate-800 px-6 py-3">
          <nav className="mx-auto flex max-w-5xl items-center gap-4 text-sm">
            <Link
              to="/"
              className="font-medium hover:text-emerald-400"
            >
              Chat 42
            </Link>
            <Link
              to="/search"
              className="text-slate-400 hover:text-slate-200"
            >
              Search
            </Link>

            <Link
              to="/profile"
              className="text-slate-400 hover:text-slate-200"
            >
              Profile
            </Link>

            {(user.role === 'moderator' || user.role === 'admin') && (
              <Link
                to="/admin"
                className="text-slate-400 hover:text-slate-200"
              >
                Admin
              </Link>
            )}

            {user.role === 'admin' && (
              <Link
                to="/analytics"
                className="text-slate-400 hover:text-slate-200"
              >
                Analytics
              </Link>
            )}
            {/* Pushes the bell to the far right of the nav row */}
            <div className="ml-auto flex items-center">
              <NotificationBell />
            </div>
          </nav>
        </header>
      )}
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>

      <footer className="border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-500">
        <Link
          to="/privacy-policy"
          className="hover:text-slate-300 hover:underline"
        >
          Privacy Policy
        </Link>

        <span className="mx-2">·</span>

        <Link
          to="/terms-of-service"
          className="hover:text-slate-300 hover:underline"
        >
          Terms of Service
        </Link>
      </footer>

      {user && <LiveToasts />}
    </div>
  )
}

