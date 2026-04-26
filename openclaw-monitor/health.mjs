import { CONFIG } from './config.mjs'
import * as log from './logger.mjs'

export class HealthChecker {
  constructor(stats) {
    this.stats = stats
    this.consecutiveFailures = 0
  }

  async check() {
    const start = Date.now()
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), CONFIG.thresholds.healthCheckMs)

      const res = await fetch(`${CONFIG.openclaw.baseUrl}/health`, {
        signal: controller.signal,
        headers: CONFIG.openclaw.token ? { Authorization: `Bearer ${CONFIG.openclaw.token}` } : {},
      })
      clearTimeout(timeout)

      const latency = Date.now() - start
      const body = await res.json().catch(() => ({}))

      if (res.ok) {
        this.consecutiveFailures = 0
        this.stats.recordHealth(latency, true, body)
        log.debug(`Health OK (${latency}ms)`, { status: body.status, uptime: body.uptime })
        return { ok: true, latency, body }
      }

      this.consecutiveFailures++
      this.stats.recordHealth(latency, false)
      log.warn(`Health check returned ${res.status}`, { latency, failures: this.consecutiveFailures })
      return { ok: false, latency, status: res.status }
    } catch (err) {
      const latency = Date.now() - start
      this.consecutiveFailures++
      this.stats.recordHealth(latency, false)
      log.error(`Health check failed: ${err.message}`, { latency, failures: this.consecutiveFailures })
      return { ok: false, latency, error: err.message }
    }
  }

  shouldRestart() {
    return this.consecutiveFailures >= CONFIG.thresholds.maxConsecutiveFailures
  }
}
