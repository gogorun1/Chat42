import { Link, Outlet } from 'react-router-dom'

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
      <footer className="border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-500">
        <Link to="/privacy-policy" className="hover:text-slate-300 hover:underline">
          Privacy Policy
        </Link>
        <span className="mx-2">·</span>
        <Link to="/terms-of-service" className="hover:text-slate-300 hover:underline">
          Terms of Service
        </Link>
      </footer>
    </div>
  )
}
