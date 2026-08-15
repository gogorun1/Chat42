import { useCallback, useEffect, useRef, useState } from 'react'
import {
  analyticsApi,
  sightingsApi,
  type AnalyticsSummary,
  type Zone,
} from '../lib/api'
import { useSightingSocket } from '../lib/useSightingSocket'
import { BarChart } from '../components/charts/BarChart'
import { LineChart } from '../components/charts/LineChart'
import { PieChart } from '../components/charts/PieChart'
import { downloadCsv, exportToPdf } from '../lib/exportHelpers'

const QUICK_RANGES = [
  { label: '7 days', days: 7 },
  { label: '30 days', days: 30 },
  { label: '90 days', days: 90 },
]

function KpiCard({
  label,
  value,
  detail,
}: {
  label: string
  value: string | number
  detail?: string
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 print:border-slate-300 print:bg-white">
      <p className="text-sm text-slate-400 print:text-slate-600">{label}</p>
      <p className="mt-1 text-3xl font-semibold">{value}</p>
      {detail && (
        <p className="mt-1 text-xs text-slate-500 print:text-slate-600">
          {detail}
        </p>
      )}
    </div>
  )
}

export function AnalyticsPage() {
  const dashboardRef = useRef<HTMLDivElement>(null)

  const [zones, setZones] = useState<Zone[]>([])
  const [zoneId, setZoneId] = useState('')
  const [days, setDays] = useState(30)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const [data, setData] = useState<AnalyticsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    sightingsApi
      .zones()
      .then((result) =>
        setZones(
          [...result].sort((a, b) => a.name.localeCompare(b.name)),
        ),
      )
      .catch(() => setZones([]))
  }, [])

  const fetchSummary = useCallback(() => {
    setError(null)
    setUpdating(true)

    analyticsApi
      .summary({
        days: dateFrom || dateTo ? undefined : days,
        date_from: dateFrom ? `${dateFrom}T00:00:00Z` : undefined,
        date_to: dateTo ? `${dateTo}T23:59:59Z` : undefined,
        zone_id: zoneId ? Number(zoneId) : undefined,
      })
      .then(setData)
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : 'Failed to load analytics',
        ),
      )
      .finally(() => {
        setLoading(false)
        setUpdating(false)
      })
  }, [days, dateFrom, dateTo, zoneId])

  useEffect(() => {
    setLoading(true)
    fetchSummary()
  }, [fetchSummary])

  const handleSocketMessage = useCallback(() => {
    fetchSummary()
  }, [fetchSummary])

  useSightingSocket(handleSocketMessage)

  function selectQuickRange(d: number) {
    setDays(d)
    setDateFrom('')
    setDateTo('')
  }

  function handleZoneChange(value: string) {
    setZoneId(value)
  }

  function handleZoneChartClick(label: string) {
    const clickedZone = zones.find((zone) => zone.name === label)

    if (!clickedZone) return

    setZoneId((current) =>
      current === String(clickedZone.id) ? '' : String(clickedZone.id),
    )
  }

  function handleExportCsv() {
    if (!data) return

    downloadCsv(`analytics-${data.window_start}.csv`, [
      ...data.zone_activity.map((z) => ({
        section: 'zone_activity',
        zone_id: z.zone_id,
        zone_name: z.zone_name,
        count: z.count,
      })),
      ...data.daily_trend.map((d) => ({
        section: 'daily_trend',
        date: d.date,
        count: d.count,
      })),
      ...data.top_reporters.map((r) => ({
        section: 'top_reporters',
        user_id: r.user_id,
        email: r.email,
        count: r.count,
      })),
    ])
  }

  async function handleExportPdf() {
    if (!dashboardRef.current || !data) return

    setExporting(true)

    try {
      await exportToPdf(
        dashboardRef.current,
        `analytics-${data.window_start}.pdf`,
      )
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to export PDF',
      )
    } finally {
      setExporting(false)
    }
  }

  const selectedZone = zones.find((z) => String(z.id) === zoneId)

  const sortedZoneActivity = data
    ? [...data.zone_activity].sort(
        (a, b) =>
          b.count - a.count || a.zone_name.localeCompare(b.zone_name),
      )
    : []

  const topZone = sortedZoneActivity[0]
  const topReporter = data?.top_reporters[0]

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100 print:bg-white print:text-black">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-2xl font-semibold">Analytics</h1>
          {updating && (
            <p className="mt-1 text-xs text-emerald-400">Updating…</p>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {QUICK_RANGES.map((range) => (
            <button
              key={range.days}
              onClick={() => selectQuickRange(range.days)}
              className={`rounded border px-3 py-1.5 text-sm ${
                !dateFrom &&
                !dateTo &&
                days === range.days
                  ? 'border-emerald-500 bg-emerald-500/10 text-emerald-300'
                  : 'border-slate-700 bg-slate-900 text-slate-300'
              }`}
            >
              {range.label}
            </button>
          ))}

          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-white [color-scheme:dark]"
          />

          <span className="self-center text-sm text-slate-500">to</span>

          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-white [color-scheme:dark]"

          />

          <select
            value={zoneId}
            onChange={(e) => handleZoneChange(e.target.value)}
            className="rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm"
          >
            <option value="">All zones</option>
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.name}
              </option>
            ))}
          </select>

          <button
            onClick={handleExportCsv}
            disabled={!data}
            className="rounded border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40"
          >
            Export CSV
          </button>

          <button
            onClick={handleExportPdf}
            disabled={!data || exporting}
            className="rounded border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40"
          >
            {exporting ? 'Creating PDF…' : 'Export PDF'}
          </button>
        </div>
      </div>

      {error && <p className="mb-4 text-red-400 print:hidden">{error}</p>}

      {loading && !data && (
        <p className="text-slate-400 print:hidden">Loading…</p>
      )}

      {data && (
        <div
          ref={dashboardRef}
          className="space-y-6 bg-slate-950 print:bg-white"
        >
          <div className="hidden print:block">
            <h1 className="mb-1 text-2xl font-semibold text-black">
              Analytics
            </h1>
            <p className="mb-5 text-sm text-slate-600">
              {data.window_start} → {data.window_end ?? 'now'}
              {selectedZone ? ` · ${selectedZone.name}` : ''}
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              label="All-time sightings"
              value={data.total_sightings}
              detail="All recorded sightings"
            />

            <KpiCard
              label="Selected period"
              value={data.period_sightings}
              detail={`${data.window_start} → ${
                data.window_end ?? 'now'
              }`}
            />

            <KpiCard
              label="Most active zone"
              value={topZone?.zone_name ?? '—'}
              detail={
                topZone
                  ? `${topZone.count} sightings`
                  : 'No sightings'
              }
            />

            <KpiCard
              label="Top reporter"
              value={topReporter?.email ?? '—'}
              detail={
                topReporter
                  ? `${topReporter.count} sightings`
                  : 'No sightings'
              }
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 print:border-slate-300 print:bg-white">
              <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                  <h2 className="font-medium">Zone activity</h2>
                  <p className="mt-1 text-xs text-slate-500">
                    Click a zone to filter the dashboard.
                  </p>
                </div>

                {selectedZone && (
                  <button
                    type="button"
                    onClick={() => setZoneId('')}
                    className="rounded border border-slate-700 px-2 py-1 text-xs text-slate-400 hover:bg-slate-800"
                  >
                    Clear filter
                  </button>
                )}
              </div>

              <BarChart
                data={sortedZoneActivity.map((z) => ({
                  label: z.zone_name,
                  value: z.count,
                }))}
                selectedLabel={selectedZone?.name}
                onBarClick={handleZoneChartClick}
              />
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 print:border-slate-300 print:bg-white">
              <h2 className="mb-4 font-medium">Zone distribution</h2>

              <PieChart
                data={sortedZoneActivity.map((z) => ({
                  label: z.zone_name,
                  value: z.count,
                }))}
              />
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 print:border-slate-300 print:bg-white lg:col-span-2">
              <h2 className="mb-4 font-medium">Daily trend</h2>

              <LineChart
                data={data.daily_trend.map((d) => ({
                  label: d.date,
                  value: d.count,
                }))}
              />
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 print:border-slate-300 print:bg-white lg:col-span-2">
              <h2 className="mb-4 font-medium">Top reporters</h2>

              {data.top_reporters.length === 0 ? (
                <p className="text-sm text-slate-500">No sightings yet.</p>
              ) : (
                <ol className="space-y-1">
                  {data.top_reporters.map((reporter, index) => (
                    <li
                      key={reporter.user_id}
                      className="flex justify-between border-b border-slate-800 py-2 text-sm last:border-0 print:border-slate-300"
                    >
                      <span>
                        <span className="mr-2 text-slate-500">
                          #{index + 1}
                        </span>
                        {reporter.email}
                      </span>

                      <span className="text-slate-400">
                        {reporter.count} sightings
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
