interface Props {
  startDate: string
  endDate: string
  onStartChange: (v: string) => void
  onEndChange: (v: string) => void
}

export default function DateRangePicker({ startDate, endDate, onStartChange, onEndChange }: Props) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm text-gray-600 font-medium">From</label>
      <input
        type="date"
        value={startDate}
        max={endDate}
        onChange={(e) => onStartChange(e.target.value)}
        className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
      />
      <label className="text-sm text-gray-600 font-medium">To</label>
      <input
        type="date"
        value={endDate}
        min={startDate}
        onChange={(e) => onEndChange(e.target.value)}
        className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
      />
    </div>
  )
}
