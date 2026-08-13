import Plot from '../../lib/Plot'

type Slice = { label: string; value: number }

const COLORS = ['#38bdf8', '#34d399', '#fbbf24', '#f472b6', '#a78bfa', '#fb923c', '#4ade80', '#f87171']

export function PieChart({ data }: { data: Slice[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-slate-500">No data in this range.</p>
  }

  return (
    <Plot
      data={[
        {
          labels: data.map((d) => d.label),
          values: data.map((d) => d.value),
          type: 'pie',
          hole: 0.45,
          marker: { colors: COLORS },
          textinfo: 'percent',
          hovertemplate: '%{label}: %{value} (%{percent})<extra></extra>',
        },
      ]}
      layout={{
        height: 260,
        margin: { l: 10, r: 10, t: 10, b: 10 },
        paper_bgcolor: 'transparent',
        font: { color: '#cbd5e1' },
        showlegend: true,
        legend: { font: { color: '#cbd5e1' } },
      }}
      config={{ displayModeBar: 'hover', displaylogo: false, responsive: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
