import { ChangeEvent, FormEvent, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, ApiError, Sighting } from '../lib/api'
import { useAuth } from '../context/AuthContext'

type PublicProfile = {
  id: number
  display_name: string | null
  avatar_url: string | null
  online: boolean
}

type FriendEntry = {
  friendship_id: number
  id: number
  display_name: string | null
  avatar_url: string | null
  online: boolean
}

type FriendList = {
  friends: FriendEntry[]
  pending_requests: FriendEntry[]
}

type UserSearchResult = {
  id: number
  email: string
  display_name: string | null
  avatar_url: string | null
}

export function ProfilePage() {
  const { id } = useParams()
  const { user: currentUser } = useAuth()

  const isOwnProfile = !id || Number(id) === currentUser?.id

  return isOwnProfile ? <OwnProfile /> : <OtherProfile userId={Number(id)} />
}

function Avatar({ url, size = 80 }: { url: string | null; size?: number }) {
  return url ? (
    <img
      src={url}
      alt="avatar"
      style={{ width: size, height: size }}
      className="rounded-full border border-slate-700 object-cover"
    />
  ) : (
    <div
      style={{ width: size, height: size }}
      className="flex items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-slate-500"
    >
      ?
    </div>
  )
}

function OwnProfile() {
  const { user, refreshUser } = useAuth()
  const [displayName, setDisplayName] = useState(user?.display_name ?? '')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [friendList, setFriendList] = useState<FriendList | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<UserSearchResult[] | null>(null)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [sentRequests, setSentRequests] = useState<Set<number>>(new Set())
  const [mySightings, setMySightings] = useState<Sighting[] | null>(null)

  function loadFriends() {
    api.get<FriendList>('/users/me/friends').then(setFriendList).catch(() => undefined)
  }

  useEffect(loadFriends, [])

  useEffect(() => {
    api.get<Sighting[]>('/sightings/').then(setMySightings).catch(() => undefined)
  }, [])

  async function handleSaveName(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await api.patch('/users/me', { display_name: displayName })
      await refreshUser()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  async function handleAvatarChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setError(null)
    const formData = new FormData()
    formData.append('avatar', file)
    try {
      await api.postForm('/users/me/avatar', formData)
      await refreshUser()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to upload avatar')
    }
  }

  async function handleAccept(friendshipId: number) {
    await api.post(`/users/me/friend-requests/${friendshipId}/accept`)
    loadFriends()
  }

  async function handleRemove(userId: number) {
    await api.del(`/users/${userId}/friend`)
    loadFriends()
  }

  async function handleSearch(event: FormEvent) {
    event.preventDefault()
    setSearchError(null)
    try {
      const results = await api.get<UserSearchResult[]>(`/users/search?q=${encodeURIComponent(searchQuery)}`)
      setSearchResults(results)
    } catch (err) {
      setSearchError(err instanceof ApiError ? err.message : 'Search failed')
    }
  }

  async function handleSendRequest(userId: number) {
    setSearchError(null)
    try {
      await api.post(`/users/${userId}/friend-request`)
      setSentRequests((prev) => new Set(prev).add(userId))
    } catch (err) {
      setSearchError(err instanceof ApiError ? err.message : 'Failed to send friend request')
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-8 px-4 py-10">
      <div>
        <h1 className="text-2xl font-semibold">Profile</h1>
        <p className="mt-1 text-sm text-slate-400">{user?.email}</p>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <section className="flex items-center gap-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
        <Avatar url={user?.avatar_url ?? null} />
        <div>
          <label className="block text-sm text-slate-400 mb-1">Change avatar</label>
          <input type="file" accept="image/*" onChange={handleAvatarChange} className="text-sm" />
        </div>
      </section>

      <form
        onSubmit={handleSaveName}
        className="flex flex-wrap items-end gap-2 rounded-xl border border-slate-800 bg-slate-900 p-6"
      >
        <div className="flex-1">
          <label className="block text-sm text-slate-400 mb-1">Display name</label>
          <input
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            placeholder="Your name"
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={saving || !displayName}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          Save
        </button>
      </form>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Find people</h2>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search by name or email"
            className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={!searchQuery.trim()}
            className="rounded-md bg-slate-700 px-4 py-2 text-sm font-medium hover:bg-slate-600 disabled:opacity-50"
          >
            Search
          </button>
        </form>
        {searchError && <p className="mt-2 text-sm text-red-400">{searchError}</p>}
        {searchResults && (
          <ul className="mt-4 divide-y divide-slate-800">
            {searchResults.map((result) => {
              const isFriend = friendList?.friends.some((f) => f.id === result.id)
              const incomingRequest = friendList?.pending_requests.find((f) => f.id === result.id)
              const alreadySent = sentRequests.has(result.id)
              return (
                <li key={result.id} className="flex items-center justify-between py-2 text-sm">
                  <span className="flex items-center gap-2">
                    <Avatar url={result.avatar_url} size={32} />
                    <span className="flex flex-col">
                      <span>{result.display_name ?? `User #${result.id}`}</span>
                      <span className="text-xs text-slate-500">{result.email}</span>
                    </span>
                  </span>
                  {isFriend ? (
                    <span className="text-xs text-slate-500">Already friends</span>
                  ) : incomingRequest ? (
                    <button
                      onClick={() => handleAccept(incomingRequest.friendship_id)}
                      className="rounded-md bg-emerald-600 px-3 py-1 text-xs font-medium hover:bg-emerald-500"
                    >
                      Accept
                    </button>
                  ) : alreadySent ? (
                    <span className="text-xs text-slate-500">Requested</span>
                  ) : (
                    <button
                      onClick={() => handleSendRequest(result.id)}
                      className="rounded-md bg-emerald-600 px-3 py-1 text-xs font-medium hover:bg-emerald-500"
                    >
                      Add friend
                    </button>
                  )}
                </li>
              )
            })}
            {searchResults.length === 0 && <li className="py-2 text-sm text-slate-500">No users found.</li>}
          </ul>
        )}
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Friend requests</h2>
        <ul className="divide-y divide-slate-800">
          {friendList?.pending_requests.map((entry) => (
            <li key={entry.friendship_id} className="flex items-center justify-between py-2 text-sm">
              <span className="flex items-center gap-2">
                <Avatar url={entry.avatar_url} size={32} />
                {entry.display_name ?? `User #${entry.id}`}
              </span>
              <button
                onClick={() => handleAccept(entry.friendship_id)}
                className="rounded-md bg-emerald-600 px-3 py-1 text-xs font-medium hover:bg-emerald-500"
              >
                Accept
              </button>
            </li>
          ))}
          {friendList && friendList.pending_requests.length === 0 && (
            <li className="py-2 text-sm text-slate-500">No pending requests.</li>
          )}
        </ul>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Friends</h2>
        <ul className="divide-y divide-slate-800">
          {friendList?.friends.map((entry) => (
            <li key={entry.friendship_id} className="flex items-center justify-between py-2 text-sm">
              <span className="flex items-center gap-2">
                <Avatar url={entry.avatar_url} size={32} />
                {entry.display_name ?? `User #${entry.id}`}
                <span className={entry.online ? 'text-emerald-400' : 'text-slate-600'}>●</span>
              </span>
              <button onClick={() => handleRemove(entry.id)} className="text-red-400 hover:text-red-300">
                Remove
              </button>
            </li>
          ))}
          {friendList && friendList.friends.length === 0 && (
            <li className="py-2 text-sm text-slate-500">No friends yet.</li>
          )}
        </ul>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">My sighting history</h2>
        <ul className="divide-y divide-slate-800">
          {mySightings?.map((sighting) => (
            <li key={sighting.id} className="flex items-center gap-3 py-2 text-sm">
              <img
                src={sighting.image_url}
                alt={`Cat spotted in ${sighting.zone.name}`}
                className="h-12 w-12 rounded-md border border-slate-700 object-cover"
              />
              <span className="flex flex-col">
                <span>{sighting.zone.name}</span>
                <span className="text-xs text-slate-500">
                  {new Date(sighting.created_at).toLocaleString()}
                </span>
              </span>
            </li>
          ))}
          {mySightings && mySightings.length === 0 && (
            <li className="py-2 text-sm text-slate-500">No sightings reported yet.</li>
          )}
        </ul>
      </section>
    </div>
  )
}

function OtherProfile({ userId }: { userId: number }) {
  const [profile, setProfile] = useState<PublicProfile | null>(null)
  const [friendList, setFriendList] = useState<FriendList | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  function load() {
    api
      .get<PublicProfile>(`/users/${userId}`)
      .then(setProfile)
      .catch(() => setError('Failed to load profile'))
    api.get<FriendList>('/users/me/friends').then(setFriendList).catch(() => undefined)
  }

  useEffect(load, [userId])

  const friendEntry = friendList?.friends.find((f) => f.id === userId)
  const pendingEntry = friendList?.pending_requests.find((f) => f.id === userId)

  async function handleAddFriend() {
    setActionError(null)
    try {
      await api.post(`/users/${userId}/friend-request`)
      load()
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'Failed to send friend request')
    }
  }

  async function handleAccept() {
    if (!pendingEntry) return
    await api.post(`/users/me/friend-requests/${pendingEntry.friendship_id}/accept`)
    load()
  }

  async function handleRemove() {
    await api.del(`/users/${userId}/friend`)
    load()
  }

  if (error) return <p className="p-10 text-sm text-red-400">{error}</p>
  if (!profile) return null

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-4 py-10">
      <section className="flex items-center gap-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
        <Avatar url={profile.avatar_url} />
        <div>
          <h1 className="text-xl font-semibold">{profile.display_name ?? `User #${profile.id}`}</h1>
          <p className={`text-sm ${profile.online ? 'text-emerald-400' : 'text-slate-500'}`}>
            {profile.online ? 'Online' : 'Offline'}
          </p>
        </div>
      </section>

      {actionError && <p className="text-sm text-red-400">{actionError}</p>}

      {friendEntry ? (
        <button
          onClick={handleRemove}
          className="self-start rounded-md border border-red-800 px-4 py-2 text-sm text-red-400 hover:bg-red-950"
        >
          Remove friend
        </button>
      ) : pendingEntry ? (
        <button
          onClick={handleAccept}
          className="self-start rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500"
        >
          Accept friend request
        </button>
      ) : (
        <button
          onClick={handleAddFriend}
          className="self-start rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500"
        >
          Add friend
        </button>
      )}
    </div>
  )
}
