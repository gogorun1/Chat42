import { useEffect, useState } from 'react'
import { api, Badge, LeaderboardEntry } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export function GamificationPage() {
  const { user } = useAuth()
  const [badges, setBadges] = useState<Badge[] | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[] | null>(null)

  useEffect(() => {
    api.get<Badge[]>('/gamification/achievements').then(setBadges).catch(() => undefined)
    api.get<LeaderboardEntry[]>('/gamification/leaderboard').then(setLeaderboard).catch(() => undefined)
  }, [])

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-8 px-4 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Gamification</h1>
        <p className="mt-1 text-sm text-slate-400">
          Badges and leaderboard. Want to guess where the cat is? Head to the Campus Map.
        </p>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Your badges</h2>
        {badges && badges.length === 0 && (
          <p className="text-sm text-slate-500">No badges yet — go log a sighting!</p>
        )}
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {badges?.map((badge) => (
            <li key={badge.code} className="rounded-lg border border-slate-800 bg-slate-950 p-3 text-center">
              <p className="text-2xl">🏅</p>
              <p className="mt-1 text-sm font-medium">{badge.name}</p>
              <p className="mt-1 text-xs text-slate-500">{badge.description}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Leaderboard</h2>
        <ol className="divide-y divide-slate-800 text-sm">
          {leaderboard?.map((entry, index) => (
            <li
              key={entry.user_id}
              className={`flex items-center justify-between py-2 ${entry.user_id === user?.id ? 'text-emerald-400' : ''}`}
            >
              <span>
                #{index + 1} {entry.display_name ?? `User #${entry.user_id}`}
              </span>
              <span>{entry.score} pts</span>
            </li>
          ))}
          {leaderboard && leaderboard.length === 0 && (
            <li className="py-2 text-slate-500">No one on the board yet.</li>
          )}
        </ol>
      </section>
    </div>
  )
}
