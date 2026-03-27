import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(scriptDir, '..')
const envPath = path.join(repoRoot, '.env')

function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {}
  }

  const result = {}
  const lines = fs.readFileSync(filePath, 'utf8').split(/\r?\n/)

  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue
    const eqIndex = line.indexOf('=')
    if (eqIndex === -1) continue
    const key = line.slice(0, eqIndex).trim()
    const value = line.slice(eqIndex + 1).trim()
    result[key] = value
  }

  return result
}

function isTruthy(value) {
  return ['1', 'true', 'yes', 'on'].includes((value ?? '').toLowerCase())
}

const env = {
  ...parseEnvFile(envPath),
  ...process.env
}

const failures = []
const warnings = []

const databaseUrl = env.DATABASE_URL || ''
const hasPgFields = ['PGUSER', 'PGPASSWORD', 'PGHOST', 'PGDATABASE'].every((key) => env[key])
const appEnv = (env.APP_ENV || '').toLowerCase()
const secretKey = env.SECRET_KEY || ''

if (appEnv !== 'production') {
  failures.push('APP_ENV should be set to production.')
}

if (secretKey.length < 32 || ['change-me-in-production', 'changeme'].includes(secretKey)) {
  failures.push('SECRET_KEY must be a strong 32+ character value.')
}

if (!databaseUrl && !hasPgFields) {
  failures.push('Set DATABASE_URL or all required PG* values for Supabase/Postgres.')
}

if ((databaseUrl || '').startsWith('sqlite') && !isTruthy(env.ALLOW_SQLITE_IN_PRODUCTION)) {
  failures.push('Production must not point to SQLite.')
}

if (env.SEED_DEMO_DATA === '1') {
  warnings.push('SEED_DEMO_DATA is enabled. Disable it for a real production database.')
}

if (env.DEMO_RESET_PASSWORDS === '1') {
  warnings.push('DEMO_RESET_PASSWORDS is enabled. Disable it in production.')
}

if (!fs.existsSync(path.join(repoRoot, 'dist', 'index.html'))) {
  warnings.push('Frontend dist bundle is missing. Run npm run build-only before non-Docker deploys.')
}

if (failures.length > 0) {
  console.error('Production readiness check failed:')
  for (const failure of failures) {
    console.error(`- ${failure}`)
  }
  if (warnings.length > 0) {
    console.error('Warnings:')
    for (const warning of warnings) {
      console.error(`- ${warning}`)
    }
  }
  process.exit(1)
}

console.log('Production readiness check passed.')
if (warnings.length > 0) {
  console.log('Warnings:')
  for (const warning of warnings) {
    console.log(`- ${warning}`)
  }
}
