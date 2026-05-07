import { useState, useRef, useEffect } from 'react'
import { voiceCommand, VoiceCommandResult } from '../api/client'

interface Props {
  contextTicketId?: number | null
  onCommandExecuted: (result: VoiceCommandResult) => void
}

type State = 'idle' | 'recording' | 'processing' | 'error'

function fmt(s: number) {
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

function playBase64Audio(b64: string) {
  const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0))
  const blob = new Blob([bytes], { type: 'audio/mpeg' })
  const url = URL.createObjectURL(blob)
  const audio = new Audio(url)
  audio.onended = () => URL.revokeObjectURL(url)
  audio.play().catch(() => URL.revokeObjectURL(url))
}

export function VoiceInput({ contextTicketId, onCommandExecuted }: Props) {
  const [state, setState] = useState<State>('idle')
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const recorderRef  = useRef<MediaRecorder | null>(null)
  const chunksRef    = useRef<Blob[]>([])
  const timerRef     = useRef<ReturnType<typeof setInterval> | null>(null)
  const autoStopRef  = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => () => {
    timerRef.current    && clearInterval(timerRef.current)
    autoStopRef.current && clearTimeout(autoStopRef.current)
  }, [])

  async function startRecording() {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      const recorder = new MediaRecorder(stream, { mimeType })
      chunksRef.current = []

      recorder.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(chunksRef.current, { type: mimeType })
        const ext  = mimeType.includes('webm') ? 'webm' : 'mp4'
        setState('processing')
        try {
          const result = await voiceCommand(blob, `recording.${ext}`, contextTicketId)
          if (result.confirmation_audio) {
            playBase64Audio(result.confirmation_audio)
          }
          onCommandExecuted(result)
          setState('idle')
        } catch (e) {
          setError(e instanceof Error ? e.message : String(e))
          setState('error')
        }
      }

      recorder.start()
      recorderRef.current = recorder
      setState('recording')
      setElapsed(0)
      timerRef.current    = setInterval(() => setElapsed(n => n + 1), 1000)
      autoStopRef.current = setTimeout(() => stopRecording(), 30_000)
    } catch {
      setError('Brak dostępu do mikrofonu. Sprawdź uprawnienia w przeglądarce.')
      setState('error')
    }
  }

  function stopRecording() {
    timerRef.current    && clearInterval(timerRef.current)
    autoStopRef.current && clearTimeout(autoStopRef.current)
    timerRef.current = autoStopRef.current = null
    recorderRef.current?.stop()
    recorderRef.current = null
  }

  function handleClick() {
    if (state === 'recording') stopRecording()
    else startRecording()
  }

  return (
    <div className="flex flex-col items-end">
      <button
        onClick={handleClick}
        disabled={state === 'processing'}
        className={`text-xs px-3 py-1.5 rounded-lg font-medium border transition-colors disabled:opacity-50
          ${state === 'recording'
            ? 'bg-red-50 text-red-700 border-red-300 hover:bg-red-100'
            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50'
          }`}
      >
        {state === 'idle'       && '🎤 Dyktuj'}
        {state === 'processing' && '⏺ Przetwarzam...'}
        {state === 'error'      && '🎤 Spróbuj ponownie'}
        {state === 'recording'  && (
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse inline-block" />
            Nagrywam... {fmt(elapsed)}
          </span>
        )}
      </button>
      {error && state !== 'recording' && (
        <p className="text-xs text-red-500 mt-1 max-w-[220px] text-right">{error}</p>
      )}
    </div>
  )
}
