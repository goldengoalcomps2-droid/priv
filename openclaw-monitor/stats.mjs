import { CONFIG } from './config.mjs'

export class Stats {
  constructor() {
    this.healthHistory = []
    this.latencyHistory = { chat: [], overview: [], websocket: [] }
    this.startTime = Date.now()
    this.totalChecks = 0
    this.totalFailures = 0
    this.lastHealthBody = null
  }

  recordHealth(latencyMs, success, body) {
    this.totalChecks++
    if (!success) this.totalFailures++
    if (body) this.lastHealthBody = body
    this._push(this.healthHistory, { ts: Date.now(), latencyMs, success })
  }

  recordLatency(type, latencyMs, success = true) {
    if (!this.latencyHistory[type]) this.latencyHistory[type] = []
    this._push(this.latencyHistory[type], { ts: Date.now(), latencyMs, success })
  }

  _push(arr, item) {
    arr.push(item)
    if (arr.length > CONFIG.historySize) arr.shift()
  }

  getHealthSummary() {
    const recent = this.healthHistory.slice(-20)
    if (recent.length === 0) return { avg: 0, p95: 0, successRate: 0, samples: 0 }

    const latencies = recent.filter(h => h.success).map(h => h.latencyMs).sort((a, b) => a - b)
    const successes = recent.filter(h => h.success).length

    return {
      avg: latencies.length ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : 0,
      p95: latencies.length ? latencies[Math.floor(latencies.length * 0.95)] : 0,
      min: latencies.length ? latencies[0] : 0,
      max: latencies.length ? latencies[latencies.length - 1] : 0,
      successRate: Math.round((successes / recent.length) * 100),
      samples: recent.length,
    }
  }

  getLatencySummary(type) {
    const recent = (this.latencyHistory[type] || []).slice(-20)
    if (recent.length === 0) return { avg: 0, p95: 0, successRate: 0, samples: 0 }

    const latencies = recent.filter(r => r.success).map(r => r.latencyMs).sort((a, b) => a - b)
    const successes = recent.filter(r => r.success).length

    return {
      avg: latencies.length ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : 0,
      p95: latencies.length ? latencies[Math.floor(latencies.length * 0.95)] : 0,
      min: latencies.length ? latencies[0] : 0,
      max: latencies.length ? latencies[latencies.length - 1] : 0,
      successRate: Math.round((successes / recent.length) * 100),
      samples: recent.length,
    }
  }

  getFullReport() {
    const uptime = Math.round((Date.now() - this.startTime) / 1000)
    return {
      monitorUptime: `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m ${uptime % 60}s`,
      totalChecks: this.totalChecks,
      totalFailures: this.totalFailures,
      availability: this.totalChecks ? `${Math.round(((this.totalChecks - this.totalFailures) / this.totalChecks) * 100)}%` : 'N/A',
      health: this.getHealthSummary(),
      chatLatency: this.getLatencySummary('chat'),
      overviewLatency: this.getLatencySummary('overview'),
      wsLatency: this.getLatencySummary('websocket'),
      openclawStatus: this.lastHealthBody,
    }
  }
}
