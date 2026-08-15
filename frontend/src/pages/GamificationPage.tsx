import { FormEvent, useEffect, useState } from 'react'
import { api, ApiError, Badge, LeaderboardEntry, Prediction, Zone } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export function GamificationPage() {
  const { user } = useAuth()
  const [badges, setBadges] = useState<Badge[] | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[] | null>(null)
  const [zones, setZones] = useState<Zone[]>([])
  const [predictions, setPredictions] = useState<Prediction[] | null>(null)
  const [guessZoneId, setGuessZoneId] = useState('')
  const [guessError, setGuessError] = useState<string | null>(null)
  const [guessSuccess, setGuessSuccess] = useState<string | null>(null)

  function loadGamificationData() {
    api.get<Badge[]>('/gamification/achievements').then(setBadges).catch(() => undefined)
    api.get<LeaderboardEntry[]>('/gamification/leaderboard').then(setLeaderboard).catch(() => undefined)
    api.get<Prediction[]>('/gamification/predictions/me').then(setPredictions).catch(() => undefined)
  }

  useEffect(() => {
    api.get<Zone[]>('/sightings/zones').then(setZones).catch(() => undefined)
    loadGamificationData()
  }, [])

  const hasPendingGuess = predictions?.some((prediction) => prediction.is_correct === null) ?? false

  async function handleSubmitGuess(event: FormEvent) {
    event.preventDefault()
    setGuessError(null)
    setGuessSuccess(null)
    if (!guessZoneId) return

    try {
      await api.post('/gamification/predictions', { zone_id: Number(guessZoneId) })
      setGuessSuccess('Guess submitted — check back after it resolves!')
      setGuessZoneId('')
      loadGamificationData()
    } catch (err) {
      setGuessError(err instanceof ApiError ? err.message : 'Failed to submit guess')
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-8 px-4 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Gamification</h1>
        <p className="mt-1 text-sm text-slate-400">Badges, leaderboard, and guess-the-cat-zone.</p>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Guess where the cat will be spotted most</h2>

        {hasPendingGuess ? (
          <p className="text-sm text-slate-400">
            You've already guessed for the next round. Check back once it resolves.
          </p>
        ) : (
          <form onSubmit={handleSubmitGuess} className="flex flex-wrap gap-2">
            <select
              value={guessZoneId}
              onChange={(event) => setGuessZoneId(event.target.value)}
              className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            >
              <option value="">Select a zone</option>
              {zones.map((zone) => (
                <option key={zone.id} value={zone.id}>
                  {zone.name}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={!guessZoneId}
              className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
            >
              Submit guess
            </button>
          </form>
        )}

        {guessError && <p className="mt-2 text-sm text-red-400">{guessError}</p>}
        {guessSuccess && <p className="mt-2 text-sm text-emerald-400">{guessSuccess}</p>}

        {predictions && predictions.length > 0 && (
          <ul className="mt-4 divide-y divide-slate-800 text-sm">
            {predictions.map((prediction) => {
              const zoneName = zones.find((zone) => zone.id === prediction.zone_id)?.name ?? `Zone #${prediction.zone_id}`
              return (
                <li key={prediction.id} className="flex items-center justify-between py-2">
                  <span>
                    {prediction.target_date} — {zoneName}
                  </span>
                  <span
                    className={
                      prediction.is_correct === true
                        ? 'text-emerald-400'
                        : prediction.is_correct === false
                          ? 'text-red-400'
                          : 'text-slate-500'
                    }
                  >
                    {prediction.is_correct === true ? 'Correct!' : prediction.is_correct === false ? 'Missed' : 'Pending'}
                  </span>
                </li>
              )
            })}
          </ul>
        )}
      </section>

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
