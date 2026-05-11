interface Props {
  label: string
  value: string | number
  sub?: string
  icon?: React.ReactNode
  accent?: boolean
}

export default function StatCard({ label, value, sub, icon, accent }: Props) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-start gap-4 shadow-sm">
      {icon && (
        <div
          className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center"
          style={accent ? { background: '#b8f04a', color: '#0d1f14' } : { background: '#f0fdf4', color: '#166534' }}
        >
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide truncate">{label}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}
