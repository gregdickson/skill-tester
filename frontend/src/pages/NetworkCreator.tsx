import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import ComponentTable from '../components/ComponentTable'

export default function NetworkCreator() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [purpose, setPurpose] = useState('')
  const [goal, setGoal] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [components, setComponents] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [networkId, setNetworkId] = useState<string | null>(null)
  const [error, setError] = useState('')

  const createAndGenerate = async () => {
    if (!title || !goal) {
      setError('Title and goal are required')
      return
    }
    setError('')
    setGenerating(true)

    try {
      // Ensure company exists (create default if needed)
      let companies = await api.listCompanies()
      let company = companies[0]
      if (!company) {
        const slug = (companyName || 'default').toLowerCase().replace(/\s+/g, '-')
        company = await api.createCompany({
          name: companyName || 'Default',
          slug,
          description: '',
        })
      }

      // Create network
      const network = await api.createNetwork({
        company_id: company.id,
        title,
        purpose,
        ultimate_end_goal: goal,
      })
      setNetworkId(network.id)

      // Generate components via AI research
      const comps = await api.generatePlan(network.id, { research_depth: 3 })
      setComponents(comps)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  const finish = () => {
    if (networkId) {
      navigate(`/networks/${networkId}/training`)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-bold mb-6">Create Network</h1>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Company Name</label>
          <input
            type="text"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="Default"
            className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-green"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Network Title *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Master Copywriting Skill"
            className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-green"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Purpose</label>
          <input
            type="text"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            placeholder="Multi-component skill mastery scoring"
            className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-green"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Ultimate End Goal *</label>
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Create the best copywriting skill.md that produces elite-level ad copy, email sequences, and landing page content..."
            rows={5}
            className="w-full bg-bg-panel border border-border-subtle rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-green resize-y"
          />
        </div>

        {error && <p className="text-accent-red text-sm">{error}</p>}

        {!components.length && (
          <button
            onClick={createAndGenerate}
            disabled={generating || !title || !goal}
            className="px-4 py-2 bg-accent-green text-black rounded font-medium text-sm disabled:opacity-50"
          >
            {generating ? 'Researching & generating components...' : 'Research & Generate Components'}
          </button>
        )}
      </div>

      {generating && (
        <div className="mt-6 p-4 bg-bg-panel border border-border-subtle rounded">
          <div className="flex items-center gap-2 text-sm text-accent-amber">
            <span className="animate-spin">&#9696;</span>
            AI is researching your goal and decomposing it into components...
          </div>
          <p className="text-xs text-gray-500 mt-2">
            This involves web search, content extraction, and LLM synthesis. May take 30-60 seconds.
          </p>
        </div>
      )}

      {components.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">
              Generated Components ({components.length})
            </h2>
            <button
              onClick={finish}
              className="px-4 py-2 bg-accent-green text-black rounded font-medium text-sm"
            >
              Open Training Lab
            </button>
          </div>
          <div className="bg-bg-panel border border-border-subtle rounded">
            <ComponentTable components={components} />
          </div>
        </div>
      )}
    </div>
  )
}
