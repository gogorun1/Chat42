import { FormEvent, useEffect, useState } from 'react'
import { api, ApiError, Zone } from '../lib/api'
import { useAuth, UserRole } from '../context/AuthContext'

type SightingSearchItem = {
  id: number
  zone_id: number
  zone_name: string
  reporter_id: number
  reporter_email: string
  image_url: string
  created_at: string
}

type SightingSearchResult = {
  items: SightingSearchItem[]
  total: number
  page: number
  page_size: number
}

type AdminUser = {
  id: number
  email: string
  ft_login: string | null
  role: UserRole
}

export function AdminPage() {
  const { user } = useAuth()

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-8 px-4 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Admin</h1>
        <p className="mt-1 text-sm text-slate-400">Zone maintenance and false-report moderation.</p>
      </div>

      <ZonesPanel />
      <SightingsPanel />
      {user?.role === 'admin' && <UsersPanel />}
    </div>
  )
}

function ZonesPanel() {
  const [zones, setZones] = useState<Zone[]>([])
  const [slug, setSlug] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function loadZones() {
    api.get<Zone[]>('/sightings/zones').then(setZones).catch(() => setError('Failed to load zones'))
  }

  useEffect(loadZones, [])

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await api.post('/admin/zones', { slug, name })
      setSlug('')
      setName('')
      loadZones()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create zone')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(zoneId: number) {
    setError(null)
    try {
      await api.del(`/admin/zones/${zoneId}`)
      loadZones()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to delete zone')
    }
  }

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
      <h2 className="mb-4 text-lg font-semibold">Zones</h2>

      <form onSubmit={handleCreate} className="mb-4 flex flex-wrap gap-2">
        <input
          value={slug}
          onChange={(event) => setSlug(event.target.value)}
          placeholder="slug"
          className="w-32 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        />
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Zone name"
          className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={loading || !slug || !name}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          Add zone
        </button>
      </form>

      {error && <p className="mb-3 text-sm text-red-400">{error}</p>}

      <ul className="divide-y divide-slate-800">
        {zones.map((zone) => (
          <li key={zone.id} className="flex items-center justify-between py-2 text-sm">
            <span>
              {zone.name} <span className="text-slate-500">({zone.slug})</span>
            </span>
            <button
              onClick={() => handleDelete(zone.id)}
              className="text-red-400 hover:text-red-300"
            >
              Delete
            </button>
          </li>
        ))}
        {zones.length === 0 && <li className="py-2 text-sm text-slate-500">No zones yet.</li>}
      </ul>
    </section>
  )
}

function SightingsPanel() {
  const [result, setResult] = useState<SightingSearchResult | null>(null)
  const [zones, setZones] = useState<Zone[]>([])
  const [error, setError] = useState<string | null>(null)

  function loadSightings() {
    api
      .get<SightingSearchResult>('/search/sightings?page=1&page_size=20')
      .then(setResult)
      .catch(() => setError('Failed to load sightings'))
  }

  useEffect(() => {
    loadSightings()
    api.get<Zone[]>('/sightings/zones').then(setZones).catch(() => undefined)
  }, [])

  async function handleReassign(sightingId: number, zoneId: string) {
    setError(null)
    try {
      await api.patch(`/admin/sightings/${sightingId}`, { zone_id: Number(zoneId) })
      loadSightings()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to reassign zone')
    }
  }

  async function handleDelete(sightingId: number) {
    setError(null)
    try {
      await api.del(`/admin/sightings/${sightingId}`)
      loadSightings()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to delete sighting')
    }
  }

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
      <h2 className="mb-4 text-lg font-semibold">Sightings</h2>

      {error && <p className="mb-3 text-sm text-red-400">{error}</p>}

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-500">
            <tr>
              <th className="pb-2 pr-4">Reporter</th>
              <th className="pb-2 pr-4">Zone</th>
              <th className="pb-2 pr-4">Reported</th>
              <th className="pb-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {result?.items.map((sighting) => (
              <tr key={sighting.id}>
                <td className="py-2 pr-4">{sighting.reporter_email}</td>
                <td className="py-2 pr-4">
                  <select
                    value={sighting.zone_id}
                    onChange={(event) => handleReassign(sighting.id, event.target.value)}
                    className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
                  >
                    {zones.map((zone) => (
                      <option key={zone.id} value={zone.id}>
                        {zone.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="py-2 pr-4 text-slate-400">
                  {new Date(sighting.created_at).toLocaleString()}
                </td>
                <td className="py-2">
                  <button
                    onClick={() => handleDelete(sighting.id)}
                    className="text-red-400 hover:text-red-300"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {result && result.items.length === 0 && (
              <tr>
                <td colSpan={4} className="py-4 text-center text-slate-500">
                  No sightings yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function UsersPanel() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [error, setError] = useState<string | null>(null)

  function loadUsers() {
    api.get<AdminUser[]>('/admin/users').then(setUsers).catch(() => setError('Failed to load users'))
  }

  useEffect(loadUsers, [])

  async function handleRoleChange(userId: number, role: string) {
    setError(null)
    try {
      await api.patch(`/admin/users/${userId}/role`, { role })
      loadUsers()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to change role')
    }
  }

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
      <h2 className="mb-4 text-lg font-semibold">Users</h2>

      {error && <p className="mb-3 text-sm text-red-400">{error}</p>}

      <ul className="divide-y divide-slate-800">
        {users.map((u) => {
          const isSelf = u.id === currentUser?.id
          return (
            <li key={u.id} className="flex items-center justify-between py-2 text-sm">
              <span>
                {u.email}
                {isSelf && <span className="ml-2 text-slate-500">(you)</span>}
              </span>
              <select
                value={u.role}
                disabled={isSelf}
                title={isSelf ? "You can't change your own role" : undefined}
                onChange={(event) => handleRoleChange(u.id, event.target.value)}
                className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="user">user</option>
                <option value="moderator">moderator</option>
                <option value="admin">admin</option>
              </select>
            </li>
          )
        })}
        {users.length === 0 && <li className="py-2 text-sm text-slate-500">No users yet.</li>}
      </ul>
    </section>
  )
}
