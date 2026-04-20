import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useNetworkStore } from '../stores/networkStore'
import NetworkCard from '../components/NetworkCard'

export default function NetworkManager() {
  const { networks, loading, error, fetchNetworks } = useNetworkStore()

  useEffect(() => {
    fetchNetworks()
  }, [])

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Networks</h1>
        <Link
          to="/networks/new"
          className="px-4 py-2 bg-accent-green text-black rounded font-medium text-sm"
        >
          New Network
        </Link>
      </div>

      {loading && <p className="text-gray-500">Loading...</p>}
      {error && <p className="text-accent-red text-sm">{error}</p>}

      {!loading && networks.length === 0 && (
        <div className="text-center py-16">
          <p className="text-gray-500 mb-4">No networks yet</p>
          <Link
            to="/networks/new"
            className="px-4 py-2 bg-accent-green text-black rounded font-medium text-sm"
          >
            Create your first network
          </Link>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {networks.map((network) => (
          <NetworkCard key={network.id} network={network} />
        ))}
      </div>
    </div>
  )
}
