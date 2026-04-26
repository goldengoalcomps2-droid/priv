import { appendFileSync } from 'fs'
import { CONFIG } from './config.mjs'

const LEVELS = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3, CRITICAL: 4 }
const COLORS = {
  DEBUG: '\x1b[90m',
  INFO: '\x1b[36m',
  WARN: '\x1b[33m',
  ERROR: '\x1b[31m',
  CRITICAL: '\x1b[41m\x1b[37m',
  RESET: '\x1b[0m',
  DIM: '\x1b[2m',
  BOLD: '\x1b[1m',
}

const minLevel = LEVELS[process.env.LOG_LEVEL?.toUpperCase()] ?? LEVELS.INFO

function ts() {
  return new Date().toISOString()
}

export function log(level, msg, data) {
  if (LEVELS[level] < minLevel) return
  const line = `[${ts()}] ${level.padEnd(8)} ${msg}`
  const color = COLORS[level] || ''

  console.log(`${color}${line}${COLORS.RESET}${data ? ` ${COLORS.DIM}${JSON.stringify(data)}${COLORS.RESET}` : ''}`)

  try {
    appendFileSync(CONFIG.logFile, `${line}${data ? ' ' + JSON.stringify(data) : ''}\n`)
  } catch {}
}

export const debug = (msg, data) => log('DEBUG', msg, data)
export const info = (msg, data) => log('INFO', msg, data)
export const warn = (msg, data) => log('WARN', msg, data)
export const error = (msg, data) => log('ERROR', msg, data)
export const critical = (msg, data) => log('CRITICAL', msg, data)
