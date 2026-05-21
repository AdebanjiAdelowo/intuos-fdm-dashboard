import { useEffect, useState, useCallback } from 'react'
import { ChevronLeft, ChevronRight, Users } from 'lucide-react'
import { Card, Title, Text, TextInput, Button } from '@tremor/react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import {
  searchPilots,
  getPilotAlarmsByDate,
  getPilotFlightsByDate,
  getPilotFlightsWithAlarms,
  getFlewHoursByPilot,
  Pilot,
} from '../api'
import DataTable from '../components/DataTable'
import DateRangePicker from '../components/DateRangePicker'
import LoadingSpinner from '../components/LoadingSpinner'
import StatCard from '../components/StatCard'
import { useDateRange } from '../hooks/useDateRange'

type Row = Record<string, unknown>

export default function PilotsPage() {
  const { startDate, endDate, setStartDate, setEndDate } = useDateRange()
  const [pilots, setPilots] = useState<Pilot[]>([])
  const [totalItems, setTotalItems] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [inputVal, setInputVal] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Pilot | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // Detail state
  const [flights, setFlights] = useState<Row[]>([])
  const [alarms, setAlarms] = useState<Row[]>([])
  const [flightsWithAlarms, setFlightsWithAlarms] = useState<number | null>(null)
  const [flewHours, setFlewHours] = useState<Row[]>([])

  const fetchPilots = useCallback(() => {
    setLoading(true)
    searchPilots(startDate, endDate, search, page, 20)
      .then((r) => {
        setPilots(Array.isArray(r.data) ? r.data : [])
        setTotalItems(r.pagination?.total_items ?? 0)
        setTotalPages(r.pagination?.total_pages ?? 1)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [startDate, endDate, search, page])

  useEffect(() => {
    fetchPilots()
  }, [fetchPilots])

  useEffect(() => {
    setPage(1)
  }, [startDate, endDate, search])

  useEffect(() => {
    if (!selected) return
    const id = String(selected.codcf ?? selected.id ?? selected.pilot_id ?? '')
    if (!id) return
    setDetailLoading(true)
    Promise.all([
      getPilotFlightsByDate(id, startDate, endDate),
      getPilotAlarmsByDate(id, startDate, endDate),
      getPilotFlightsWithAlarms(id, startDate, endDate),
      getFlewHoursByPilot(id, startDate, endDate),
    ])
      .then(([fl, al, fwa, fh]) => {
        const flData = Array.isArray(fl.data) ? fl.data : []
        setFlights(flData as Row[])
        setAlarms(Array.isArray(al.data) ? al.data as Row[] : [])
        const fwaVal = Array.isArray(fwa.data) ? fwa.data[0] : null
        setFlightsWithAlarms(typeof fwaVal === 'number' ? fwaVal : null)
        setFlewHours(Array.isArray(fh.data) ? fh.data as Row[] : [])
      })
      .catch(() => {})
      .finally(() => setDetailLoading(false))
  }, [selected, startDate, endDate])

  const alarmChartData = alarms
    .slice(0, 1)
    .flatMap((row) =>
      Object.entries(row)
        .filter(([k, v]) => k !== 'registration' && k !== 'total' && k !== 'pilot' && Number(v) > 0)
        .map(([k, v]) => ({ name: k, count: Number(v) }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 15)
    )

  if (selected) {
    const pilotId = String(selected.codcf ?? selected.id ?? selected.pilot_id ?? '?')
    const pilotName = String(selected.nome ?? selected.name ?? pilotId)
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <button
          onClick={() => setSelected(null)}
          className="flex items-center gap-1.5 text-sm font-medium mb-5 hover:opacity-70 transition-opacity"
          style={{ color: '#0d1f14' }}
        >
          <ChevronLeft className="w-4 h-4" /> Back to pilots
        </button>

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: '#0d1f14' }}>
              <Users className="w-5 h-5" style={{ color: '#b8f04a' }} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-tremor-content-strong">{pilotName}</h1>
              <Text className="mt-0.5">Pilot detail · ID {pilotId}</Text>
            </div>
          </div>
          <DateRangePicker
            startDate={startDate}
            endDate={endDate}
            onStartChange={setStartDate}
            onEndChange={setEndDate}
          />
        </div>

        {detailLoading ? (
          <LoadingSpinner />
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <StatCard label="Flights in Range" value={flights.length} />
              <StatCard label="Flights with Alarms" value={flightsWithAlarms ?? '—'} />
              <StatCard
                label="Flew Hours"
                value={flewHours.length > 0 ? String(Object.values(flewHours[0])[0] ?? '—') : '—'}
              />
            </div>

            {alarmChartData.length > 0 && (
              <Card className="mb-6">
                <Title>Alarm Breakdown</Title>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={alarmChartData} margin={{ top: 4, right: 16, bottom: 60, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-40} textAnchor="end" interval={0} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}

            <Card>
              <Title>Recent Flights</Title>
              <DataTable
                columns={[
                  { key: 'id_volo', label: 'Flight ID' },
                  { key: 'stick_on', label: 'Departure' },
                  { key: 'stick_off', label: 'Arrival' },
                ]}
                data={flights.slice(0, 50)}
                emptyMessage="No flights in this date range."
              />
            </Card>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-tremor-content-strong">Pilots</h1>
          <Text className="mt-0.5">{totalItems} pilots in range</Text>
        </div>
        <DateRangePicker
          startDate={startDate}
          endDate={endDate}
          onStartChange={setStartDate}
          onEndChange={setEndDate}
        />
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="px-5 py-3 flex items-center gap-3" style={{ borderBottom: '1px solid #e5e7eb' }}>
          <TextInput
            placeholder="Search by name…"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { setSearch(inputVal); setPage(1) } }}
            className="max-w-xs"
          />
          <Button
            size="sm"
            onClick={() => { setSearch(inputVal); setPage(1) }}
            style={{ background: '#0d1f14', color: '#b8f04a', border: 'none' }}
          >
            Search
          </Button>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <>
            <DataTable
              columns={[
                { key: 'codcf', label: 'ID' },
                { key: 'nome', label: 'Name' },
                { key: 'cognome', label: 'Surname' },
                { key: 'email', label: 'Email' },
              ]}
              data={pilots}
              onRowClick={(row) => setSelected(row)}
              emptyMessage="No pilots found."
            />
            <div className="px-5 py-3 flex items-center justify-between text-sm text-tremor-content" style={{ borderTop: '1px solid #e5e7eb' }}>
              <Text>Page {page} of {totalPages} · {totalItems} total</Text>
              <div className="flex gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="p-1.5 rounded-tremor-small hover:bg-tremor-background-subtle disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="p-1.5 rounded-tremor-small hover:bg-tremor-background-subtle disabled:opacity-40 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
