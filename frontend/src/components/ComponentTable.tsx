interface ComponentTableProps {
  components: any[]
  onUpdate?: (id: string, updates: any) => void
}

const statusColors: Record<string, string> = {
  strong: 'bg-accent-green/20 text-accent-green',
  developing: 'bg-accent-amber/20 text-accent-amber',
  weak: 'bg-accent-red/20 text-accent-red',
}

const priorityColors: Record<string, string> = {
  critical: 'text-accent-red',
  high: 'text-accent-amber',
  medium: 'text-gray-400',
  low: 'text-gray-600',
}

export default function ComponentTable({ components, onUpdate }: ComponentTableProps) {
  if (!components.length) {
    return <div className="text-gray-500 text-sm p-4">No components yet</div>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-500 text-xs border-b border-border-subtle">
            <th className="text-left py-2 px-3">#</th>
            <th className="text-left py-2 px-3">Component</th>
            <th className="text-left py-2 px-3">Priority</th>
            <th className="text-left py-2 px-3">Weight</th>
            <th className="text-left py-2 px-3">Score</th>
            <th className="text-left py-2 px-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {components.map((c, i) => (
            <tr key={c.id} className="border-b border-border-subtle/50 hover:bg-bg-hover">
              <td className="py-2 px-3 text-gray-600 font-mono">{i + 1}</td>
              <td className="py-2 px-3">
                <div className="font-medium">{c.name}</div>
                {c.description && (
                  <div className="text-gray-500 text-xs mt-0.5 line-clamp-1">{c.description}</div>
                )}
              </td>
              <td className={`py-2 px-3 text-xs font-mono ${priorityColors[c.priority] || ''}`}>
                {c.priority}
              </td>
              <td className="py-2 px-3">
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-bg-primary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent-green rounded-full transition-all"
                      style={{ width: `${c.weight * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-gray-400">{c.weight.toFixed(2)}</span>
                </div>
              </td>
              <td className="py-2 px-3">
                <span className="text-xs font-mono">{(c.score_pct || 0).toFixed(0)}%</span>
              </td>
              <td className="py-2 px-3">
                <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[c.status] || ''}`}>
                  {c.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
