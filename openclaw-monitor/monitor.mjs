#!/usr/bin/env node

import { CONFIG } from './config.mjs'
import { Stats } from './stats.mjs'
import { HealthChecker } from './health.mjs'
import { LatencyProbe } from './latency.mjs'
import { restartOpenClaw, getDiagnostics } from './restart.mjs'
import * as log from './logger.mjs'

const BANNER = `
\x1b[36m╔══════════════════════════════════════════════╗
║       OpenClaw Performance Monitor           ║
║       Watchdog & Latency Tracker             ║
╚══════════════════════════════════════════════╝\x1b[0m`

class OpenClawMonitor {
  constructor() {
    this.stats = new Stats()
    this.health = new HealthChecker(this.stats)
    this.latency = new LatencyProbe(this.stats)
    this.running = false
    this.intervals = []
  }

  async start() {
    console.log(BANNER)
    log.info(`Starting OpenClaw Monitor`)
    log.info(`Target: ${CONFIG.openclaw.baseUrl}`)
    log.info(`Health check interval: ${CONFIG.intervals.healthCheckSec}s`)
    log.info(`Latency probe interval: ${CONFIG.intervals.latencyProbeSec}s`)
    log.info(`Report interval: ${CONFIG.intervals.reportSec}s`)
    log.info(`Slow threshold: ${CONFIG.thresholds.chatResponseMs}ms | Critical: ${CONFIG.thresholds.criticalResponseMs}ms`)
    log.info(`Auto-restart: ${CONFIG.autoRestart ? 'ENABLED' : 'DISABLED'}`)
    console.log('')

    this.running = true

    await this.runHealthCheck()
    await this.runLatencyProbe()

    this.intervals.push(
      setInterval(() => this.runHealthCheck(), CONFIG.intervals.healthCheckSec * 1000)
    )
    this.intervals.push(
      setInterval(() => this.runLatencyProbe(), CONFIG.intervals.latencyProbeSec * 1000)
    )
    this.intervals.push(
      setInterval(() => this.printReport(), CONFIG.intervals.reportSec * 1000)
    )

    process.on('SIGINT', () => this.stop())
    process.on('SIGTERM', () => this.stop())

    log.info('Monitor running. Press Ctrl+C to stop.\n')
  }

  async runHealthCheck() {
    const result = await this.health.check()

    if (this.health.shouldRestart()) {
      log.critical(`${CONFIG.thresholds.maxConsecutiveFailures} consecutive health check failures!`)
      this.printDiagnostics()

      if (CONFIG.autoRestart) {
        const restarted = await restartOpenClaw()
        if (restarted) {
          this.health.consecutiveFailures = 0
          log.info('Waiting for OpenClaw to come back online...')
          await new Promise(r => setTimeout(r, 10_000))
          await this.health.check()
        }
      }
    }
  }

  async runLatencyProbe() {
    await this.latency.probeOverview()
    await this.latency.probeChat()
    await this.latency.probeWebSocket()
  }

  printDiagnostics() {
    log.warn('Running diagnostics...')
    const diag = getDiagnostics()
    console.log('\n\x1b[33m── Diagnostics ──────────────────────────\x1b[0m')
    for (const [key, val] of Object.entries(diag)) {
      console.log(`  \x1b[1m${key}:\x1b[0m ${val}`)
    }
    console.log('\x1b[33m─────────────────────────────────────────\x1b[0m\n')
  }

  printReport() {
    const report = this.stats.getFullReport()
    const bar = (pct) => {
      const filled = Math.round(pct / 5)
      return '\x1b[32m' + '█'.repeat(filled) + '\x1b[90m' + '░'.repeat(20 - filled) + '\x1b[0m'
    }

    console.log(`
\x1b[36m╔══════════════════════════════════════════════╗
║            PERFORMANCE REPORT                ║
╚══════════════════════════════════════════════╝\x1b[0m

  \x1b[1mMonitor Uptime:\x1b[0m    ${report.monitorUptime}
  \x1b[1mTotal Checks:\x1b[0m      ${report.totalChecks} (${report.totalFailures} failures)
  \x1b[1mAvailability:\x1b[0m      ${bar(parseInt(report.availability))} ${report.availability}

  \x1b[1m── Health Endpoint ─────────────────────\x1b[0m
    Avg: ${report.health.avg}ms | P95: ${report.health.p95}ms | Min: ${report.health.min}ms | Max: ${report.health.max}ms
    Success Rate: ${report.health.successRate}% (${report.health.samples} samples)

  \x1b[1m── Chat Latency ────────────────────────\x1b[0m
    Avg: ${report.chatLatency.avg}ms | P95: ${report.chatLatency.p95}ms | Min: ${report.chatLatency.min}ms | Max: ${report.chatLatency.max}ms
    Success Rate: ${report.chatLatency.successRate}% (${report.chatLatency.samples} samples)
    ${report.chatLatency.avg > CONFIG.thresholds.chatResponseMs ? '\x1b[31m⚠ ABOVE SLOW THRESHOLD\x1b[0m' : '\x1b[32m✓ Within acceptable range\x1b[0m'}

  \x1b[1m── WebSocket ───────────────────────────\x1b[0m
    Avg: ${report.wsLatency.avg}ms | P95: ${report.wsLatency.p95}ms
    Success Rate: ${report.wsLatency.successRate}% (${report.wsLatency.samples} samples)

  \x1b[1m── Overview Page ───────────────────────\x1b[0m
    Avg: ${report.overviewLatency.avg}ms | P95: ${report.overviewLatency.p95}ms
    Success Rate: ${report.overviewLatency.successRate}% (${report.overviewLatency.samples} samples)
`)

    if (report.openclawStatus) {
      console.log(`  \x1b[1m── OpenClaw Status ─────────────────────\x1b[0m`)
      for (const [k, v] of Object.entries(report.openclawStatus)) {
        console.log(`    ${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`)
      }
      console.log('')
    }
  }

  stop() {
    if (!this.running) return
    this.running = false
    log.info('Shutting down monitor...')
    this.intervals.forEach(clearInterval)
    this.printReport()
    log.info('Monitor stopped.')
    process.exit(0)
  }
}

const monitor = new OpenClawMonitor()
monitor.start().catch(err => {
  log.critical(`Monitor crashed: ${err.message}`)
  process.exit(1)
})
