import { create } from 'zustand'
import { api } from '../api/client'

interface NetworkState {
  networks: any[]
  currentNetwork: any | null
  components: any[]
  loading: boolean
  error: string | null
  fetchNetworks: () => Promise<void>
  fetchNetwork: (id: string) => Promise<void>
  fetchComponents: (networkId: string) => Promise<void>
  setCurrentNetwork: (network: any) => void
  updateComponentLocally: (id: string, updates: any) => void
}

export const useNetworkStore = create<NetworkState>((set, get) => ({
  networks: [],
  currentNetwork: null,
  components: [],
  loading: false,
  error: null,

  fetchNetworks: async () => {
    set({ loading: true, error: null })
    try {
      const networks = await api.listNetworks()
      set({ networks, loading: false })
    } catch (e: any) {
      set({ error: e.message, loading: false })
    }
  },

  fetchNetwork: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const network = await api.getNetwork(id)
      set({ currentNetwork: network, loading: false })
    } catch (e: any) {
      set({ error: e.message, loading: false })
    }
  },

  fetchComponents: async (networkId: string) => {
    try {
      const components = await api.listComponents(networkId)
      set({ components })
    } catch (e: any) {
      set({ error: e.message })
    }
  },

  setCurrentNetwork: (network) => set({ currentNetwork: network }),

  updateComponentLocally: (id, updates) => {
    set((state) => ({
      components: state.components.map((c) =>
        c.id === id ? { ...c, ...updates } : c
      ),
    }))
  },
}))
