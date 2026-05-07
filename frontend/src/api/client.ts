const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8002'

export interface TicketTask {
  id: string
  text: string
  done: boolean
}

export interface Ticket {
  id: number
  created_at: string
  updated_at: string
  channel: string
  sender: string | null
  sender_type: string
  subject: string | null
  body_raw: string | null
  priority: 'critical' | 'high' | 'medium' | 'low'
  category: string
  status: string
  ai_title: string | null
  ai_summary: string | null
  ai_draft_reply: string | null
  ai_reasoning: string | null
  ai_suggested_action: string | null
  ai_missing_info: string[] | null
  ai_follow_up_signals: string[] | null
  confidence: number | null
  admin_override_priority: string | null
  admin_notes: string | null
  tasks: TicketTask[] | null
  follow_up_count: number
  escalated: boolean
  priority_order: number
}

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

export async function getTickets(params?: Record<string, string>): Promise<Ticket[]> {
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''
  return req<Ticket[]>(`/api/tickets${qs}`)
}

export async function getTicket(id: number): Promise<Ticket> {
  return req<Ticket>(`/api/tickets/${id}`)
}

export async function updateTicket(id: number, patch: Partial<Ticket>): Promise<Ticket> {
  return req<Ticket>(`/api/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(patch) })
}

export async function resolveTicket(id: number): Promise<Ticket> {
  return req<Ticket>(`/api/tickets/${id}/resolve`, { method: 'POST' })
}

export async function dismissTicket(id: number): Promise<Ticket> {
  return req<Ticket>(`/api/tickets/${id}/dismiss`, { method: 'POST' })
}

export async function ingestMessage(data: {
  channel: string
  sender: string
  subject?: string
  body: string
}): Promise<unknown> {
  return req('/api/ingest', { method: 'POST', body: JSON.stringify(data) })
}

export interface BriefingStatus {
  ready: boolean
  generated_at: string | null
  ticket_count: number
  is_generating: boolean
  script_preview: string | null
}

export async function getBriefing(): Promise<Blob | null> {
  const res = await fetch(`${BASE}/api/voice/briefing`)
  if (res.status === 202) return null   // still generating
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.blob()
}

export async function getBriefingStatus(): Promise<BriefingStatus> {
  return req<BriefingStatus>('/api/voice/briefing/status')
}

export async function getIntro(): Promise<Blob> {
  const res = await fetch(`${BASE}/api/voice/intro`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.blob()
}

export interface VoiceIntent {
  intent: string
  confidence: number
  summary: string
  entities: Record<string, string | null>
  suggested_ticket: { category: string; priority: string; body: string }
  human_readable: string
}

export interface VoiceInterpretResult {
  transcript: string
  intent: VoiceIntent
  whisper_confidence: number | null
}

export async function interpretVoice(audioBlob: Blob, filename: string): Promise<VoiceInterpretResult> {
  const form = new FormData()
  form.append('audio', audioBlob, filename)
  const res = await fetch(`${BASE}/api/voice/interpret`, { method: 'POST', body: form })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

export type VoiceActionTaken = 'created_ticket' | 'escalated' | 'resolved' | 'note_added' | 'task_added' | 'none'

export interface VoiceCommandResult {
  transcript: string
  intent: VoiceIntent
  action_taken: VoiceActionTaken
  affected_ticket_id: number | null
  confirmation_text: string
  confirmation_audio: string | null  // base64 mp3
}

export async function voiceCommand(
  audioBlob: Blob,
  filename: string,
  contextTicketId?: number | null,
): Promise<VoiceCommandResult> {
  const form = new FormData()
  form.append('audio', audioBlob, filename)
  if (contextTicketId != null) form.append('context_ticket_id', String(contextTicketId))
  const res = await fetch(`${BASE}/api/voice/command`, { method: 'POST', body: form })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}
