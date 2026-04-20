interface ActivityEntry {
  type: string
  data: any
  timestamp: string
}

interface ActivityFeedProps {
  entries: ActivityEntry[]
}

const typeColors: Record<string, string> = {
  'training.training_step': 'text-accent-green',
  'training.weight': 'text-accent-amber',
  'training.error': 'text-accent-red',
  'training.research': 'text-blue-400',
}

export default function ActivityFeed({ entries }: ActivityFeedProps) {
  if (!entries.length) {
    return <div className="text-gray-500 text-sm p-3">No activity yet</div>
  }

  return (
    <div className="space-y-1 text-xs max-h-96 overflow-y-auto">
      {entries.map((entry, i) => (
        <div key={i} className="flex gap-2 px-3 py-1.5 hover:bg-bg-hover rounded">
          <span className="text-gray-600 shrink-0 font-mono">
            {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
          <span className={typeColors[entry.type] || 'text-gray-400'}>
            {entry.data?.message || JSON.stringify(entry.data)}
          </span>
        </div>
      ))}
    </div>
  )
}
