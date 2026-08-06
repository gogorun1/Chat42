import { useAuth } from '../context/AuthContext'
import CampusMap from "../components/42map";


export function HomePage() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">

      {/* Header */}
      <div className="mb-8 flex items-center justify-between">

        <div>
          <h1 className="text-4xl font-bold text-amber-400">
            🐱 Chat42
          </h1>

          <p className="mt-2 text-slate-400">
            Where is Moulinette today?
          </p>
        </div>

        <div className="text-right">

          <p className="text-sm text-slate-400">
            Logged in as
          </p>

          <p className="font-semibold">
            {user?.email}
          </p>

          <button
            onClick={logout}
            className="mt-3 rounded-md border border-slate-700 px-4 py-2 hover:bg-slate-800"
          >
            Log out
          </button>

        </div>

      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">

        {/* Map */}
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-lg">

          <h2 className="mb-4 text-xl font-semibold text-amber-400">
            🗺 Campus Map
          </h2>

          <CampusMap />

        </div>

        {/* Last Seen */}
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-lg">

          <h2 className="mb-4 text-xl font-semibold text-amber-400">
            📍 Last Seen
          </h2>

          <div className="space-y-3">

            <div>
              <p className="text-sm text-slate-400">Zone</p>
              <p>Floor 0</p>
            </div>

            <div>
              <p className="text-sm text-slate-400">Reporter</p>
              <p>Alice</p>
            </div>

            <div>
              <p className="text-sm text-slate-400">Time</p>
              <p>18:45</p>
            </div>

          </div>

        </div>

      </div>

      {/* Quick Actions */}
      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">

        <button className="rounded-lg bg-slate-900 p-4 transition hover:bg-slate-800">
          📖
          <br />
          Diary
        </button>

        <button className="rounded-lg bg-slate-900 p-4 transition hover:bg-slate-800">
          🎯
          <br />
          Guess
        </button>

        <button className="rounded-lg bg-slate-900 p-4 transition hover:bg-slate-800">
          🐾
          <br />
          History
        </button>

        <button className="rounded-lg bg-slate-900 p-4 transition hover:bg-slate-800">
          🔥
          <br />
          Heat Map
        </button>

        <button className="rounded-lg bg-slate-900 p-4 transition hover:bg-slate-800">
          🏆
          <br />
          Ranking
        </button>

        <button className="rounded-lg bg-amber-500 p-4 font-semibold text-black transition hover:bg-amber-400">
          ➕
          <br />
          Report
        </button>

      </div>

    </div>
  );
}