import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { alarmColor, alarmLabel } from '../constants/alarmColors'

interface AlarmEntry {
  name: string
  value: number
}

interface Props {
  data: AlarmEntry[]
  height?: number
}

export default function AlarmDonut({ data, height = 260 }: Props) {
  if (data.length === 0) return <p className="text-sm text-gray-400 text-center py-10">No alarm data</p>

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius="55%"
          outerRadius="75%"
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={alarmColor(entry.name)} />
          ))}
        </Pie>
        <Tooltip
          formatter={(val: number, name: string) => [val.toLocaleString(), alarmLabel(name)]}
        />
        <Legend
          formatter={(value: string) => alarmLabel(value)}
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 11 }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
