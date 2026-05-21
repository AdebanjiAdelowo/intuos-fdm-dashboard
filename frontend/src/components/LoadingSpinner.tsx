export default function LoadingSpinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-tremor-content">
      <div className="w-8 h-8 border-4 border-t-transparent rounded-full animate-spin mb-3" style={{ borderColor: '#0d1f14', borderTopColor: 'transparent' }} />
      <p className="text-sm">{label}</p>
    </div>
  )
}
