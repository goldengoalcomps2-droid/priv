#!/usr/bin/env node

/**
 * OpenClaw Auto-Diagnose & Fix
 * Reads your actual config, finds the bottlenecks, and patches them.
 * Run: node fix-openclaw.mjs
 * Dry run: node fix-openclaw.mjs --dry-run
 */

import { readFileSync, writeFileSync, existsSync, copyFileSync } from 'fs'
import { execSync } from 'child_process'
import { homedir } from 'os'
import { join } from 'path'

const DRY_RUN = process.argv.includes('--dry-run')
const VERBOSE = process.argv.includes('--verbose')

const C = {
  R: '\x1b[0m', RED: '\x1b[31m', GRN: '\x1b[32m', YEL: '\x1b[33m',
  CYN: '\x1b[36m', DIM: '\x1b[2m', BLD: '\x1b[1m', MAG: '\x1b[35m',
}

const CONFIG_PATH = process.env.OPENCLAW_CONFIG_PATH || join(homedir(), '.openclaw', 'openclaw.json')
const STATE_DIR = join(homedir(), '.openclaw')

console.log(`
${C.CYN}${C.BLD}╔══════════════════════════════════════════════════╗
║     OpenClaw Auto-Diagnose & Fix                 ║
║     Finds the real bottlenecks and patches them   ║
╚══════════════════════════════════════════════════╝${C.R}
`)

// ─── Helpers ────────────────────────────────────────────────────────────────

function info(msg) { console.log(`  ${C.CYN}ℹ${C.R} ${msg}`) }
function good(msg) { console.log(`  ${C.GRN}✓${C.R} ${msg}`) }
function warn(msg) { console.log(`  ${C.YEL}⚠${C.R} ${msg}`) }
function bad(msg) { console.log(`  ${C.RED}✗${C.R} ${msg}`) }
function fix(msg) { console.log(`  ${C.MAG}→ FIX:${C.R} ${msg}`) }
function section(msg) { console.log(`\n${C.BLD}${msg}${C.R}`) }

function shell(cmd, fallback = null) {
  try { return execSync(cmd, { encoding: 'utf8', timeout: 10000 }).trim() }
  catch { return fallback }
}

function deepGet(obj, path) {
  return path.split('.').reduce((o, k) => o?.[k], obj)
}

function deepSet(obj, path, value) {
  const keys = path.split('.')
  let current = obj
  for (let i = 0; i < keys.length - 1; i++) {
    if (!current[keys[i]] || typeof current[keys[i]] !== 'object') {
      current[keys[i]] = {}
    }
    current = current[keys[i]]
  }
  current[keys[keys.length - 1]] = value
}

// ─── Load Config ────────────────────────────────────────────────────────────

section('1. Loading Configuration')

let config = {}
let configRaw = ''

if (!existsSync(CONFIG_PATH)) {
  bad(`Config not found at ${CONFIG_PATH}`)
  info('Creating default config...')
  config = {}
} else {
  configRaw = readFileSync(CONFIG_PATH, 'utf8')
  try {
    const cleaned = configRaw
      .replace(/\/\/.*$/gm, '')
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .replace(/,\s*([}\]])/g, '$1')
    config = JSON.parse(cleaned)
    good(`Loaded config from ${CONFIG_PATH}`)
  } catch (err) {
    bad(`Failed to parse config: ${err.message}`)
    info('Attempting to read with openclaw CLI...')
    const cliDump = shell('openclaw config export 2>/dev/null')
    if (cliDump) {
      try { config = JSON.parse(cliDump); good('Loaded via CLI export') }
      catch { bad('CLI export also failed. Starting with empty config.') }
    }
  }
}

if (VERBOSE) {
  console.log(`${C.DIM}  Current config keys: ${Object.keys(config).join(', ') || '(empty)'}${C.R}`)
}

// ─── Collect System Info ────────────────────────────────────────────────────

section('2. System Health Check')

const issues = []
const fixes = []

const totalMemMB = (() => {
  const meminfo = shell('cat /proc/meminfo 2>/dev/null')
  if (!meminfo) return null
  const match = meminfo.match(/MemTotal:\s+(\d+)/)
  return match ? Math.round(parseInt(match[1]) / 1024) : null
})()

const availMemMB = (() => {
  const meminfo = shell('cat /proc/meminfo 2>/dev/null')
  if (!meminfo) return null
  const match = meminfo.match(/MemAvailable:\s+(\d+)/)
  return match ? Math.round(parseInt(match[1]) / 1024) : null
})()

const loadAvg = shell('cat /proc/loadavg 2>/dev/null')?.split(' ').slice(0, 3).map(Number)
const cpuCount = parseInt(shell('nproc 2>/dev/null') || '0')

if (totalMemMB) {
  if (totalMemMB < 2048) {
    bad(`RAM: ${totalMemMB}MB — critically low (min 2GB, recommended 4GB+)`)
    issues.push({ severity: 'CRITICAL', area: 'system', msg: `Only ${totalMemMB}MB RAM — OOM kills likely` })
  } else if (totalMemMB < 4096) {
    warn(`RAM: ${totalMemMB}MB — below recommended 4GB`)
    issues.push({ severity: 'HIGH', area: 'system', msg: `${totalMemMB}MB RAM — tight for OpenClaw + LLM overhead` })
  } else {
    good(`RAM: ${totalMemMB}MB`)
  }

  if (availMemMB && availMemMB < 512) {
    bad(`Available RAM: ${availMemMB}MB — system is memory-starved`)
    issues.push({ severity: 'CRITICAL', area: 'system', msg: `Only ${availMemMB}MB available RAM` })
  }
}

if (loadAvg && cpuCount) {
  const load1m = loadAvg[0]
  if (load1m > cpuCount * 2) {
    bad(`CPU load: ${loadAvg.join(' ')} (${cpuCount} cores) — system overloaded`)
    issues.push({ severity: 'HIGH', area: 'system', msg: `CPU load ${load1m} with ${cpuCount} cores` })
  } else if (load1m > cpuCount) {
    warn(`CPU load: ${loadAvg.join(' ')} (${cpuCount} cores) — elevated`)
  } else {
    good(`CPU load: ${loadAvg.join(' ')} (${cpuCount} cores)`)
  }
}

const swapTotal = (() => {
  const meminfo = shell('cat /proc/meminfo 2>/dev/null')
  if (!meminfo) return null
  const match = meminfo.match(/SwapTotal:\s+(\d+)/)
  return match ? Math.round(parseInt(match[1]) / 1024) : null
})()

if (swapTotal !== null && swapTotal === 0 && totalMemMB && totalMemMB < 4096) {
  warn('No swap configured — increases OOM risk on low-memory systems')
  issues.push({ severity: 'MEDIUM', area: 'system', msg: 'No swap space configured' })
}

// ─── Check OpenClaw Process ────────────────────────────────────────────────

section('3. OpenClaw Process')

const openclawProcs = shell("ps aux | grep -E '[o]penclaw|[n]ode.*gateway' | grep -v 'fix-openclaw'")
if (openclawProcs) {
  good('OpenClaw process found')
  if (VERBOSE) console.log(`${C.DIM}${openclawProcs}${C.R}`)

  const nodeMemLines = shell("ps -eo pid,rss,comm | grep -E 'node|openclaw' | grep -v grep")
  if (nodeMemLines) {
    const totalNodeMB = nodeMemLines.split('\n')
      .map(l => parseInt(l.trim().split(/\s+/)[1] || '0'))
      .reduce((a, b) => a + b, 0) / 1024
    if (totalNodeMB > 1024) {
      bad(`Node processes using ${Math.round(totalNodeMB)}MB — memory bloat`)
      issues.push({ severity: 'HIGH', area: 'process', msg: `Node using ${Math.round(totalNodeMB)}MB RAM` })
    } else if (totalNodeMB > 512) {
      warn(`Node processes using ${Math.round(totalNodeMB)}MB`)
    } else {
      good(`Node memory usage: ${Math.round(totalNodeMB)}MB`)
    }
  }
} else {
  bad('No OpenClaw process found — gateway may not be running')
  issues.push({ severity: 'CRITICAL', area: 'process', msg: 'OpenClaw gateway not running' })
}

// ─── Check Port ─────────────────────────────────────────────────────────────

const configPort = deepGet(config, 'gateway.port') || 18789
const portCheck = shell(`ss -tlnp sport = :${configPort} 2>/dev/null`) ||
                  shell(`netstat -tlnp 2>/dev/null | grep :${configPort}`)
if (portCheck && portCheck.includes(String(configPort))) {
  good(`Port ${configPort} is listening`)
} else {
  bad(`Port ${configPort} not listening`)
  issues.push({ severity: 'CRITICAL', area: 'network', msg: `Port ${configPort} not bound` })
}

// ─── Network Latency to LLM Provider ───────────────────────────────────────

section('4. LLM Provider Latency')

async function pingProvider(name, url) {
  const start = Date.now()
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 10000)
    await fetch(url, { method: 'HEAD', signal: controller.signal })
    clearTimeout(timeout)
    return Date.now() - start
  } catch {
    return Date.now() - start
  }
}

const providerLatencies = {}
const providers = [
  ['Anthropic', 'https://api.anthropic.com'],
  ['OpenAI', 'https://api.openai.com'],
  ['OpenRouter', 'https://openrouter.ai'],
]

for (const [name, url] of providers) {
  const latency = await pingProvider(name, url)
  providerLatencies[name] = latency
  const color = latency < 200 ? C.GRN : latency < 500 ? C.YEL : C.RED
  console.log(`  ${color}${latency < 500 ? '✓' : '⚠'} ${name}: ${latency}ms round-trip${C.R}`)
  if (latency > 500) {
    issues.push({ severity: 'MEDIUM', area: 'network', msg: `${name} API latency: ${latency}ms` })
  }
}

// ─── Analyze Config for Performance Issues ──────────────────────────────────

section('5. Configuration Analysis')

// 5a. Model choice
const currentModel = deepGet(config, 'agents.defaults.model')
if (currentModel) {
  info(`Current model: ${currentModel}`)
  const slowModels = ['opus', 'o1', 'o3', 'gpt-5.4']
  const isSlowModel = slowModels.some(m => currentModel.toLowerCase().includes(m))
  if (isSlowModel) {
    warn(`Model "${currentModel}" is a reasoning/large model — inherently slow`)
    issues.push({
      severity: 'HIGH', area: 'model',
      msg: `Using slow model: ${currentModel}`,
      fix: 'agents.defaults.model',
      value: 'anthropic/claude-sonnet-4-6',
      desc: 'Switch to Sonnet for faster responses (keeps high quality)',
    })
  } else {
    good(`Model "${currentModel}" is a good speed choice`)
  }
} else {
  warn('No default model set — OpenClaw picks one automatically (may be slow)')
  issues.push({
    severity: 'MEDIUM', area: 'model',
    msg: 'No explicit model configured',
    fix: 'agents.defaults.model',
    value: 'anthropic/claude-sonnet-4-6',
    desc: 'Pin a fast model to avoid slow auto-selection',
  })
}

// 5b. Streaming
const acpStreamMode = deepGet(config, 'acp.stream.deliveryMode')
if (acpStreamMode === 'final_only') {
  bad('Streaming is set to "final_only" — you wait for the entire response before seeing anything')
  issues.push({
    severity: 'HIGH', area: 'streaming',
    msg: 'ACP stream delivery mode is "final_only"',
    fix: 'acp.stream.deliveryMode',
    value: 'live',
    desc: 'Enable live streaming so responses appear word-by-word',
  })
} else if (acpStreamMode === 'live') {
  good('ACP streaming: live mode')
} else {
  info('ACP stream delivery mode not set (checking defaults...)')
}

const streamCoalesce = deepGet(config, 'acp.stream.coalesceIdleMs')
if (streamCoalesce && streamCoalesce > 200) {
  warn(`Stream coalesce delay: ${streamCoalesce}ms — adds perceived latency`)
  issues.push({
    severity: 'MEDIUM', area: 'streaming',
    msg: `Stream coalesce at ${streamCoalesce}ms delays visible output`,
    fix: 'acp.stream.coalesceIdleMs',
    value: 50,
    desc: 'Lower coalesce window for snappier streaming',
  })
}

// 5c. MCP session idle TTL
const mcpIdleTtl = deepGet(config, 'mcp.sessionIdleTtlMs')
if (mcpIdleTtl !== undefined && mcpIdleTtl < 300000) {
  warn(`MCP idle TTL: ${mcpIdleTtl}ms — sessions expire quickly, causing cold restarts`)
  issues.push({
    severity: 'MEDIUM', area: 'mcp',
    msg: `MCP session idle TTL too low (${mcpIdleTtl}ms)`,
    fix: 'mcp.sessionIdleTtlMs',
    value: 600000,
    desc: 'Increase to 10 minutes to reduce cold-start reconnections',
  })
} else {
  good(`MCP idle TTL: ${mcpIdleTtl || 600000}ms (default 10min)`)
}

// 5d. Browser (resource hog if unused)
const browserEnabled = deepGet(config, 'browser.enabled')
if (browserEnabled !== false) {
  const browserProcs = shell("ps aux | grep -E '[c]hrome|[c]hromium' | wc -l")
  const browserCount = parseInt(browserProcs || '0')
  if (browserCount > 0) {
    warn(`Browser enabled with ${browserCount} Chrome processes — uses significant RAM`)
    issues.push({
      severity: 'MEDIUM', area: 'browser',
      msg: `Browser enabled (${browserCount} Chrome processes consuming RAM)`,
      fix: 'browser.enabled',
      value: false,
      desc: 'Disable browser if you don\'t need web browsing — saves 200-500MB RAM',
    })
  } else {
    info('Browser enabled but no Chrome processes running')
  }
}

// 5e. Logging level
const logLevel = deepGet(config, 'logging.level')
if (logLevel === 'debug' || logLevel === 'trace') {
  warn(`Log level: "${logLevel}" — verbose logging slows everything down`)
  issues.push({
    severity: 'MEDIUM', area: 'logging',
    msg: `Debug-level logging active`,
    fix: 'logging.level',
    value: 'warn',
    desc: 'Reduce log level to "warn" for production speed',
  })
} else {
  good(`Log level: ${logLevel || 'info'} (default)`)
}

const consoleLogLevel = deepGet(config, 'logging.consoleLevel')
if (consoleLogLevel === 'debug' || consoleLogLevel === 'trace') {
  issues.push({
    severity: 'LOW', area: 'logging',
    msg: 'Console log level is debug/trace',
    fix: 'logging.consoleLevel',
    value: 'warn',
    desc: 'Reduce console verbosity',
  })
}

// 5f. Diagnostics overhead
const diagOtel = deepGet(config, 'diagnostics.otel.enabled')
if (diagOtel === true) {
  warn('OpenTelemetry export enabled — adds overhead to every request')
  issues.push({
    severity: 'MEDIUM', area: 'diagnostics',
    msg: 'OTel tracing active (adds latency)',
    fix: 'diagnostics.otel.enabled',
    value: false,
    desc: 'Disable OTel export unless you\'re actively debugging',
  })
}

const cacheTrace = deepGet(config, 'diagnostics.cacheTrace.enabled')
if (cacheTrace === true) {
  issues.push({
    severity: 'LOW', area: 'diagnostics',
    msg: 'Cache tracing enabled (disk I/O overhead)',
    fix: 'diagnostics.cacheTrace.enabled',
    value: false,
    desc: 'Disable cache tracing for faster operation',
  })
}

// 5g. Gateway reload mode
const reloadMode = deepGet(config, 'gateway.reload.mode')
if (reloadMode === 'restart') {
  warn('Gateway reload mode is "restart" — config changes cause full restarts')
  issues.push({
    severity: 'LOW', area: 'gateway',
    msg: 'Reload mode "restart" causes downtime on config changes',
    fix: 'gateway.reload.mode',
    value: 'hybrid',
    desc: 'Use hybrid reload for zero-downtime config changes',
  })
}

// 5h. Thinking/reasoning mode
const thinkingMode = deepGet(config, 'agents.defaults.thinking')
if (thinkingMode && thinkingMode !== 'off') {
  warn(`Thinking mode: "${JSON.stringify(thinkingMode)}" — adds seconds to every response`)
  issues.push({
    severity: 'HIGH', area: 'thinking',
    msg: 'Extended thinking/reasoning enabled — major latency source',
    fix: 'agents.defaults.thinking',
    value: 'off',
    desc: 'Disable extended thinking for faster chat responses',
  })
} else if (thinkingMode === 'off') {
  good('Extended thinking: off')
}

// 5i. Max output tokens
const maxOutput = deepGet(config, 'acp.stream.maxOutputChars')
if (maxOutput && maxOutput > 100000) {
  warn(`Max output chars: ${maxOutput} — very large responses take longer`)
  issues.push({
    severity: 'LOW', area: 'tokens',
    msg: `Max output ${maxOutput} chars is very high`,
    fix: 'acp.stream.maxOutputChars',
    value: 50000,
    desc: 'Cap output to reduce tail latency on long responses',
  })
}

// 5j. Cron jobs competing for resources
const cronEnabled = deepGet(config, 'cron.enabled')
const cronMaxConcurrent = deepGet(config, 'cron.maxConcurrentRuns')
if (cronEnabled !== false && cronMaxConcurrent && cronMaxConcurrent > 2) {
  warn(`Cron max concurrent runs: ${cronMaxConcurrent} — background jobs compete with chat`)
  issues.push({
    severity: 'MEDIUM', area: 'cron',
    msg: `${cronMaxConcurrent} concurrent cron jobs can starve chat sessions`,
    fix: 'cron.maxConcurrentRuns',
    value: 1,
    desc: 'Limit cron concurrency so chat gets priority',
  })
}

// 5k. ACP session TTL
const acpTtl = deepGet(config, 'acp.runtime.ttlMinutes')
if (acpTtl && acpTtl < 10) {
  issues.push({
    severity: 'MEDIUM', area: 'sessions',
    msg: `ACP runtime TTL ${acpTtl}min — sessions expire fast, causing cold starts`,
    fix: 'acp.runtime.ttlMinutes',
    value: 30,
    desc: 'Increase session TTL to reduce cold-start delays',
  })
}

// ─── Live Chat Probe ────────────────────────────────────────────────────────

section('6. Live Chat Response Test')

async function probeChatEndpoint() {
  const endpoints = [
    `http://127.0.0.1:${configPort}/api/chat`,
    `http://127.0.0.1:${configPort}/v1/chat/completions`,
  ]

  for (const url of endpoints) {
    const start = Date.now()
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 60000)
      const res = await fetch(url, {
        method: 'POST',
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'Reply with just the word OK',
          session: 'agent:main:fix-diagnostic',
          stream: false,
        }),
      })
      clearTimeout(timeout)
      const latency = Date.now() - start

      if (res.ok || res.status === 401) {
        return { url, latency, status: res.status, ok: res.ok }
      }
    } catch (err) {
      const latency = Date.now() - start
      if (err.name === 'AbortError') {
        return { url, latency, error: 'Timed out after 60s', timeout: true }
      }
    }
  }
  return null
}

const chatProbe = await probeChatEndpoint()
if (chatProbe) {
  if (chatProbe.timeout) {
    bad(`Chat timed out after ${chatProbe.latency}ms — gateway unreachable or LLM unresponsive`)
    issues.push({ severity: 'CRITICAL', area: 'chat', msg: 'Chat endpoint timed out at 60s' })
  } else if (chatProbe.latency > 30000) {
    bad(`Chat response: ${chatProbe.latency}ms — critically slow`)
    issues.push({ severity: 'CRITICAL', area: 'chat', msg: `Chat latency: ${chatProbe.latency}ms` })
  } else if (chatProbe.latency > 10000) {
    warn(`Chat response: ${chatProbe.latency}ms — slow`)
    issues.push({ severity: 'HIGH', area: 'chat', msg: `Chat latency: ${chatProbe.latency}ms` })
  } else if (chatProbe.latency > 5000) {
    warn(`Chat response: ${chatProbe.latency}ms — moderate`)
  } else {
    good(`Chat response: ${chatProbe.latency}ms`)
  }
} else {
  bad('Could not reach any chat endpoint')
  issues.push({ severity: 'CRITICAL', area: 'chat', msg: 'All chat endpoints unreachable' })
}

// ─── Apply Fixes ────────────────────────────────────────────────────────────

section('7. Applying Fixes')

const configFixes = issues.filter(i => i.fix)

if (configFixes.length === 0 && issues.length === 0) {
  good('No issues found — OpenClaw config looks optimal')
  console.log(`\n${C.DIM}If it still feels slow, the bottleneck is likely your LLM provider's API speed.${C.R}`)
} else if (configFixes.length === 0) {
  warn(`Found ${issues.length} issues but none are config-fixable from here`)
  info('Issues are system-level (RAM, CPU) or require manual intervention')
} else {
  console.log(`  Found ${C.BLD}${configFixes.length}${C.R} config issues to fix:\n`)

  for (const issue of configFixes) {
    const current = deepGet(config, issue.fix)
    console.log(`  ${C.YEL}[${issue.severity}]${C.R} ${issue.msg}`)
    console.log(`    ${C.DIM}Current: ${JSON.stringify(current) ?? '(not set)'}${C.R}`)
    console.log(`    ${C.MAG}→ Set ${issue.fix} = ${JSON.stringify(issue.value)}${C.R}`)
    console.log(`    ${C.DIM}${issue.desc}${C.R}\n`)
  }

  if (DRY_RUN) {
    info('DRY RUN — no changes written. Run without --dry-run to apply.\n')
  } else {
    const backupPath = `${CONFIG_PATH}.backup.${Date.now()}`
    if (existsSync(CONFIG_PATH)) {
      copyFileSync(CONFIG_PATH, backupPath)
      good(`Backed up config to ${backupPath}`)
    }

    for (const issue of configFixes) {
      deepSet(config, issue.fix, issue.value)
      fix(`Set ${issue.fix} = ${JSON.stringify(issue.value)}`)
    }

    const output = JSON.stringify(config, null, 2)
    writeFileSync(CONFIG_PATH, output, 'utf8')
    good(`Wrote optimized config to ${CONFIG_PATH}`)

    info('Restarting OpenClaw gateway to apply changes...')
    const restartCmds = [
      'openclaw gateway restart',
      'openclaw restart',
      'systemctl restart openclaw',
    ]

    let restarted = false
    for (const cmd of restartCmds) {
      try {
        const which = shell(`which ${cmd.split(' ')[0]}`)
        if (!which) continue
        console.log(`  ${C.DIM}Trying: ${cmd}${C.R}`)
        execSync(cmd, { timeout: 30000, stdio: 'pipe' })
        good(`Restarted with: ${cmd}`)
        restarted = true
        break
      } catch { continue }
    }

    if (!restarted) {
      warn('Could not auto-restart — please run: openclaw restart')
    }
  }
}

// ─── Summary ────────────────────────────────────────────────────────────────

section('8. Summary')

const bySeverity = { CRITICAL: [], HIGH: [], MEDIUM: [], LOW: [] }
for (const issue of issues) {
  if (bySeverity[issue.severity]) bySeverity[issue.severity].push(issue)
}

if (issues.length === 0) {
  console.log(`\n  ${C.GRN}${C.BLD}All clear — no performance issues detected.${C.R}\n`)
} else {
  console.log('')
  for (const [sev, items] of Object.entries(bySeverity)) {
    if (items.length === 0) continue
    const color = sev === 'CRITICAL' ? C.RED : sev === 'HIGH' ? C.RED : sev === 'MEDIUM' ? C.YEL : C.DIM
    for (const item of items) {
      const fixed = configFixes.includes(item)
      console.log(`  ${color}[${sev}]${C.R} ${item.msg}${fixed ? ` ${C.GRN}← FIXED${C.R}` : ''}`)
    }
  }

  const unfixed = issues.filter(i => !configFixes.includes(i))
  if (unfixed.length > 0) {
    console.log(`\n${C.BLD}  Manual actions needed:${C.R}`)
    for (const issue of unfixed) {
      if (issue.area === 'system' && issue.msg.includes('RAM')) {
        console.log(`  ${C.YEL}→${C.R} Upgrade server RAM to at least 4GB`)
      } else if (issue.area === 'system' && issue.msg.includes('swap')) {
        console.log(`  ${C.YEL}→${C.R} Add swap: sudo fallocate -l 2G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`)
      } else if (issue.area === 'process' && issue.msg.includes('not running')) {
        console.log(`  ${C.YEL}→${C.R} Start OpenClaw: openclaw start`)
      } else if (issue.area === 'process' && issue.msg.includes('memory')) {
        console.log(`  ${C.YEL}→${C.R} Restart to clear memory bloat: openclaw restart`)
      } else if (issue.area === 'network') {
        console.log(`  ${C.YEL}→${C.R} ${issue.msg} — consider a closer region or different provider`)
      } else if (issue.area === 'chat') {
        console.log(`  ${C.YEL}→${C.R} Chat latency is high — check LLM API key quotas and rate limits`)
      }
    }
  }

  const fixedCount = configFixes.length
  console.log(`\n  ${C.BLD}${fixedCount}/${issues.length} issues auto-fixed.${C.R}`)
  if (!DRY_RUN && fixedCount > 0) {
    console.log(`  ${C.GRN}Config has been optimized and gateway restart attempted.${C.R}`)
    console.log(`  ${C.DIM}Original config backed up alongside openclaw.json${C.R}`)
  }
}

console.log('')
