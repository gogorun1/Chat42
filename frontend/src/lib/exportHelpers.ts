import jsPDF from 'jspdf'
import html2canvas from 'html2canvas-pro'

type Row = Record<string, unknown>

function escapeCsv(value: unknown): string {
  const text = value == null ? '' : String(value)
  return `"${text.replace(/"/g, '""')}"`
}

export function downloadCsv(filename: string, rows: Row[]) {
  if (rows.length === 0) return

  const headers = Object.keys(rows[0])
  const csv = [
    headers.map(escapeCsv).join(','),
    ...rows.map((row) => headers.map((header) => escapeCsv(row[header])).join(',')),
  ].join('\r\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function waitForImages(element: HTMLElement): Promise<void> {
  const images = Array.from(element.querySelectorAll('img'))

  if (images.length === 0) return Promise.resolve()

  return Promise.all(
    images.map(
      (image) =>
        new Promise<void>((resolve) => {
          if (image.complete) {
            resolve()
            return
          }

          image.addEventListener('load', () => resolve(), { once: true })
          image.addEventListener('error', () => resolve(), { once: true })
        }),
    ),
  ).then(() => undefined)
}

function waitForRender(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve())
    })
  })
}

export async function exportToPdf(element: HTMLElement | null, filename = 'analytics.pdf') {
  if (!element) return

  const previousOverflow = document.body.style.overflow
  const previousElementWidth = element.style.width

  try {
    // Give Plotly a chance to finish its responsive resize before capture.
    await waitForRender()
    await waitForImages(element)
    await waitForRender()

    // Capture the dashboard at a stable desktop width. This avoids exporting
    // the narrow/mobile layout when the browser window is small.
    const captureWidth = Math.max(element.scrollWidth, 1100)
    element.style.width = `${captureWidth}px`
    document.body.style.overflow = 'hidden'

    await waitForRender()

    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      allowTaint: false,
      backgroundColor: '#ffffff',
      logging: false,
      imageTimeout: 15000,
      windowWidth: captureWidth,
      scrollX: 0,
      scrollY: 0,
    })

    if (canvas.width === 0 || canvas.height === 0) {
      throw new Error('Could not render the analytics dashboard for PDF export.')
    }

    // A4 in points. Use a fixed page size and split a tall dashboard over
    // multiple pages instead of creating an impractically large PDF page.
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'pt',
      format: 'a4',
      compress: true,
    })

    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const margin = 24
    const contentWidth = pageWidth - margin * 2
    const contentHeight = pageHeight - margin * 2
    const pxPerPoint = canvas.width / contentWidth
    const pageSourceHeight = Math.floor(contentHeight * pxPerPoint)

    let sourceY = 0
    let page = 0

    while (sourceY < canvas.height) {
      const sourceHeight = Math.min(pageSourceHeight, canvas.height - sourceY)

      const pageCanvas = document.createElement('canvas')
      pageCanvas.width = canvas.width
      pageCanvas.height = sourceHeight

      const context = pageCanvas.getContext('2d')
      if (!context) {
        throw new Error('Could not prepare PDF page.')
      }

      context.fillStyle = '#ffffff'
      context.fillRect(0, 0, pageCanvas.width, pageCanvas.height)
      context.drawImage(canvas, 0, sourceY, canvas.width, sourceHeight, 0, 0, canvas.width, sourceHeight)

      const imageData = pageCanvas.toDataURL('image/png')
      const renderedHeight = sourceHeight / pxPerPoint

      if (page > 0) {
        pdf.addPage()
      }

      pdf.addImage(imageData, 'PNG', margin, margin, contentWidth, renderedHeight, undefined, 'FAST')

      sourceY += sourceHeight
      page += 1
    }

    pdf.save(filename)
  } finally {
    element.style.width = previousElementWidth
    document.body.style.overflow = previousOverflow
  }
}