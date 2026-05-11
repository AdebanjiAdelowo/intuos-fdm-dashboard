import { useState } from 'react'

function defaultDates() {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  const fmt = (d: Date) => d.toISOString().split('T')[0]
  return { start: fmt(start), end: fmt(end) }
}

export function useDateRange() {
  const { start: defaultStart, end: defaultEnd } = defaultDates()
  const [startDate, setStartDate] = useState(defaultStart)
  const [endDate, setEndDate] = useState(defaultEnd)
  return { startDate, endDate, setStartDate, setEndDate }
}
