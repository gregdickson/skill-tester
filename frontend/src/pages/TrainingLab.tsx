import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import { useNetworkStore } from '../stores/networkStore'
import { useActivityStore } from '../stores/activityStore'
import ComponentTable from '../components/ComponentTable'
import LossChart from '../components/LossChart'
import ActivityFeed from '../components/ActivityFeed'
import ChatPanel from '../components/ChatPanel'

export default function TrainingLab() {
  const { id } = useParams<{ id: string }>()
  const { currentNetwork, components, fetchNetwork, fetchComponents } = useNetworkStore()
  const { entries, addEntry, clear } = useActivityStore()
  const [lossHistory, setLossHistory] = useState<{ step: number; loss: number }[]>([])
  const [training, setTraining] = useState(false)
  const [steps, setSteps] = useState(50)
  const [activeTab, setActiveTab] = useState<'activity' | 'chat'>('activity')

  useEffect(() => {
    if (id) {
      fetchNetwork(id)
      fetchComponents(id)
      clear()
      api.getLossHistory(id).then((data) => setLossHistory(data.loss_history || []))
    }
  }, [id])

  const handleWsMessage = useCallback((data: any) => {
    addEntry(data)
    if (data.type === 'training.training_step' && data.data?.loss !== undefined) {
      setLossHistory((prev) => [...prev, { step: prev.length + 1, loss: data.data.loss }])
    }
    if (data.type === 'training.weight') {
      // Refresh components to get updated weights
      if (id) fetchComponents(id)
    }
    if (data.type === 'training.complete' || data.type === 'training.error') {
      setTraining(false)
      if (id) {
        fetchNetwork(id)
        fetchComponents(id)
      }
    }
  }, [id, addEntry, fetchComponents, fetchNetwork])

  useWebSocket(id, handleWsMessage)

  const startTraining = async () => {
    if (!id) return
    setTraining(true)
    try {
      await api.startTraining(id, steps)
    } catch (e: any) {
      setTraining(false)
      addEntry({ type: 'training.error', data: { message: e.message } })
    }
  }

  const pauseTraining = async () => {
    if (!id) return
    try {
      await api.pauseTraining(id)
      setTraining(false)
    } catch {
      // ignore
    }
  }

  if (!currentNetwork) {
    return <div className="p-6 text-gray-500">Loading...</div>
  }

  const strong = components.filter((c) => c.status === 'strong').length
  const developing = components.filter((c) => c.status === 'developing').length
  const weak = components.filter((c) => c.status === 'weak').length

  return (
    <div className="flex h-full">
      {/* Left panel */}
      <div className="w-64 border-r border-border-subtle p-4 flex flex-col gap-4">
        <div>
          <h2 className="text-lg font-bold">{currentNetwork.title}</h2>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            currentNetwork.status === 'training' ? 'bg-accent-amber/20 text-accent-amber' :
            currentNetwork.status === 'converged' ? 'bg-accent-green/20 text-accent-green' :
            'bg-gray-700 text-gray-300'
          }`}>
            {currentNetwork.status}
          </span>
        </div>

        <div className="space-y-2">
          <div>
            <span className="text-xs text-gray-500">Loss</span>
            <p className="text-2xl font-mono text-accent-green">
              {currentNetwork.current_loss?.toFixed(4) || '—'}
            </p>
          </div>
          <div>
            <span className="text-xs text-gray-500">Steps</span>
            <p className="text-lg font-mono">{currentNetwork.total_steps}</p>
          </div>
          <div>
            <span className="text-xs text-gray-500">Readiness</span>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-bg-primary rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent-green rounded-full transition-all"
                  style={{ width: `${currentNetwork.readiness_pct || 0}%` }}
                />
              </div>
              <span className="text-xs font-mono">{(currentNetwork.readiness_pct || 0).toFixed(0)}%</span>
            </div>
          </div>
        </div>

        <div className="text-xs space-y-1">
          <div className="flex justify-between">
            <span className="text-accent-green">Strong</span>
            <span>{strong}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-accent-amber">Developing</span>
            <span>{developing}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-accent-red">Weak</span>
            <span>{weak}</span>
          </div>
        </div>

        <div className="space-y-2 mt-auto">
          <div>
            <label className="text-xs text-gray-500">Steps</label>
            <input
              type="number"
              value={steps}
              onChange={(e) => setSteps(parseInt(e.target.value) || 50)}
              className="w-full bg-bg-primary border border-border-subtle rounded px-2 py-1 text-sm font-mono"
            />
          </div>
          {!training ? (
            <button
              onClick={startTraining}
              className="w-full px-3 py-2 bg-accent-green text-black rounded font-medium text-sm"
            >
              Start Training
            </button>
          ) : (
            <button
              onClick={pauseTraining}
              className="w-full px-3 py-2 bg-accent-amber text-black rounded font-medium text-sm"
            >
              Pause Training
            </button>
          )}
        </div>
      </div>

      {/* Centre panel */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Loss chart */}
        <div className="border-b border-border-subtle p-4">
          <h3 className="text-sm text-gray-400 mb-2">Loss Curve</h3>
          <LossChart data={lossHistory} />
        </div>

        {/* Component table */}
        <div className="flex-1 overflow-auto p-4">
          <h3 className="text-sm text-gray-400 mb-2">Components ({components.length})</h3>
          <ComponentTable components={components} />
        </div>
      </div>

      {/* Right panel */}
      <div className="w-80 border-l border-border-subtle flex flex-col">
        <div className="flex border-b border-border-subtle">
          <button
            onClick={() => setActiveTab('activity')}
            className={`flex-1 px-3 py-2 text-xs ${
              activeTab === 'activity' ? 'text-accent-green border-b-2 border-accent-green' : 'text-gray-500'
            }`}
          >
            Activity
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex-1 px-3 py-2 text-xs ${
              activeTab === 'chat' ? 'text-accent-green border-b-2 border-accent-green' : 'text-gray-500'
            }`}
          >
            Chat
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          {activeTab === 'activity' ? (
            <ActivityFeed entries={entries} />
          ) : (
            <ChatPanel networkId={id!} mode="learn" />
          )}
        </div>
      </div>
    </div>
  )
}
