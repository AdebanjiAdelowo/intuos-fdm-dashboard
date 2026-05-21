import { useEffect, useState } from 'react'
import { Plane, Users, Activity, AlertTriangle } from 'lucide-react'
import { Card, Title, Text, BarChart as TremorBar } from '@tremor/react'
import {
  getRegistrationsWithFlightsCount,
  getPilotsWithFlightsCount,
  getTopRegistrationsByAlarms,
  AlarmSummary,
} from '../api'
import StatCard from '../components/StatCard'
import DateRangePicker from '../components/DateRangePicker'
import LoadingSpinner from '../components/LoadingSpinner'
import { useDateRange } from '../hooks/useDateRange'

export default function DashboardPage() {
  const { startDate, endDate, setStartDate, setEndDate } = useDateRange()
  const [regCount, setRegCount] = useState<number | null>(null)
  const [pilotCount, setPilotCount] = useState<number | null>(null)
  const [topAlarms, setTopAlarms] = useState<AlarmSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    Promise.all([
      getRegistrationsWithFlightsCount(),
      getPilotsWithFlightsCount(),
      getTopRegistrationsByAlarms(10, startDate, endDate),
    ])
      .then(([rc, pc, alarms]) => {
        setRegCount(rc.data)
        setPilotCount(pc.data)
        setTopAlarms(Array.isArray(alarms.data) ? alarms.data : [])
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [startDate, endDate])

  const chartData = topAlarms
    .slice(0, 10)
    .map((a) => ({ name: String(a.registration ?? a['marche'] ?? '?'), Total: Number(a.total ?? 0) }))

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-tremor-content-strong">Overview</h1>
          <Text className="mt-0.5">Fleet performance summary</Text>
        </div>
        <DateRangePicker
          startDate={startDate}
          endDate={endDate}
          onStartChange={setStartDate}
          onEndChange={setEndDate}
        />
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-tremor-default text-sm">{error}</div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Aircraft with Flights" value={regCount ?? '—'} icon={<Plane className="w-5 h-5" />} accent />
        <StatCard label="Pilots with Flights" value={pilotCount ?? '—'} icon={<Users className="w-5 h-5" />} />
        <StatCard label="Date Range" value={`${startDate} → ${endDate}`} icon={<Activity className="w-5 h-5" />} />
        <StatCard label="Top Alarm Registrations" value={chartData.length} icon={<AlertTriangle className="w-5 h-5" />} />
      </div>

      {/* Chart */}
      <Card>
        <Title>Top Registrations by Total Alarms</Title>
        <Text className="mt-1 mb-4">Top 10 aircraft by alarm count in the selected range</Text>
        {loading ? (
          <LoadingSpinner />
        ) : chartData.length === 0 ? (
          <p className="text-sm text-tremor-content text-center py-10">No alarm data for the selected range.</p>
        ) : (
          <TremorBar
            data={chartData}
            index="name"
            categories={['Total']}
            colors={['green']}
            valueFormatter={(v) => v.toLocaleString()}
            showLegend={false}
            className="h-72 mt-4"
          />
        )}
      </Card>
    </div>
  )
}
