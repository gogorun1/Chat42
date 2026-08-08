import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, Sighting, Zone } from '../lib/api'

export function UploadPage() {
  const [zones, setZones] = useState<Zone[]>([])
  const [zoneId, setZoneId] = useState('')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<Sighting | null>(null)

  useEffect(() => {
    api.get<Zone[]>('/sightings/zones').then(setZones).catch(() => setError('Failed to load map zones'))
  }, [])

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  function handleFileChange(file: File | null, options?: { clearSuccess?: boolean }) {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
    setSelectedFile(null)
    if (options?.clearSuccess !== false) setSuccess(null)
    setError(null)

    if (!file) return

    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!selectedFile || !zoneId) {
      setError('Choose a photo and a map zone before submitting.')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    const formData = new FormData()
    formData.append('zone_id', zoneId)
    formData.append('image', selectedFile)

    try {
      const sighting = await api.postForm<Sighting>('/sightings/', formData)
      setSuccess(sighting)
      handleFileChange(null, { clearSuccess: false })
      setZoneId('')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-lg flex-1 flex-col px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Report a cat sighting</h1>
          <p className="mt-1 text-sm text-slate-400">Upload a campus cat photo and tag the map zone.</p>
        </div>
        <Link to="/" className="text-sm text-slate-400 hover:text-slate-200">
          Back
        </Link>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border border-slate-800 bg-slate-900 p-6">
        <label className="block">
          <span className="mb-2 block text-sm font-medium">Photo</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            capture="environment"
            onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
            className="block w-full text-sm text-slate-300 file:mr-4 file:rounded-md file:border-0 file:bg-slate-700 file:px-4 file:py-2 file:text-sm file:text-slate-100 hover:file:bg-slate-600"
          />
        </label>

        {previewUrl && (
          <img src={previewUrl} alt="Preview" className="max-h-64 w-full rounded-lg object-cover" />
        )}

        <label className="block">
          <span className="mb-2 block text-sm font-medium">Map zone</span>
          <select
            value={zoneId}
            onChange={(event) => setZoneId(event.target.value)}
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          >
            <option value="">Select a zone</option>
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.name}
              </option>
            ))}
          </select>
        </label>

        {error && <p className="text-sm text-red-400">{error}</p>}

        {success && (
          <div className="rounded-md border border-emerald-800 bg-emerald-950/40 p-4 text-sm text-emerald-200">
            <p>Sighting saved in {success.zone.name}.</p>
            <img
              src={success.image_url}
              alt="Uploaded sighting"
              className="mt-3 max-h-48 w-full rounded-md object-cover"
            />
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          {loading ? 'Uploading…' : 'Submit sighting'}
        </button>
      </form>
    </div>
  )
}
