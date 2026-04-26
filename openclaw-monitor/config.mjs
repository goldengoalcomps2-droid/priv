export const CONFIG = {
  openclaw: {
    host: process.env.OPENCLAW_HOST || '127.0.0.1',
    port: parseInt(process.env.OPENCLAW_PORT || '18789'),
    get baseUrl() { return `http://${this.host}:${this.port}` },
    get wsUrl() { return `ws://${this.host}:${this.port}` },
    token: process.env.OPENCLAW_TOKEN || '',
  },

  thresholds: {
    healthCheckMs: 2000,
    chatResponseMs: parseInt(process.env.SLOW_THRESHOLD_MS || '10000'),
    criticalResponseMs: parseInt(process.env.CRITICAL_THRESHOLD_MS || '30000'),
    maxConsecutiveFailures: 3,
    memoryWarningPct: 85,
  },

  intervals: {
    healthCheckSec: parseInt(process.env.HEALTH_INTERVAL || '15'),
    latencyProbeSec: parseInt(process.env.LATENCY_INTERVAL || '60'),
    reportSec: parseInt(process.env.REPORT_INTERVAL || '300'),
    wsReconnectSec: 5,
  },

  autoRestart: process.env.AUTO_RESTART !== 'false',
  logFile: process.env.LOG_FILE || './openclaw-monitor.log',
  historySize: 100,
}
