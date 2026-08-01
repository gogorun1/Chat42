import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function HomePage() {
  const { user, logout } = useAuth()

  return (
    <div className="flex flex-1 items-center justify-center px-4 py-12">
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center shadow-lg">
        <h1 className="text-2xl font-semibold">Chat 42</h1>
        <p className="mt-2 text-sm text-slate-400">Logged in as {user?.email}</p>
        <Link
          to="/upload"
          className="mt-6 inline-block rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500"
        >
          Report a cat sighting
        </Link>
        <button
          onClick={logout}
          className="mt-4 block w-full rounded-md border border-slate-700 px-4 py-2 text-sm hover:bg-slate-800"
        >
          Log out
        </button>
      </div>
    </div>
  )
}
