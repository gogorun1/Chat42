// import { useEffect, useState } from 'react'
// import { ApiError, sightingsApi, type SightingSearchItem, type Zone } from '../lib/api'

// export function SearchPage() {
//   const [zones, setZones] = useState<Zone[]>([])
//   const [zoneId, setZoneId] = useState<string>('')
//   const [dateFrom, setDateFrom] = useState('')
//   const [dateTo, setDateTo] = useState('')
//   const [page, setPage] = useState(1)
//   const pageSize = 12

//   const [items, setItems] = useState<SightingSearchItem[]>([])
//   const [total, setTotal] = useState(0)
//   const [loading, setLoading] = useState(true)
//   const [error, setError] = useState<string | null>(null)

//   // Per-card report state, keyed by sighting id.
//   const [reportingId, setReportingId] = useState<number | null>(null)
//   const [reason, setReason] = useState('')
//   const [reportError, setReportError] = useState<string | null>(null)
//   const [reportSubmitting, setReportSubmitting] = useState(false)
//   const [reportedIds, setReportedIds] = useState<Set<number>>(new Set())

//   useEffect(() => {
//     sightingsApi.zones().then(setZones).catch(() => setZones([]))
//   }, [])

//   useEffect(() => {
//     setLoading(true)
//     setError(null)

//     sightingsApi
//       .search({
//         zone_id: zoneId ? Number(zoneId) : undefined,
//         date_from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
//         date_to: dateTo ? new Date(dateTo).toISOString() : undefined,
//         page,
//         page_size: pageSize,
//       })
//       .then((res) => {
//         setItems(res.items)
//         setTotal(res.total)
//       })
//       .catch((err) => setError(err instanceof Error ? err.message : 'Search failed'))
//       .finally(() => setLoading(false))
//   }, [zoneId, dateFrom, dateTo, page])

//   function updateFilter(setter: (v: string) => void, value: string) {
//     setter(value)
//     setPage(1)
//   }

//   function openReportForm(sightingId: number) {
//     setReportingId(sightingId)
//     setReason('')
//     setReportError(null)
//   }

//   function closeReportForm() {
//     setReportingId(null)
//     setReason('')
//     setReportError(null)
//   }

//   async function submitReport(sightingId: number) {
//     if (reason.trim().length < 5) {
//       setReportError('Please give a reason (at least 5 characters).')
//       return
//     }

//     setReportSubmitting(true)
//     setReportError(null)

//     try {
//       await sightingsApi.requestDeletion(sightingId, reason.trim())
//       setReportedIds((prev) => new Set(prev).add(sightingId))
//       setReportingId(null)
//       setReason('')
//     } catch (err) {
//       if (err instanceof ApiError && err.status === 409) {
//         setReportError('You already have a pending request for this sighting.')
//       } else {
//         setReportError(err instanceof Error ? err.message : 'Could not submit request')
//       }
//     } finally {
//       setReportSubmitting(false)
//     }
//   }

//   const totalPages = Math.max(1, Math.ceil(total / pageSize))

//   return (
//     <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-8">
//       <h1 className="text-2xl font-semibold mb-6">Sighting Search</h1>

//       <div className="flex flex-wrap gap-3 mb-6">
//         <select
//           className="bg-slate-900 border border-slate-700 rounded px-3 py-2"
//           value={zoneId}
//           onChange={(e) => updateFilter(setZoneId, e.target.value)}
//         >
//           <option value="">All zones</option>
//           {zones.map((z) => (
//             <option key={z.id} value={z.id}>
//               {z.name}
//             </option>
//           ))}
//         </select>

//         <input
//           type="date"
//           className="bg-white text-slate-900 border border-slate-300 rounded px-3 py-2 [color-scheme:light]"
//           value={dateFrom}
//           onChange={(e) => updateFilter(setDateFrom, e.target.value)}
//         />
//         <span className="self-center text-slate-500">to</span>
//         <input
//           type="date"
//           className="bg-white text-slate-900 border border-slate-300 rounded px-3 py-2 [color-scheme:light]"
//           value={dateTo}
//           onChange={(e) => updateFilter(setDateTo, e.target.value)}
//         />
//       </div>

//       {error && <p className="text-red-400 mb-4">{error}</p>}
//       {loading && <p className="text-slate-400">Loading…</p>}

//       {!loading && !error && (
//         <>
//           <p className="text-slate-400 mb-4">
//             {total} sighting{total === 1 ? '' : 's'} found
//           </p>

//           <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
//             {items.map((s) => (
//               <div key={s.id} className="bg-slate-900 rounded-lg overflow-hidden border border-slate-800">
//                 <img src={s.image_url} alt={`Cat sighting in ${s.zone_name}`} className="w-full h-32 object-cover" />
//                 <div className="p-2 text-sm">
//                   <p className="font-medium">{s.zone_name}</p>
//                   <p className="text-slate-500">{new Date(s.created_at).toLocaleString()}</p>

//                   {reportedIds.has(s.id) ? (
//                     <p className="mt-2 text-xs text-emerald-400">Request submitted</p>
//                   ) : reportingId === s.id ? (
//                     <div className="mt-2 space-y-2">
//                       <textarea
//                         value={reason}
//                         onChange={(e) => setReason(e.target.value)}
//                         placeholder="Why should this be removed?"
//                         rows={2}
//                         className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-100"
//                         autoFocus
//                       />
//                       {reportError && <p className="text-xs text-red-400">{reportError}</p>}
//                       <div className="flex gap-2">
//                         <button
//                           onClick={() => submitReport(s.id)}
//                           disabled={reportSubmitting}
//                           className="flex-1 rounded bg-red-900/60 px-2 py-1 text-xs text-red-200 hover:bg-red-900 disabled:opacity-40"
//                         >
//                           {reportSubmitting ? 'Submitting…' : 'Submit'}
//                         </button>
//                         <button
//                           onClick={closeReportForm}
//                           className="rounded border border-slate-700 px-2 py-1 text-xs text-slate-400 hover:bg-slate-800"
//                         >
//                           Cancel
//                         </button>
//                       </div>
//                     </div>
//                   ) : (
//                     <button
//                       onClick={() => openReportForm(s.id)}
//                       className="mt-2 text-xs text-slate-500 hover:text-red-400"
//                     >
//                       Report
//                     </button>
//                   )}
//                 </div>
//               </div>
//             ))}
//           </div>

//           {items.length === 0 && <p className="text-slate-500">No sightings match these filters.</p>}

//           <div className="flex items-center gap-3 mt-6">
//             <button
//               disabled={page <= 1}
//               onClick={() => setPage((p) => p - 1)}
//               className="px-3 py-1 rounded bg-slate-800 disabled:opacity-40"
//             >
//               Prev
//             </button>
//             <span className="text-slate-400">
//               Page {page} of {totalPages}
//             </span>
//             <button
//               disabled={page >= totalPages}
//               onClick={() => setPage((p) => p + 1)}
//               className="px-3 py-1 rounded bg-slate-800 disabled:opacity-40"
//             >
//               Next
//             </button>
//           </div>
//         </>
//       )}
//     </div>
//   )
// }

import { useEffect, useState } from 'react'
import { sightingsApi, type SightingSearchItem, type Zone } from '../lib/api'
import { useAuth, type UserRole } from '../context/AuthContext' // adjust path if AuthContext lives elsewhere

export function SearchPage() {
  const { user: currentUser } = useAuth()

  const [zones, setZones] = useState<Zone[]>([])
  const [zoneId, setZoneId] = useState<string>('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 12

  const [items, setItems] = useState<SightingSearchItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Per-card moderator "remove" state, keyed by sighting id.
  const [removingId, setRemovingId] = useState<number | null>(null)

  useEffect(() => {
    sightingsApi.zones().then(setZones).catch(() => setZones([]))
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)

    sightingsApi
      .search({
        zone_id: zoneId ? Number(zoneId) : undefined,
        date_from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
        date_to: dateTo ? new Date(dateTo).toISOString() : undefined,
        page,
        page_size: pageSize,
      })
      .then((res) => {
        setItems(res.items)
        setTotal(res.total)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Search failed'))
      .finally(() => setLoading(false))
  }, [zoneId, dateFrom, dateTo, page])

  function updateFilter(setter: (v: string) => void, value: string) {
    setter(value)
    setPage(1)
  }

  function canModerate(role: UserRole | undefined) {
    return role === 'moderator' || role === 'admin'
  }

  async function removeSighting(sightingId: number) {
    if (!confirm('Remove this sighting? The uploader will be notified.')) return

    setRemovingId(sightingId)
    try {
      await sightingsApi.deleteSighting(sightingId)
      setItems((prev) => prev.filter((s) => s.id !== sightingId))
      setTotal((prev) => prev - 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not remove sighting')
    } finally {
      setRemovingId(null)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-8">
      <h1 className="text-2xl font-semibold mb-6">Sighting Search</h1>

      <div className="flex flex-wrap gap-3 mb-6">
        <select
          className="bg-slate-900 border border-slate-700 rounded px-3 py-2"
          value={zoneId}
          onChange={(e) => updateFilter(setZoneId, e.target.value)}
        >
          <option value="">All zones</option>
          {zones.map((z) => (
            <option key={z.id} value={z.id}>
              {z.name}
            </option>
          ))}
        </select>

        <input
          type="date"
          className="bg-white text-slate-900 border border-slate-300 rounded px-3 py-2 [color-scheme:light]"
          value={dateFrom}
          onChange={(e) => updateFilter(setDateFrom, e.target.value)}
        />
        <span className="self-center text-slate-500">to</span>
        <input
          type="date"
          className="bg-white text-slate-900 border border-slate-300 rounded px-3 py-2 [color-scheme:light]"
          value={dateTo}
          onChange={(e) => updateFilter(setDateTo, e.target.value)}
        />
      </div>

      {error && <p className="text-red-400 mb-4">{error}</p>}
      {loading && <p className="text-slate-400">Loading…</p>}

      {!loading && !error && (
        <>
          <p className="text-slate-400 mb-4">
            {total} sighting{total === 1 ? '' : 's'} found
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {items.map((s) => (
              <div key={s.id} className="bg-slate-900 rounded-lg overflow-hidden border border-slate-800">
                <img src={s.image_url} alt={`Cat sighting in ${s.zone_name}`} className="w-full h-32 object-cover" />
                <div className="p-2 text-sm">
                  <p className="font-medium">{s.zone_name}</p>
                  <p className="text-slate-500">{new Date(s.created_at).toLocaleString()}</p>

                  {canModerate(currentUser?.role) && (
                    <button
                      onClick={() => removeSighting(s.id)}
                      disabled={removingId === s.id}
                      className="mt-2 text-xs text-red-500 hover:text-red-400 disabled:opacity-40"
                    >
                      {removingId === s.id ? 'Removing…' : 'Remove'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {items.length === 0 && <p className="text-slate-500">No sightings match these filters.</p>}

          <div className="flex items-center gap-3 mt-6">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1 rounded bg-slate-800 disabled:opacity-40"
            >
              Prev
            </button>
            <span className="text-slate-400">
              Page {page} of {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1 rounded bg-slate-800 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}