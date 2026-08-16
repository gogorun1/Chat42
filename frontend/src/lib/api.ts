export const API_BASE_URL = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  const isFormData = options.body instanceof FormData
  if (!isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers,
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      // response had no JSON body; fall back to statusText
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body !== undefined ? JSON.stringify(body) : undefined }),
  postForm: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: 'POST', body: formData }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body !== undefined ? JSON.stringify(body) : undefined }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

export type Zone = {
  id: number
  slug: string
  name: string
}

export type Sighting = {
  id: number
  zone_id: number
  image_url: string
  created_at: string
  zone: Zone
}

export type SearchSighting = {
  id: number
  zone_id: number
  zone_name: string
  reporter_id: number
  reporter_email: string
  image_url: string
  created_at: string
}

export type SightingSearchResult = {
  items: SearchSighting[]
  total: number
  page: number
  page_size: number
}

export type Diary = {
  date: string
  content: string
}

export type Badge = {
  code: string
  name: string
  description: string
  awarded_at: string
}

export type LeaderboardEntry = {
  user_id: number
  display_name: string | null
  avatar_url: string | null
  sighting_count: number
  guess_points: number
  score: number
}

export type GuessResult = {
  correct: boolean
  guess_points: number
  actual_zone_id: number
}

export type ZoneActivity = {
  zone_id: number
  zone_name: string
  count: number
}

export type DailyTrend = {
  date: string // "YYYY-MM-DD"
  count: number
}

export type TopReporter = {
  user_id: number
  email: string
  display_name: string | null
  count: number
}

export type AnalyticsSummary = {
  total_sightings: number
  period_sightings: number
  window_start: string
  window_end: string | null
  zone_activity: ZoneActivity[]
  daily_trend: DailyTrend[]
  top_reporters: TopReporter[]
}

export type AnalyticsParams = {
  days?: number
  date_from?: string
  date_to?: string
  zone_id?: number
  reporter_limit?: number
}

// Small helper: builds a query string, skipping undefined/empty values so
// callers can pass a partial params object without manually filtering it.
function buildQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

export const sightingsApi = {
  zones: () => api.get<Zone[]>('/sightings/zones'),
}

export const analyticsApi = {
  summary: (params: AnalyticsParams = {}) =>
    api.get<AnalyticsSummary>(`/analytics/summary${buildQuery(params)}`),
}
