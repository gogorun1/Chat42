import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import CampusMap from "../components/42map";

export function HomePage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-8 text-white">
      <div className="mb-8 flex flex-col gap-4 rounded-xl border border-yellow-400 bg-slate-900 p-5 shadow-lg md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-yellow-400">🐱 Chat42</h1>
          <p className="mt-1 text-sm text-slate-400">Campus Cat Adventure</p>
        </div>

        <div className="flex items-center gap-5">
          <div className="text-right">
            <p className="text-sm text-slate-400">👤 {user?.email}</p>
            <p className="mt-1 font-bold text-yellow-400">⭐ 120 pts</p>
            <p className="text-sm text-slate-400">🏆 Rank #12</p>
          </div>

          <button
            onClick={logout}
            className="rounded-md border border-slate-700 px-4 py-2 text-sm transition hover:bg-slate-800"
          >
            Log out
          </button>
        </div>
      </div>

      <CampusMap />

      <Link
        to="/upload"
        className="mt-6 inline-block rounded-lg bg-amber-500 p-4 font-semibold text-black transition hover:bg-amber-400"
      >
        ➕ Report a cat sighting
      </Link>
    </div>
  );
}
