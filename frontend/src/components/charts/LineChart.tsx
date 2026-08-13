import Plot from '../../lib/Plot'

type Point = { label: string; value: number }

export function LineChart({ data, height = 260 }: { data: Point[]; height?: number }) {
  if (data.length === 0) {
    return <p className="text-sm text-slate-500">No data in this range.</p>
  }

  return (
    <Plot
      data={[
        {
          x: data.map((d) => d.label),
          y: data.map((d) => d.value),
          type: 'scatter',
          mode: 'lines+markers',
          line: { color: '#34d399' },
          marker: { color: '#34d399', size: 6 },
          hovertemplate: '%{x}: %{y}<extra></extra>',
        },
      ]}
      layout={{
        height,
        margin: { l: 40, r: 10, t: 10, b: 40 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#cbd5e1' },
        xaxis: { gridcolor: '#1e293b' },
        yaxis: { gridcolor: '#1e293b', rangemode: 'tozero' },
      }}
      config={{ displayModeBar: 'hover', displaylogo: false, responsive: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
