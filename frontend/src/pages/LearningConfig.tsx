import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import ChatPanel from '../components/ChatPanel'

export default function LearningConfig() {
  const { id } = useParams<{ id: string }>()
  const [config, setConfig] = useState<any>({})
  const [networkConfig, setNetworkConfig] = useState<any>({})
  const [howItWorks, setHowItWorks] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (id) {
      api.getConfig(id, 'learn').then((data) => {
        setConfig(data.config || {})
        setNetworkConfig(data.network_config || {})
        setHowItWorks(data.how_it_works || '')
      })
    }
  }, [id])

  const save = async () => {
    if (!id) return
    setSaving(true)
    try {
      await api.updateConfig(id, 'learn', {
        how_it_works: howItWorks,
        network_config: networkConfig,
        ...config,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  const updateNetworkConfig = (key: string, value: any) => {
    setNetworkConfig((prev: any) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-2xl">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-xl font-bold">Learning Config</h1>
            <button
              onClick={save}
              disabled={saving}
              className="px-4 py-2 bg-accent-green text-black rounded font-medium text-sm disabled:opacity-50"
            >
              {saved ? 'Saved!' : saving ? 'Saving...' : 'Save'}
            </button>
          </div>

          <div className="space-y-5">
            <div>
              <label className="block text-sm text-gray-400 mb-1">How It Works</label>
              <textarea
                value={howItWorks}
                onChange={(e) => setHowItWorks(e.target.value)}
                rows={6}
                placeholder="Master instruction block that governs all training behaviour..."
                className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-green resize-y"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Learning Rate</label>
                <input
                  type="number"
                  step="0.001"
                  value={networkConfig.learning_rate ?? 0.01}
                  onChange={(e) => updateNetworkConfig('learning_rate', parseFloat(e.target.value))}
                  className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-green"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Research Depth (0-5)</label>
                <input
                  type="number"
                  min="0"
                  max="5"
                  value={networkConfig.research_depth ?? 0}
                  onChange={(e) => updateNetworkConfig('research_depth', parseInt(e.target.value))}
                  className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-green"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Components Per Step</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={networkConfig.components_per_step ?? 5}
                  onChange={(e) => updateNetworkConfig('components_per_step', parseInt(e.target.value))}
                  className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-green"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Full Regen Frequency</label>
                <input
                  type="number"
                  min="1"
                  value={networkConfig.full_regen_frequency ?? 10}
                  onChange={(e) => updateNetworkConfig('full_regen_frequency', parseInt(e.target.value))}
                  className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-green"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Priority Multipliers</label>
              <div className="grid grid-cols-4 gap-2">
                {['critical', 'high', 'medium', 'low'].map((p) => (
                  <div key={p}>
                    <label className="block text-xs text-gray-500 mb-0.5 capitalize">{p}</label>
                    <input
                      type="number"
                      step="0.1"
                      value={networkConfig.priority_multipliers?.[p] ?? { critical: 2.0, high: 1.5, medium: 1.0, low: 0.5 }[p]}
                      onChange={(e) =>
                        updateNetworkConfig('priority_multipliers', {
                          ...(networkConfig.priority_multipliers || {}),
                          [p]: parseFloat(e.target.value),
                        })
                      }
                      className="w-full bg-bg-panel border border-border-subtle rounded px-2 py-1 text-sm font-mono focus:outline-none focus:border-accent-green"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Model</label>
              <input
                type="text"
                value={networkConfig.model_config?.research_model ?? 'moonshotai/kimi-k2'}
                onChange={(e) =>
                  updateNetworkConfig('model_config', {
                    research_model: e.target.value,
                    evaluator_model: e.target.value,
                    generator_model: e.target.value,
                  })
                }
                className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-green"
              />
              <p className="text-xs text-gray-600 mt-1">OpenRouter model ID (used for all AI roles)</p>
            </div>
          </div>
        </div>
      </div>

      {/* Chat panel */}
      <div className="w-80 border-l border-border-subtle">
        <div className="px-3 py-2 border-b border-border-subtle text-xs text-gray-500">Chat (Learn Mode)</div>
        <ChatPanel networkId={id!} mode="learn" />
      </div>
    </div>
  )
}
