import { CONFIG } from './config.mjs'
import * as log from './logger.mjs'

export class LatencyProbe {
  constructor(stats) {
    this.stats = stats
  }

  async probeChat() {
    const start = Date.now()
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), CONFIG.thresholds.criticalResponseMs + 5000)

      const res = await fetch(`${CONFIG.openclaw.baseUrl}/api/chat`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(CONFIG.openclaw.token ? { Authorization: `Bearer ${CONFIG.openclaw.token}` } : {}),
        },
        body: JSON.stringify({
          message: 'ping',
          session: 'agent:monitor:healthcheck',
          stream: false,
        }),
      })
      clearTimeout(timeout)

      const latency = Date.now() - start
      this.stats.recordLatency('chat', latency)

      if (latency > CONFIG.thresholds.criticalResponseMs) {
        log.critical(`Chat response CRITICAL: ${latency}ms (threshold: ${CONFIG.thresholds.criticalResponseMs}ms)`)
      } else if (latency > CONFIG.thresholds.chatResponseMs) {
        log.warn(`Chat response SLOW: ${latency}ms (threshold: ${CONFIG.thresholds.chatResponseMs}ms)`)
      } else {
        log.info(`Chat response OK: ${latency}ms`)
      }

      return { ok: res.ok, latency, status: res.status }
    } catch (err) {
      const latency = Date.now() - start
      this.stats.recordLatency('chat', latency, false)
      log.error(`Chat probe failed: ${err.message}`, { latency })
      return { ok: false, latency, error: err.message }
    }
  }

  async probeOverview() {
    const start = Date.now()
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), CONFIG.thresholds.healthCheckMs * 2)

      const res = await fetch(`${CONFIG.openclaw.baseUrl}/overview`, {
        signal: controller.signal,
        headers: CONFIG.openclaw.token ? { Authorization: `Bearer ${CONFIG.openclaw.token}` } : {},
      })
      clearTimeout(timeout)

      const latency = Date.now() - start
      this.stats.recordLatency('overview', latency)
      log.debug(`Overview probe: ${latency}ms (${res.status})`)
      return { ok: res.ok, latency }
    } catch (err) {
      const latency = Date.now() - start
      this.stats.recordLatency('overview', latency, false)
      return { ok: false, latency, error: err.message }
    }
  }

  async probeWebSocket() {
    return new Promise((resolve) => {
      const start = Date.now()
      let resolved = false

      const done = (ok, extra = {}) => {
        if (resolved) return
        resolved = true
        const latency = Date.now() - start
        this.stats.recordLatency('websocket', latency, ok)
        resolve({ ok, latency, ...extra })
      }

      try {
        const wsUrl = `${CONFIG.openclaw.wsUrl}/ws`
        const { default: WebSocket } = await import('ws')
        const ws = new WebSocket(wsUrl, {
          headers: CONFIG.openclaw.token ? { Authorization: `Bearer ${CONFIG.openclaw.token}` } : {},
        })

        const timeout = setTimeout(() => {
          ws.terminate()
          done(false, { error: 'WebSocket connection timeout' })
        }, 5000)

        ws.on('open', () => {
          clearTimeout(timeout)
          const latency = Date.now() - start
          log.debug(`WebSocket connected in ${latency}ms`)
          ws.close()
          done(true)
        })

        ws.on('error', (err) => {
          clearTimeout(timeout)
          done(false, { error: err.message })
        })
      } catch (err) {
        done(false, { error: err.message })
      }
    })
  }
}
