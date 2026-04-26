#!/usr/bin/env node

import { CONFIG } from './config.mjs'

const BASE = CONFIG.openclaw.baseUrl
const HEADERS = {
  'Content-Type': 'application/json',
  ...(CONFIG.openclaw.token ? { Authorization: `Bearer ${CONFIG.openclaw.token}` } : {}),
}

const C = {
  R: '\x1b[0m', RED: '\x1b[31m', GRN: '\x1b[32m', YEL: '\x1b[33m',
  CYN: '\x1b[36m', DIM: '\x1b[2m', BLD: '\x1b[1m',
}

async function timed(label, fn) {
  const start = Date.now()
  try {
    const result = await fn()
    const ms = Date.now() - start
    const color = ms < 1000 ? C.GRN : ms < 5000 ? C.YEL : C.RED
    const icon = ms < 1000 ? '✓' : ms < 5000 ? '~' : '✗'
    console.log(`  ${color}${icon} ${label}: ${ms}ms${C.R}`)
    return { ok: true, ms, result }
  } catch (err) {
    const ms = Date.now() - start
    console.log(`  ${C.RED}✗ ${label}: FAILED (${ms}ms) — ${err.message}${C.R}`)
    return { ok: false, ms, error: err.message }
  }
}

async function main() {
  console.log(`\n${C.CYN}${C.BLD}OpenClaw Slow Response Diagnostics${C.R}`)
  console.log(`${C.DIM}Target: ${BASE}${C.R}\n`)

  const results = {}

  // 1. Basic connectivity
  console.log(`${C.BLD}1. Connectivity${C.R}`)
  results.health = await timed('Health endpoint', () =>
    fetch(`${BASE}/health`, { headers: HEADERS }).then(r => r.json())
  )
  results.overview = await timed('Overview page', () =>
    fetch(`${BASE}/overview`, { headers: HEADERS }).then(r => r.text())
  )

  // 2. Chat response time (this is what the user experiences)
  console.log(`\n${C.BLD}2. Chat Response Time (3 sequential probes)${C.R}`)
  const chatTimes = []
  for (let i = 1; i <= 3; i++) {
    const r = await timed(`Chat probe #${i}`, () =>
      fetch(`${BASE}/api/chat`, {
        method: 'POST', headers: HEADERS,
        body: JSON.stringify({ message: 'Say hi in under 5 words', session: 'agent:monitor:diag', stream: false }),
      }).then(r => r.json())
    )
    chatTimes.push(r.ms)
  }

  // 3. WebSocket connection
  console.log(`\n${C.BLD}3. WebSocket Connection${C.R}`)
  results.ws = await timed('WebSocket handshake', async () => {
    const { default: WebSocket } = await import('ws')
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(`${CONFIG.openclaw.wsUrl}/ws`, {
        headers: CONFIG.openclaw.token ? { Authorization: `Bearer ${CONFIG.openclaw.token}` } : {},
      })
      const t = setTimeout(() => { ws.terminate(); reject(new Error('Timeout')) }, 5000)
      ws.on('open', () => { clearTimeout(t); ws.close(); resolve(true) })
      ws.on('error', (e) => { clearTimeout(t); reject(e) })
    })
  })

  // 4. System resources
  console.log(`\n${C.BLD}4. System Resources${C.R}`)
  try {
    const { execSync } = await import('child_process')

    const loadAvg = execSync('cat /proc/loadavg', { encoding: 'utf8' }).trim().split(' ')
    const cpuLoad = parseFloat(loadAvg[0])
    const cpuColor = cpuLoad < 2 ? C.GRN : cpuLoad < 4 ? C.YEL : C.RED
    console.log(`  ${cpuColor}${cpuLoad < 2 ? '✓' : '~'} CPU load: ${loadAvg.slice(0, 3).join(' ')}${C.R}`)

    const memInfo = execSync('free -m', { encoding: 'utf8' })
    const memLine = memInfo.split('\n')[1].split(/\s+/)
    const totalMem = parseInt(memLine[1])
    const usedMem = parseInt(memLine[2])
    const memPct = Math.round((usedMem / totalMem) * 100)
    const memColor = memPct < 70 ? C.GRN : memPct < 85 ? C.YEL : C.RED
    console.log(`  ${memColor}${memPct < 85 ? '✓' : '✗'} Memory: ${usedMem}MB / ${totalMem}MB (${memPct}%)${C.R}`)

    try {
      const nodeProcs = execSync("ps aux | grep -E 'node|openclaw' | grep -v grep", { encoding: 'utf8' })
      const lines = nodeProcs.trim().split('\n')
      console.log(`  ${C.DIM}  Node/OpenClaw processes: ${lines.length}${C.R}`)
      for (const line of lines.slice(0, 5)) {
        const parts = line.split(/\s+/)
        console.log(`  ${C.DIM}    PID ${parts[1]} | CPU ${parts[2]}% | MEM ${parts[3]}% | ${parts.slice(10).join(' ').slice(0, 60)}${C.R}`)
      }
    } catch {}
  } catch (err) {
    console.log(`  ${C.DIM}Could not check system resources: ${err.message}${C.R}`)
  }

  // 5. Diagnosis
  console.log(`\n${C.BLD}${C.CYN}═══ DIAGNOSIS ═══${C.R}\n`)

  const avgChat = chatTimes.reduce((a, b) => a + b, 0) / chatTimes.length
  const issues = []

  if (!results.health?.ok) {
    issues.push({ severity: 'CRITICAL', msg: 'Health endpoint unreachable — OpenClaw may not be running' })
  }

  if (avgChat > 30000) {
    issues.push({ severity: 'CRITICAL', msg: `Average chat response: ${Math.round(avgChat)}ms — likely an LLM backend bottleneck or timeout` })
    issues.push({ severity: 'TIP', msg: 'Check your LLM API key quota and rate limits. Consider switching to a faster model.' })
  } else if (avgChat > 10000) {
    issues.push({ severity: 'HIGH', msg: `Average chat response: ${Math.round(avgChat)}ms — slow LLM responses` })
    issues.push({ severity: 'TIP', msg: 'Try: reduce max_tokens, switch to a smaller/faster model, or enable streaming mode' })
  } else if (avgChat > 5000) {
    issues.push({ severity: 'MEDIUM', msg: `Average chat response: ${Math.round(avgChat)}ms — moderate latency` })
    issues.push({ severity: 'TIP', msg: 'Enable streaming in OpenClaw settings so responses appear incrementally' })
  }

  if (results.health?.ok && results.health.ms > 1000) {
    issues.push({ severity: 'MEDIUM', msg: `Health endpoint slow (${results.health.ms}ms) — possible resource contention` })
  }

  if (!results.ws?.ok) {
    issues.push({ severity: 'HIGH', msg: 'WebSocket connection failed — live features may not work' })
  }

  if (chatTimes.length >= 2 && chatTimes[1] < chatTimes[0] * 0.5) {
    issues.push({ severity: 'INFO', msg: 'First request much slower than subsequent — cold start / model loading detected' })
    issues.push({ severity: 'TIP', msg: 'Keep OpenClaw warm with periodic pings (the monitor does this automatically)' })
  }

  if (issues.length === 0) {
    console.log(`  ${C.GRN}✓ All checks passed — OpenClaw appears healthy and responsive${C.R}`)
  } else {
    for (const issue of issues) {
      const color = issue.severity === 'CRITICAL' ? C.RED
        : issue.severity === 'HIGH' ? C.RED
        : issue.severity === 'MEDIUM' ? C.YEL
        : issue.severity === 'TIP' ? C.CYN
        : C.DIM
      const icon = issue.severity === 'TIP' ? '💡' : issue.severity === 'INFO' ? 'ℹ' : '⚠'
      console.log(`  ${color}${icon} [${issue.severity}] ${issue.msg}${C.R}`)
    }
  }

  console.log(`\n${C.DIM}── Common fixes for slow OpenClaw ──────────────────
  1. Enable streaming:  openclaw config set stream true
  2. Faster model:      openclaw config set model claude-sonnet-4-6
  3. Lower max tokens:  openclaw config set max_tokens 2048
  4. Check API quotas:  openclaw config show | grep api_key
  5. Restart cleanly:   openclaw restart
  6. Run this monitor:  npm start (keeps OpenClaw warm)
──────────────────────────────────────────────────${C.R}\n`)
}

main().catch(err => {
  console.error(`${C.RED}Diagnostics failed: ${err.message}${C.R}`)
  process.exit(1)
})
