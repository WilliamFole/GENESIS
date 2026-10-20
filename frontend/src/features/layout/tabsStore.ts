import { create } from 'zustand'

export type Tab = { path: string; label: string }

type TabsState = {
  tabs: Tab[]
  activePath: string | null
  open: (path: string, label: string) => void
  close: (path: string) => string | null
  closeAll: () => void
}

export const useTabs = create<TabsState>((set, get) => ({
  tabs: [],
  activePath: null,
  open: (path, label) =>
    set((s) => {
      if (s.tabs.find((t) => t.path === path)) return { activePath: path }
      return { tabs: [...s.tabs, { path, label }], activePath: path }
    }),
  close: (path) => {
    const { tabs, activePath } = get()
    const idx = tabs.findIndex((t) => t.path === path)
    if (idx < 0) return activePath
    const newTabs = tabs.filter((t) => t.path !== path)
    let newActive = activePath
    if (activePath === path) {
      newActive = newTabs[idx - 1]?.path ?? newTabs[idx]?.path ?? newTabs[0]?.path ?? null
    }
    set({ tabs: newTabs, activePath: newActive })
    return newActive
  },
  closeAll: () => set({ tabs: [], activePath: null }),
}))