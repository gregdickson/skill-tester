import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import ChatPanel from '../components/ChatPanel'

export default function CommandMode() {
  const { id } = useParams<{ id: string }>()
  const [outputs, setOutputs] = useState<any[]>([])
  const [selectedOutput, setSelectedOutput] = useState<any>(null)
  const [generating, setGenerating] = useState(false)
  const [showRaw, setShowRaw] = useState(false)

  useEffect(() => {
    if (id) {
      api.listOutputs(id).then(setOutputs)
    }
  }, [id])

  const generate = async () => {
    if (!id) return
    setGenerating(true)
    try {
      const output = await api.generateOutput(id)
      setOutputs((prev) => [output, ...prev])
      setSelectedOutput(output)
    } catch {
      // ignore
    } finally {
      setGenerating(false)
    }
  }

  const download = (output: any) => {
    const blob = new Blob([output.content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `skill-v${output.version}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-subtle">
          <h1 className="text-xl font-bold">Command Mode</h1>
          <div className="flex gap-2">
            <button
              onClick={generate}
              disabled={generating}
              className="px-4 py-2 bg-accent-green text-black rounded font-medium text-sm disabled:opacity-50"
            >
              {generating ? 'Generating...' : 'Generate Output'}
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Output list */}
          <div className="w-48 border-r border-border-subtle overflow-y-auto">
            <div className="p-2 text-xs text-gray-500">Outputs ({outputs.length})</div>
            {outputs.map((o) => (
              <button
                key={o.id}
                onClick={() => setSelectedOutput(o)}
                className={`w-full text-left px-3 py-2 text-sm border-b border-border-subtle/50 ${
                  selectedOutput?.id === o.id ? 'bg-bg-hover text-accent-green' : 'hover:bg-bg-hover'
                }`}
              >
                <div className="font-mono">v{o.version}</div>
                <div className="text-xs text-gray-500">
                  Score: {(o.quality_score * 100).toFixed(0)}%
                </div>
              </button>
            ))}
          </div>

          {/* Output viewer */}
          <div className="flex-1 overflow-auto">
            {selectedOutput ? (
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h2 className="font-mono text-sm">Version {selectedOutput.version}</h2>
                    <span className="text-xs text-gray-500">
                      Score: {(selectedOutput.quality_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowRaw(!showRaw)}
                      className="px-2 py-1 text-xs bg-bg-hover rounded"
                    >
                      {showRaw ? 'Preview' : 'Raw'}
                    </button>
                    <button
                      onClick={() => download(selectedOutput)}
                      className="px-2 py-1 text-xs bg-bg-hover rounded hover:text-accent-green"
                    >
                      Download .md
                    </button>
                  </div>
                </div>
                <div className="bg-bg-panel border border-border-subtle rounded p-4">
                  <pre className="text-sm whitespace-pre-wrap font-mono leading-relaxed">
                    {selectedOutput.content}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                {outputs.length ? 'Select an output to view' : 'Generate your first output'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chat panel */}
      <div className="w-80 border-l border-border-subtle">
        <div className="px-3 py-2 border-b border-border-subtle text-xs text-gray-500">Chat (Command Mode)</div>
        <ChatPanel networkId={id!} mode="command" />
      </div>
    </div>
  )
}
