const STYLES: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border border-red-300',
  high:     'bg-orange-100 text-orange-800 border border-orange-300',
  medium:   'bg-yellow-100 text-yellow-800 border border-yellow-300',
  low:      'bg-gray-100 text-gray-600 border border-gray-300',
}

const LABELS: Record<string, string> = {
  critical: 'CRITICAL',
  high:     'HIGH',
  medium:   'MEDIUM',
  low:      'LOW',
}

export function PriorityBadge({ priority, size = 'sm' }: { priority: string; size?: 'sm' | 'xs' }) {
  const text = size === 'xs' ? 'text-[10px]' : 'text-xs'
  return (
    <span className={`inline-block px-2 py-0.5 rounded font-bold ${text} ${STYLES[priority] ?? STYLES.low}`}>
      {LABELS[priority] ?? priority.toUpperCase()}
    </span>
  )
}
