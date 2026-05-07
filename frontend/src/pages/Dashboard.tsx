import { useEffect, useState, useCallback, useRef } from 'react'
import { Ticket, VoiceCommandResult, getTicket, getTickets, ingestMessage } from '../api/client'
import { TicketCard } from '../components/TicketCard'
import { TicketDetail } from './TicketDetail'
import { VoiceBriefing } from '../components/VoiceBriefing'
import { VoiceInput } from '../components/VoiceInput'

const PRIORITIES = ['', 'critical', 'high', 'medium', 'low']
const CATEGORIES = ['', 'security', 'maintenance', 'billing', 'complaint', 'board', 'vendor', 'other']

export function Dashboard() {
  const [tickets, setTickets]   = useState<Ticket[]>([])
  const [selected, setSelected] = useState<Ticket | null>(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState<string | null>(null)

  const [activeTab,      setActiveTab]      = useState<'active' | 'resolved'>('active')
  const [filterPriority, setFilterPriority] = useState('')
  const [filterCategory, setFilterCategory] = useState('')

  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm]           = useState({ sender: '', subject: '', body: '', channel: 'email' })
  const [ingesting, setIngesting] = useState(false)

  const [toast, setToast] = useState<string | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setTickets(await getTickets())
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  function showToast(msg: string) {
    setToast(msg)
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3000)
  }

  function handleUpdate(updated: Ticket) {
    if (updated.status === 'dismissed') {
      setTickets(prev => prev.filter(t => t.id !== updated.id))
      setSelected(null)
    } else {
      setTickets(prev => prev.map(t => t.id === updated.id ? updated : t))
      setSelected(updated)
      if (updated.status === 'resolved') {
        setActiveTab('resolved')
      }
    }
  }

  async function handleCommandExecuted(result: VoiceCommandResult) {
    showToast(result.confirmation_text)

    if (result.action_taken === 'created_ticket') {
      await load()
    } else if (
      result.affected_ticket_id != null &&
      (result.action_taken === 'escalated' || result.action_taken === 'resolved' || result.action_taken === 'note_added' || result.action_taken === 'task_added')
    ) {
      try {
        const updated = await getTicket(result.affected_ticket_id)
        setTickets(prev => prev.map(t => t.id === updated.id ? updated : t))
        if (selected?.id === updated.id) setSelected(updated)
      } catch {}
    }
  }

  async function handleIngest() {
    if (!form.body.trim() || !form.sender.trim()) return
    setIngesting(true)
    try {
      await ingestMessage({ channel: form.channel, sender: form.sender, subject: form.subject || undefined, body: form.body })
      setForm({ sender: '', subject: '', body: '', channel: 'email' })
      setModalOpen(false)
      await load()
    } finally {
      setIngesting(false)
    }
  }

  const activeTickets: Ticket[]   = []
  const resolvedTickets: Ticket[] = []
  const counts = { critical: 0, high: 0 }
  for (const t of tickets) {
    if (t.status === 'resolved') {
      resolvedTickets.push(t)
    } else if (t.status !== 'dismissed') {
      activeTickets.push(t)
      const p = t.admin_override_priority || t.priority
      if (p === 'critical') counts.critical++
      else if (p === 'high') counts.high++
    }
  }

  const displayedTickets = (activeTab === 'active' ? activeTickets : resolvedTickets).filter(t => {
    if (filterPriority && (t.admin_override_priority || t.priority) !== filterPriority) return false
    if (filterCategory && t.category !== filterCategory) return false
    return true
  })

  return (
    <div className="flex flex-col h-screen bg-gray-100">

      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-2.5 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <h1 className="text-base font-bold text-gray-900 tracking-tight">Nava AI Triage</h1>
          {counts.critical > 0 && (
            <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {counts.critical} kryt.
            </span>
          )}
          {counts.high > 0 && (
            <span className="bg-orange-400 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {counts.high} wys.
            </span>
          )}
        </div>
        <div className="flex items-start gap-2">
          <VoiceBriefing />
          <VoiceInput
            contextTicketId={selected?.id ?? null}
            onCommandExecuted={handleCommandExecuted}
          />
          <button
            onClick={load}
            className="text-xs text-gray-500 hover:text-gray-700 px-2.5 py-1.5 rounded border border-gray-200 hover:border-gray-300 transition-colors"
          >
            Odśwież
          </button>
          <button
            onClick={() => setModalOpen(true)}
            className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            + Nowe
          </button>
        </div>
      </header>

      {/* Filters */}
      <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center gap-2 text-sm flex-wrap">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide mr-1">Filtry:</span>
        {[
          { label: 'Priorytet', value: filterPriority, set: setFilterPriority, options: PRIORITIES },
          { label: 'Kategoria', value: filterCategory, set: setFilterCategory, options: CATEGORIES },
        ].map(({ label, value, set, options }) => (
          <select
            key={label}
            className="border border-gray-200 rounded px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-300"
            value={value}
            onChange={e => set(e.target.value)}
          >
            <option value="">{label}: wszystkie</option>
            {options.filter(Boolean).map((o: string) => <option key={o} value={o}>{o}</option>)}
          </select>
        ))}
        <span className="ml-auto text-xs text-gray-400">{displayedTickets.length} zgłoszeń</span>
      </div>

      {/* Main */}
      <div className="flex flex-1 overflow-hidden">
        <div className="w-72 flex-shrink-0 flex flex-col border-r border-gray-200 bg-gray-50">

          {/* Tabs */}
          <div className="flex border-b border-gray-200 bg-white">
            <button
              onClick={() => { setActiveTab('active'); setSelected(null) }}
              className={`flex-1 text-xs font-semibold py-2 transition-colors ${
                activeTab === 'active'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Aktywne
              {activeTickets.length > 0 && (
                <span className="ml-1.5 bg-gray-100 text-gray-600 rounded-full px-1.5 py-0.5 text-xs">
                  {activeTickets.length}
                </span>
              )}
            </button>
            <button
              onClick={() => { setActiveTab('resolved'); setSelected(null) }}
              className={`flex-1 text-xs font-semibold py-2 transition-colors ${
                activeTab === 'resolved'
                  ? 'text-green-600 border-b-2 border-green-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Rozwiązane
              {resolvedTickets.length > 0 && (
                <span className="ml-1.5 bg-gray-100 text-gray-600 rounded-full px-1.5 py-0.5 text-xs">
                  {resolvedTickets.length}
                </span>
              )}
            </button>
          </div>

          {/* Ticket list */}
          <div className="flex-1 overflow-y-auto p-3">
            {loading && <p className="text-sm text-gray-400 text-center mt-10">Ładowanie...</p>}
            {error   && <p className="text-sm text-red-400 text-center mt-10">{error}</p>}
            {!loading && !error && displayedTickets.length === 0 && (
              <p className="text-sm text-gray-400 text-center mt-10">Brak zgłoszeń</p>
            )}
            {displayedTickets.map(t => (
              <TicketCard key={t.id} ticket={t} selected={selected?.id === t.id} onClick={() => setSelected(t)} />
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {selected
            ? <TicketDetail key={selected.id} ticket={selected} onUpdate={handleUpdate} />
            : <div className="flex items-center justify-center h-full text-gray-400 text-sm">Wybierz zgłoszenie z listy</div>
          }
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 bg-gray-900 text-white text-sm px-4 py-2.5 rounded-xl shadow-lg max-w-sm text-center">
          {toast}
        </div>
      )}

      {/* Ingest modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md">
            <h3 className="font-bold text-gray-900 mb-4">Nowe zgłoszenie</h3>
            <div className="flex flex-col gap-3">
              <div className="flex gap-2">
                <select
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
                  value={form.channel}
                  onChange={e => setForm(f => ({ ...f, channel: e.target.value }))}
                >
                  <option value="email">✉️ email</option>
                  <option value="sms">💬 sms</option>
                  <option value="voice">🎤 voice</option>
                </select>
                <input
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
                  placeholder="Nadawca"
                  value={form.sender}
                  onChange={e => setForm(f => ({ ...f, sender: e.target.value }))}
                />
              </div>
              <input
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
                placeholder="Temat (opcjonalny)"
                value={form.subject}
                onChange={e => setForm(f => ({ ...f, subject: e.target.value }))}
              />
              <textarea
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 min-h-[120px]"
                placeholder="Treść..."
                value={form.body}
                onChange={e => setForm(f => ({ ...f, body: e.target.value }))}
              />
            </div>
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleIngest}
                disabled={ingesting || !form.body.trim() || !form.sender.trim()}
                className="flex-1 bg-blue-600 text-white text-sm font-semibold py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {ingesting ? 'Triaż AI...' : 'Wyślij do triażu'}
              </button>
              <button
                onClick={() => setModalOpen(false)}
                className="px-4 py-2 text-sm text-gray-600 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                Anuluj
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
