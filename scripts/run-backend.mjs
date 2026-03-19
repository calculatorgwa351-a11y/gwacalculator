import { spawn } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

const cwd = process.cwd()

const candidates = [
  // Preferred local venv names (Windows + POSIX)
  path.join(cwd, '.venv314', 'Scripts', 'python.exe'),
  path.join(cwd, '.venv', 'Scripts', 'python.exe'),
  path.join(cwd, '.venv314', 'bin', 'python'),
  path.join(cwd, '.venv', 'bin', 'python'),

  // Fallbacks
  'python',
  'py'
]

const python = candidates.find((p) => {
  if (p === 'python' || p === 'py') return true
  return fs.existsSync(p)
})

const child = spawn(python, ['-m', 'app.main'], {
  stdio: 'inherit',
  shell: false
})

child.on('exit', (code) => {
  process.exit(code ?? 1)
})

