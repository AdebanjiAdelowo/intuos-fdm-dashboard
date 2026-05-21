import { Card, Metric, Text } from '@tremor/react'

interface Props {
  label: string
  value: string | number
  sub?: string
  icon?: React.ReactNode
  accent?: boolean
}

export default function StatCard({ label, value, sub, icon, accent }: Props) {
  return (
    <Card className="flex items-center gap-4 p-5" decoration={accent ? 'left' : undefined} decorationColor="green">
      {icon && (
        <div
          className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center"
          style={accent ? { background: '#b8f04a', color: '#0d1f14' } : { background: '#f0fdf4', color: '#166534' }}
        >
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <Text className="uppercase tracking-wide text-xs font-medium truncate">{label}</Text>
        <Metric className="mt-0.5">{String(value)}</Metric>
        {sub && <Text className="mt-0.5 text-xs">{sub}</Text>}
      </div>
    </Card>
  )
}
