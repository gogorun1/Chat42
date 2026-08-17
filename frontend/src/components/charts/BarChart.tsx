import Plot from '../../lib/Plot'
import type { PlotMouseEvent } from 'plotly.js'

type Bar = { label: string; value: number }

type BarChartProps = {
  data: Bar[]
  selectedLabel?: string
  onBarClick?: (label: string) => void
}

export function BarChart({
  data,
  selectedLabel,
  onBarClick,
}: BarChartProps) {
  if (data.length === 0) {
    return <p className="text-sm text-slate-500">No data in this range.</p>
  }

  const sortedData = [...data].sort(
    (a, b) => b.value - a.value || a.label.localeCompare(b.label),
  )

  const labels = sortedData.map((d) => d.label)
  const values = sortedData.map((d) => d.value)

  return (
    <Plot
      data={[
        {
          x: values,
          y: labels,
          type: 'bar',
          orientation: 'h',
          marker: {
            color: sortedData.map((d) =>
              selectedLabel === d.label ? '#34d399' : '#38bdf8',
            ),
          },
          hovertemplate: '%{y}: %{x}<extra>Click to filter</extra>',
        },
      ]}
      layout={{
        height: Math.max(190, sortedData.length * 42 + 70),
        margin: { l: 135, r: 25, t: 10, b: 35 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#cbd5e1' },
        xaxis: {
          gridcolor: '#1e293b',
          fixedrange: false,
          rangemode: 'tozero',
          zeroline: false,
          domain: [0.12, 1],
        },
        yaxis: {
          autorange: 'reversed',
          automargin: true,
          tickfont: { size: 12 },
          ticklabelposition: 'outside',
        },
        hoverlabel: {
          bgcolor: '#0f172a',
          font: { color: '#f8fafc' },
        },
      }}
      config={{
        displayModeBar: 'hover',
        displaylogo: false,
        responsive: true,
      }}
      onClick={(event: Readonly<PlotMouseEvent>) => {
        const label = event.points?.[0]?.y
        if (label != null && onBarClick) {
          onBarClick(String(label))
        }
      }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
