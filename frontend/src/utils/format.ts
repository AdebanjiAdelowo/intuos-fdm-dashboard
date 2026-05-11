export function flightDuration(stickOn: string, stickOff: string): string {
  const start = new Date(stickOn)
  const end = new Date(stickOff)
  const ms = end.getTime() - start.getTime()
  if (isNaN(ms) || ms < 0) return '—'
  const h = Math.floor(ms / 3600000)
  const m = Math.floor((ms % 3600000) / 60000)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export function formatDate(dt: string): string {
  const d = new Date(dt)
  if (isNaN(d.getTime())) return dt
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function formatTime(dt: string): string {
  const d = new Date(dt)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

export function formatDateTime(dt: string): string {
  const d = new Date(dt)
  if (isNaN(d.getTime())) return dt
  return (
    d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) +
    ' · ' +
    d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  )
}
