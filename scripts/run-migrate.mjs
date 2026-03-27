import { spawn } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(scriptDir, '..')

const candidates = [
  path.join(repoRoot, '.venv314', 'Scripts', 'python.exe'),
  path.join(repoRoot, '.venv', 'Scripts', 'python.exe'),
  path.join(repoRoot, '.venv314', 'bin', 'python'),
  path.join(repoRoot, '.venv', 'bin', 'python'),
  'python',
  'py'
]

const python = candidates.find((candidate) => {
  if (candidate === 'python' || candidate === 'py') return true
  return fs.existsSync(candidate)
})

const scriptPath = path.join(repoRoot, 'scripts', 'migrate_sqlite_to_supabase.py')
const args = [scriptPath, ...process.argv.slice(2)]

const child = spawn(python, args, {
  cwd: repoRoot,
  stdio: 'inherit',
  shell: false
})

child.on('exit', (code) => {
  process.exit(code ?? 1)
})
