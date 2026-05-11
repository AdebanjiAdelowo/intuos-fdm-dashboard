import { useEffect, useState, useCallback } from 'react'
import { ChevronLeft, ChevronRight, Search, Users } from 'lucide-react'
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
          className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-800 mb-4"
        >
          <ChevronLeft className="w-4 h-4" /> Back to pilots
        </button>

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Users className="w-6 h-6 text-brand-600" />
              {pilotName}
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">Pilot detail · ID {pilotId}</p>
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
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
                <h2 className="text-base font-semibold text-gray-900 mb-4">Alarm Breakdown</h2>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={alarmChartData} margin={{ top: 4, right: 16, bottom: 60, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-40} textAnchor="end" interval={0} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-900 mb-3">Recent Flights</h2>
              <DataTable
                columns={[
                  { key: 'id_volo', label: 'Flight ID' },
                  { key: 'stick_on', label: 'Departure' },
                  { key: 'stick_off', label: 'Arrival' },
                ]}
                data={flights.slice(0, 50)}
                emptyMessage="No flights in this date range."
              />
            </div>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pilots</h1>
          <p className="text-sm text-gray-500 mt-0.5">{totalItems} pilots in range</p>
        </div>
        <DateRangePicker
          startDate={startDate}
          endDate={endDate}
          onStartChange={setStartDate}
          onEndChange={setEndDate}
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { setSearch(inputVal); setPage(1) } }}
              placeholder="Search by name…"
              className="pl-9 pr-3 py-1.5 border border-gray-300 rounded-md text-sm w-full focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <button
            onClick={() => { setSearch(inputVal); setPage(1) }}
            className="bg-brand-600 hover:bg-brand-700 text-white text-sm px-3 py-1.5 rounded-md"
          >
            Search
          </button>
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
            <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-600">
              <span>Page {page} of {totalPages} ({totalItems} total)</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
