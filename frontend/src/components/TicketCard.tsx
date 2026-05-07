import { Ticket } from '../api/client'
import { PriorityBadge } from './PriorityBadge'

const CHANNEL_ICON: Record<string, string> = {
  email: '✉️',
  sms:   '💬',
  voice: '🎤',
}

const LEFT_BORDER: Record<string, string> = {
  critical: 'border-l-4 border-l-red-500',
  high:     'border-l-4 border-l-orange-400',
  medium:   'border-l-4 border-l-yellow-400',
  low:      'border-l-4 border-l-gray-300',
}

function timeAgo(iso: string): string {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (secs < 60)   return `${secs}s temu`
  if (secs < 3600) return `${Math.floor(secs / 60)} min temu`
  if (secs < 86400) return `${Math.floor(secs / 3600)} godz. temu`
  return `${Math.floor(secs / 86400)} dni temu`
}

interface Props {
  ticket: Ticket
  selected: boolean
  onClick: () => void
}

export function TicketCard({ ticket, selected, onClick }: Props) {
  const priority = ticket.admin_override_priority || ticket.priority
  const rawTitle = ticket.subject || ticket.ai_title || ticket.ai_summary || (ticket.body_raw?.slice(0, 60) ?? '')
  const title = rawTitle ? rawTitle.charAt(0).toUpperCase() + rawTitle.slice(1) : ''
  const showSummaryBelow = !!(ticket.ai_summary && ticket.subject)

  return (
    <div
      onClick={onClick}
      className={`cursor-pointer p-3 rounded-lg mb-2 shadow-sm transition-colors ${LEFT_BORDER[priority]}
        ${selected ? 'bg-blue-50 ring-1 ring-blue-300' : 'bg-white hover:bg-gray-50'}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {/* badges row */}
          <div className="flex items-center gap-1.5 flex-wrap mb-1">
            <PriorityBadge priority={priority} size="xs" />
            {ticket.escalated && (
              <span className="text-[10px] font-semibold bg-amber-100 text-amber-700 border border-amber-300 rounded px-1.5 py-0.5">
                ⚡ auto-eskalowano
              </span>
            )}
            {ticket.confidence != null && ticket.confidence < 0.8 && (
              <span className="text-[10px] font-semibold bg-gray-100 text-gray-500 border border-gray-300 rounded px-1.5 py-0.5">
                ⚠️ niska pewność
              </span>
            )}
          </div>

          {/* title */}
          <p className="font-medium text-gray-900 text-sm truncate">
            {CHANNEL_ICON[ticket.channel] ?? '📩'} {title || '(brak treści)'}
          </p>

          {/* sender */}
          <p className="text-xs text-gray-500 truncate">
            {(ticket.sender ?? 'Nieznany').slice(0, 28)}
          </p>

          {/* AI summary — only when not already used as title */}
          {showSummaryBelow && (
            <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{ticket.ai_summary}</p>
          )}
        </div>

        <span className="text-[10px] text-gray-400 whitespace-nowrap shrink-0 mt-0.5">
          {timeAgo(ticket.created_at)}
        </span>
      </div>
    </div>
  )
}
