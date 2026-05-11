import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend,
} from 'recharts'
import { getAllAlarms, getTopRegistrationsByAlarms, AlarmSummary } from '../api'
import DateRangePicker from '../components/DateRangePicker'
import LoadingSpinner from '../components/LoadingSpinner'
import DataTable from '../components/DataTable'
import { useDateRange } from '../hooks/useDateRange'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

export default function AlarmsPage() {
  const { startDate, endDate, setStartDate, setEndDate } = useDateRange()
  const [allAlarms, setAllAlarms] = useState<AlarmSummary[]>([])
  const [topN, setTopN] = useState(10)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    Promise.all([
      getAllAlarms(startDate, endDate),
      getTopRegistrationsByAlarms(topN, startDate, endDate),
    ])
      .then(([all]) => {
        setAllAlarms(Array.isArray(all.data) ? all.data : [])
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [startDate, endDate, topN])

  // Total alarms by registration bar chart
  const regSummary = allAlarms
    .map((r) => ({
      name: String(r.registration ?? '?'),
      total: Number(r.total ?? 0),
    }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 20)

  // Aggregate alarm types across all registrations
  const alarmTypeTotals: Record<string, number> = {}
  for (const row of allAlarms) {
    for (const [k, v] of Object.entries(row)) {
      if (k === 'registration' || k === 'total') continue
      alarmTypeTotals[k] = (alarmTypeTotals[k] ?? 0) + Number(v)
    }
  }
  const alarmTypeData = Object.entries(alarmTypeTotals)
    .map(([name, count]) => ({ name, count }))
    .filter((d) => d.count > 0)
    .sort((a, b) => b.count - a.count)
    .slice(0, 20)

  const tableCols = allAlarms.length > 0
    ? [
        { key: 'registration', label: 'Registration' },
        { key: 'total', label: 'Total' },
        ...Object.keys(allAlarms[0])
          .filter((k) => k !== 'registration' && k !== 'total')
          .slice(0, 8)
          .map((k) => ({ key: k, label: k })),
      ]
    : []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alarm Analysis</h1>
          <p className="text-sm text-gray-500 mt-0.5">Fleet-wide alarm statistics</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Top N</label>
            <select
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              className="border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {[5, 10, 15, 20].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <DateRangePicker
            startDate={startDate}
            endDate={endDate}
            onStartChange={setStartDate}
            onEndChange={setEndDate}
          />
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Alarms by Registration</h2>
              {regSummary.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">No data</p>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={regSummary} margin={{ top: 4, right: 8, bottom: 50, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                      {regSummary.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Alarm Type Distribution</h2>
              {alarmTypeData.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">No data</p>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={alarmTypeData} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={160} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {tableCols.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-900 mb-3">
                Raw Alarm Data ({allAlarms.length} registrations)
              </h2>
              <DataTable
                columns={tableCols}
                data={allAlarms}
                emptyMessage="No alarm data for the selected range."
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}
