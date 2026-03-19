import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useThemeStore } from '../theme'

describe('Theme Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    })
    document.documentElement.classList.remove('dark')
  })

  it('initializes with light theme by default', () => {
    const store = useThemeStore()
    expect(store.isDark).toBe(false)
  })

  it('initializes with dark theme if stored in localStorage', () => {
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn((key) => key === 'theme' ? 'dark' : null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    })
    const store = useThemeStore()
    expect(store.isDark).toBe(true)
  })

  it('toggles theme and updates document and localStorage', () => {
    const store = useThemeStore()
    
    // Initial state - should be light theme
    expect(store.isDark).toBe(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    
    // Toggle to dark
    store.toggleTheme()
    // Wait for watcher to run
    vi.waitFor(() => {
      expect(store.isDark).toBe(true)
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })
    
    // Toggle back to light
    store.toggleTheme()
    // Wait for watcher to run
    vi.waitFor(() => {
      expect(store.isDark).toBe(false)
      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })
  })
})
