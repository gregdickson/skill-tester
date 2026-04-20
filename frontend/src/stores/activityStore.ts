import { create } from 'zustand'

interface ActivityEntry {
  type: string
  data: any
  timestamp: string
}

interface ActivityState {
  entries: ActivityEntry[]
  addEntry: (entry: any) => void
  clear: () => void
}

export const useActivityStore = create<ActivityState>((set) => ({
  entries: [],

  addEntry: (entry) =>
    set((state) => ({
      entries: [
        { ...entry, timestamp: new Date().toISOString() },
        ...state.entries,
      ].slice(0, 200),
    })),

  clear: () => set({ entries: [] }),
}))
