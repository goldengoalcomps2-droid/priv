import { useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Bell, Wifi, WifiOff } from 'lucide-react'
import { api } from '../../api/client'

const PAGE_TITLES = {
  '/dashboard':   'Dashboard',
  '/chat':        'Agent Chat',
  '/content':     'Content Feed',
  '/approval':    'Approval Queue',
  '/analytics':   'Analytics',
  '/trends':      'Trend Tracker',
  '/suggestions': 'Suggestions',
  '/reports':     'Strategy Reports',
  '/upload':      'Upload Content',
  '/settings':    'Settings',
}

export default function Header() {
  const location = useLocation()
  const title = PAGE_TITLES[location.pathname] || 'EASTEND'

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: api.getDashboardStats,
    refetchInterval: 60_000,
  })

  const { data: integrations } = useQuery({
    queryKey: ['integrations'],
    queryFn: api.getIntegrations,
  })

  const pendingCount = stats?.pending_approval_count || 0
  const agentActive = integrations ? !integrations.demo_mode : false

  return (
    <header className="bg-white border-b border-charcoal-100 px-6 py-4 flex items-center justify-between flex-shrink-0">
      <div>
        <h1 className="text-lg font-semibold text-charcoal-900">{title}</h1>
      </div>
      <div className="flex items-center gap-3">
        {pendingCount > 0 && (
          <a href="/approval" className="flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-700 text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-amber-100 transition-colors">
            <Bell size={14} />
            {pendingCount} awaiting approval
          </a>
        )}
        <div className="flex items-center gap-1.5 text-xs">
          {agentActive ? (
            <>
              <Wifi size={13} className="text-green-500" />
              <span className="text-green-600 font-medium">Live</span>
            </>
          ) : (
            <>
              <WifiOff size={13} className="text-charcoal-400" />
              <span className="text-charcoal-400">Demo</span>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
