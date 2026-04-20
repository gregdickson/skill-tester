const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export const api = {
  // Companies
  listCompanies: () => request<any[]>('/companies'),
  createCompany: (data: any) => request<any>('/companies', { method: 'POST', body: JSON.stringify(data) }),

  // Networks
  listNetworks: (companyId?: string) =>
    request<any[]>(`/networks${companyId ? `?company_id=${companyId}` : ''}`),
  createNetwork: (data: any) => request<any>('/networks', { method: 'POST', body: JSON.stringify(data) }),
  getNetwork: (id: string) => request<any>(`/networks/${id}`),
  updateNetwork: (id: string, data: any) =>
    request<any>(`/networks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  generatePlan: (id: string, data?: any) =>
    request<any[]>(`/networks/${id}/generate-plan`, { method: 'POST', body: JSON.stringify(data || {}) }),

  // Components
  listComponents: (networkId: string) => request<any[]>(`/networks/${networkId}/components`),
  createComponent: (networkId: string, data: any) =>
    request<any>(`/networks/${networkId}/components`, { method: 'POST', body: JSON.stringify(data) }),
  updateComponent: (networkId: string, componentId: string, data: any) =>
    request<any>(`/networks/${networkId}/components/${componentId}`, { method: 'PUT', body: JSON.stringify(data) }),
  reorderComponents: (networkId: string, ids: string[]) =>
    request<any>(`/networks/${networkId}/components/reorder`, { method: 'POST', body: JSON.stringify({ ids }) }),

  // Training
  startTraining: (networkId: string, steps?: number) =>
    request<any>(`/networks/${networkId}/train/start`, { method: 'POST', body: JSON.stringify({ steps: steps || 50 }) }),
  pauseTraining: (networkId: string) =>
    request<any>(`/networks/${networkId}/train/pause`, { method: 'POST' }),
  listTrainingRuns: (networkId: string) => request<any[]>(`/networks/${networkId}/training-runs`),
  getLossHistory: (networkId: string) => request<any>(`/networks/${networkId}/loss-history`),

  // Outputs
  listOutputs: (networkId: string) => request<any[]>(`/networks/${networkId}/outputs`),
  generateOutput: (networkId: string, templateId?: string) =>
    request<any>(`/networks/${networkId}/outputs/generate`, {
      method: 'POST',
      body: JSON.stringify({ template_id: templateId || null }),
    }),

  // Chat
  chat: (networkId: string, mode: string, message: string) =>
    request<any>(`/networks/${networkId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ mode, message }),
    }),

  // Activity
  listActivity: (networkId: string, limit?: number) =>
    request<any[]>(`/networks/${networkId}/activity?limit=${limit || 50}`),

  // Config
  getConfig: (networkId: string, mode: string) => request<any>(`/networks/${networkId}/config/${mode}`),
  updateConfig: (networkId: string, mode: string, data: any) =>
    request<any>(`/networks/${networkId}/config/${mode}`, { method: 'PUT', body: JSON.stringify(data) }),
}
