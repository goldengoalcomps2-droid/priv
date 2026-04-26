import { execSync, exec } from 'child_process'
import * as log from './logger.mjs'
import { CONFIG } from './config.mjs'

let lastRestartTime = 0
const RESTART_COOLDOWN_MS = 60_000

export async function restartOpenClaw() {
  if (!CONFIG.autoRestart) {
    log.warn('Auto-restart is disabled. Set AUTO_RESTART=true to enable.')
    return false
  }

  const now = Date.now()
  if (now - lastRestartTime < RESTART_COOLDOWN_MS) {
    log.warn(`Restart cooldown active (${Math.round((RESTART_COOLDOWN_MS - (now - lastRestartTime)) / 1000)}s remaining)`)
    return false
  }

  log.critical('Attempting OpenClaw restart...')
  lastRestartTime = now

  const commands = [
    'openclaw restart',
    'openclaw gateway restart',
    'systemctl restart openclaw',
  ]

  for (const cmd of commands) {
    try {
      execSync(`which ${cmd.split(' ')[0]}`, { stdio: 'ignore' })
      log.info(`Trying: ${cmd}`)
      execSync(cmd, { timeout: 30_000, stdio: 'pipe' })
      log.info(`Restart command succeeded: ${cmd}`)

      await new Promise(r => setTimeout(r, 5000))
      return true
    } catch {
      continue
    }
  }

  log.error('All restart methods failed. Manual intervention required.')
  return false
}

export function getDiagnostics() {
  const diag = {}

  try {
    diag.openclawProcess = execSync("ps aux | grep -i openclaw | grep -v grep", { encoding: 'utf8', timeout: 5000 }).trim()
  } catch {
    diag.openclawProcess = 'NOT FOUND'
  }

  try {
    diag.portListeners = execSync(`ss -tlnp sport = :${CONFIG.openclaw.port} 2>/dev/null || netstat -tlnp 2>/dev/null | grep ${CONFIG.openclaw.port}`, { encoding: 'utf8', timeout: 5000 }).trim()
  } catch {
    diag.portListeners = 'Unable to check'
  }

  try {
    diag.systemMemory = execSync("free -h | head -2", { encoding: 'utf8', timeout: 5000 }).trim()
  } catch {
    diag.systemMemory = 'Unable to check'
  }

  try {
    diag.systemLoad = execSync("uptime", { encoding: 'utf8', timeout: 5000 }).trim()
  } catch {
    diag.systemLoad = 'Unable to check'
  }

  try {
    diag.nodeProcesses = execSync("ps aux | grep node | grep -v grep | wc -l", { encoding: 'utf8', timeout: 5000 }).trim()
  } catch {
    diag.nodeProcesses = 'Unable to check'
  }

  return diag
}
