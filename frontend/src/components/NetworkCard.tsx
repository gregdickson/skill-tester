import { Link } from 'react-router-dom'

interface NetworkCardProps {
  network: any
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-700 text-gray-300',
  training: 'bg-accent-amber/20 text-accent-amber',
  converged: 'bg-accent-green/20 text-accent-green',
  archived: 'bg-gray-800 text-gray-500',
}

export default function NetworkCard({ network }: NetworkCardProps) {
  return (
    <div className="bg-bg-panel border border-border-subtle rounded-lg p-4 hover:border-accent-green/30 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-medium text-sm">{network.title}</h3>
        <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[network.status] || ''}`}>
          {network.status}
        </span>
      </div>

      {network.purpose && (
        <p className="text-gray-500 text-xs mb-3 line-clamp-2">{network.purpose}</p>
      )}

      <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
        <span>Loss: {network.current_loss?.toFixed(4) || 'N/A'}</span>
        <span>Steps: {network.total_steps}</span>
        <span>Ready: {network.readiness_pct?.toFixed(0) || 0}%</span>
      </div>

      {/* Readiness bar */}
      <div className="w-full h-1 bg-bg-primary rounded-full mb-3 overflow-hidden">
        <div
          className="h-full bg-accent-green rounded-full transition-all"
          style={{ width: `${network.readiness_pct || 0}%` }}
        />
      </div>

      <div className="flex gap-2">
        <Link
          to={`/networks/${network.id}/training`}
          className="text-xs px-3 py-1 bg-bg-hover rounded hover:bg-accent-green/10 hover:text-accent-green transition-colors"
        >
          Training Lab
        </Link>
        <Link
          to={`/networks/${network.id}/command`}
          className="text-xs px-3 py-1 bg-bg-hover rounded hover:bg-accent-green/10 hover:text-accent-green transition-colors"
        >
          Command
        </Link>
        <Link
          to={`/networks/${network.id}/config`}
          className="text-xs px-3 py-1 bg-bg-hover rounded hover:bg-accent-green/10 hover:text-accent-green transition-colors"
        >
          Config
        </Link>
      </div>
    </div>
  )
}
