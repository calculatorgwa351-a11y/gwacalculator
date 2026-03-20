const palette = [
  '#1d4ed8',
  '#0ea5e9',
  '#14b8a6',
  '#f97316',
  '#e11d48',
  '#7c3aed',
  '#0f766e',
  '#0891b2'
]

const hashCode = (value: string) => {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

export const getAvatarColor = (seed?: string) => {
  if (!seed) return palette[0]
  const idx = hashCode(seed) % palette.length
  return palette[idx]
}

export const getInitials = (name?: string) => {
  if (!name) return 'S'
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase()
  return `${parts[0].charAt(0)}${parts[parts.length - 1].charAt(0)}`.toUpperCase()
}
