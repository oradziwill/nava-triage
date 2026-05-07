import { useState } from 'react'
import { Ticket, TicketTask, updateTicket, resolveTicket, dismissTicket } from '../api/client'
import { PriorityBadge } from '../components/PriorityBadge'

const CHANNEL_ICON: Record<string, string> = { email: '✉️', sms: '💬', voice: '🎤' }

interface Props {
  ticket: Ticket
  onUpdate: (t: Ticket) => void
}

export function TicketDetail({ ticket, onUpdate }: Props) {
  const [draft, setDraft]           = useState(ticket.ai_draft_reply ?? '')
  const [override, setOverride]     = useState(ticket.admin_override_priority ?? '')
  const [notes, setNotes]           = useState(ticket.admin_notes ?? '')
  const [saving, setSaving]         = useState(false)
  const [reasonOpen, setReasonOpen] = useState(false)
  const [newTask, setNewTask]       = useState('')
  const [addingTask, setAddingTask] = useState(false)

  async function addTask() {
    const text = newTask.trim()
    if (!text) return
    setAddingTask(true)
    try {
      const updated = await updateTicket(ticket.id, {
        tasks: [...(ticket.tasks ?? []), { id: crypto.randomUUID(), text, done: false }],
      })
      onUpdate(updated)
      setNewTask('')
    } finally {
      setAddingTask(false)
    }
  }

  const prevPriority = ticket.priority
  const effectivePriority = override || ticket.priority

  async function save() {
    setSaving(true)
    try {
      const updated = await updateTicket(ticket.id, {
        ai_draft_reply: draft,
        admin_notes: notes || undefined,
        admin_override_priority: override || undefined,
      })
      onUpdate(updated)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 h-full overflow-y-auto">

      {/* Header */}
      <div>
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <span className="text-lg">{CHANNEL_ICON[ticket.channel] ?? '📩'}</span>
          <PriorityBadge priority={effectivePriority} />
          <span className="text-xs bg-gray-100 text-gray-600 border border-gray-200 rounded px-2 py-0.5">
            {ticket.category}
          </span>
          {ticket.escalated && (
            <span className="text-xs bg-amber-100 text-amber-700 border border-amber-300 rounded px-2 py-0.5 font-semibold">
              ⚡ auto-eskalowano
            </span>
          )}
          {ticket.confidence != null && (
            <span className={`text-xs rounded px-2 py-0.5 border ${
              ticket.confidence >= 0.8
                ? 'bg-green-50 text-green-700 border-green-200'
                : 'bg-yellow-50 text-yellow-700 border-yellow-200'
            }`}>
              pewność {Math.round(ticket.confidence * 100)}%
            </span>
          )}
        </div>
        <h2 className="text-lg font-semibold text-gray-900 leading-snug">
          {ticket.subject ?? '(brak tematu)'}
        </h2>
        <p className="text-sm text-gray-500 mt-0.5">
          {ticket.sender ?? 'Nieznany'} · {ticket.sender_type} · {ticket.channel}
        </p>
        {override && (
          <p className="text-xs text-orange-600 mt-1 font-medium">
            Zmieniono przez RM: {prevPriority} → {override}
          </p>
        )}
      </div>

      {/* Original message */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">Oryginalna wiadomość</p>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-800 whitespace-pre-wrap max-h-36 overflow-y-auto">
          {ticket.body_raw ?? '(brak treści)'}
        </div>
      </div>

      {/* AI summary */}
      {ticket.ai_summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-blue-600 mb-1">Podsumowanie AI</p>
          <p className="text-sm text-blue-900">{ticket.ai_summary}</p>
        </div>
      )}

      {/* Suggested action */}
      {ticket.ai_suggested_action && (
        <div className="border-l-4 border-blue-400 pl-3 py-1">
          <p className="text-xs font-semibold text-gray-500 mb-0.5">Zalecana akcja</p>
          <p className="text-sm font-medium text-gray-800">{ticket.ai_suggested_action}</p>
        </div>
      )}

      {/* Follow-up signals */}
      {ticket.ai_follow_up_signals && ticket.ai_follow_up_signals.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-amber-700 mb-1">Sygnały follow-up</p>
          <ul className="list-disc list-inside space-y-0.5">
            {ticket.ai_follow_up_signals.map((s, i) => (
              <li key={i} className="text-xs text-amber-800">{s}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing info */}
      {ticket.ai_missing_info && ticket.ai_missing_info.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-3">
          <p className="text-xs font-semibold text-yellow-700 mb-1">⚠️ Brakujące informacje</p>
          <ul className="list-disc list-inside space-y-0.5">
            {ticket.ai_missing_info.map((item, i) => (
              <li key={i} className="text-xs text-yellow-800">{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* AI reasoning — collapsible */}
      {ticket.ai_reasoning && (
        <div>
          <button
            onClick={() => setReasonOpen(o => !o)}
            className="text-xs text-gray-400 hover:text-gray-600 font-medium"
          >
            {reasonOpen ? '▲' : '▼'} Dlaczego taki priorytet?
          </button>
          {reasonOpen && (
            <p className="text-xs text-gray-500 mt-1 pl-2 border-l-2 border-gray-200 leading-relaxed">
              {ticket.ai_reasoning}
            </p>
          )}
        </div>
      )}

      {/* Draft reply */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">Projekt odpowiedzi</p>
        <textarea
          className="w-full border border-gray-300 rounded-lg p-2.5 text-sm text-gray-800 focus:outline-none focus:ring-1 focus:ring-blue-400 min-h-[110px] resize-y"
          value={draft}
          onChange={e => setDraft(e.target.value)}
        />
      </div>

      {/* Admin controls */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">Notatka RM</p>
          <textarea
            className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 min-h-[52px] resize-y"
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Dodaj notatkę..."
          />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">Zmień priorytet</p>
          <select
            className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
            value={override}
            onChange={e => setOverride(e.target.value)}
          >
            <option value="">— bez zmiany —</option>
            <option value="critical">CRITICAL</option>
            <option value="high">HIGH</option>
            <option value="medium">MEDIUM</option>
            <option value="low">LOW</option>
          </select>
        </div>
      </div>

      {/* Tasks */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">Zadania</p>
        {ticket.tasks && ticket.tasks.length > 0 && (
          <ul className="flex flex-col gap-1.5 mb-2">
            {ticket.tasks.map((task: TicketTask) => (
              <li key={task.id} className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={task.done}
                  onChange={async () => {
                    const updated = await updateTicket(ticket.id, {
                      tasks: ticket.tasks!.map(t =>
                        t.id === task.id ? { ...t, done: !t.done } : t
                      ),
                    })
                    onUpdate(updated)
                  }}
                  className="mt-0.5 accent-green-600 cursor-pointer"
                />
                <span className={`text-sm ${task.done ? 'line-through text-gray-400' : 'text-gray-800'}`}>
                  {task.text}
                </span>
              </li>
            ))}
          </ul>
        )}
        <div className="flex gap-2">
          <input
            className="flex-1 border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
            placeholder="Dodaj zadanie..."
            value={newTask}
            onChange={e => setNewTask(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addTask()}
            disabled={addingTask}
          />
          <button
            onClick={addTask}
            disabled={addingTask || !newTask.trim()}
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg border border-gray-300 hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            Dodaj
          </button>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 pb-2">
        <button
          onClick={save}
          disabled={saving}
          className="flex-1 bg-blue-600 text-white text-sm font-semibold py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? 'Zapisuję...' : 'Wyślij odpowiedź'}
        </button>
        <button
          onClick={() => resolveTicket(ticket.id).then(onUpdate)}
          className="flex-1 bg-green-600 text-white text-sm font-semibold py-2 rounded-lg hover:bg-green-700 transition-colors"
        >
          Oznacz jako rozwiązane
        </button>
        <button
          onClick={() => dismissTicket(ticket.id).then(onUpdate)}
          className="px-4 py-2 text-sm text-gray-500 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
        >
          Odrzuć
        </button>
      </div>
    </div>
  )
}
