import { useState, useRef, useEffect } from 'react'
import { getBriefing, getBriefingStatus, getIntro } from '../api/client'

class AudioQueue {
  private audios: HTMLAudioElement[] = []
  private urls: string[] = []

  add(blob: Blob) {
    const url = URL.createObjectURL(blob)
    this.urls.push(url)
    this.audios.push(new Audio(url))
  }

  hasItems() { return this.audios.length > 0 }

  play(gapMs = 300, onAllDone?: () => void) {
    this._playAt(0, gapMs, onAllDone)
  }

  private _playAt(index: number, gapMs: number, onAllDone?: () => void) {
    if (index >= this.audios.length) {
      onAllDone?.()
      return
    }
    const audio = this.audios[index]
    audio.onended = () => setTimeout(() => this._playAt(index + 1, gapMs, onAllDone), gapMs)
    audio.play().catch(() => onAllDone?.())
  }

  stop() {
    this.audios.forEach(a => { a.pause(); a.currentTime = 0 })
    this.urls.forEach(url => URL.revokeObjectURL(url))
    this.audios = []
    this.urls = []
  }
}

type PlayState = 'idle' | 'loading' | 'playing-intro' | 'playing-briefing' | 'waiting-cache'

export function VoiceBriefing() {
  const [playState, setPlayState] = useState<PlayState>('idle')
  const [cacheReady, setCacheReady]     = useState(false)
  const [error, setError]               = useState<string | null>(null)
  const queue = useRef(new AudioQueue())
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Poll briefing status every 10s to show the indicator dot
  useEffect(() => {
    const check = async () => {
      try {
        const s = await getBriefingStatus()
        setCacheReady(s.ready)
      } catch {}
    }
    check()
    const id = setInterval(check, 10_000)
    return () => clearInterval(id)
  }, [])

  function stopAll() {
    queue.current.stop()
    queue.current = new AudioQueue()
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
    setPlayState('idle')
  }

  async function handleClick() {
    if (playState !== 'idle') { stopAll(); return }

    setPlayState('loading')
    setError(null)
    queue.current = new AudioQueue()

    try {
      // Fetch intro and briefing cache in parallel
      const [introResult, briefingResult] = await Promise.allSettled([
        getIntro(),
        getBriefing(),
      ])

      if (introResult.status === 'rejected') {
        throw new Error(`Intro: ${introResult.reason}`)
      }

      queue.current.add(introResult.value)

      const briefingBlob = briefingResult.status === 'fulfilled' ? briefingResult.value : null

      if (briefingBlob) {
        queue.current.add(briefingBlob)
        setPlayState('playing-intro')
        queue.current.play(300, () => {
          setPlayState('idle')
          setCacheReady(true)
        })
      } else {
        // Cache not ready — play intro then poll
        setPlayState('playing-intro')
        queue.current.play(300, () => {
          setPlayState('waiting-cache')
          startPollingForBriefing()
        })
      }
    } catch (e) {
      setPlayState('idle')
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  function startPollingForBriefing() {
    pollRef.current = setInterval(async () => {
      try {
        const blob = await getBriefing()
        if (blob) {
          if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
          queue.current = new AudioQueue()
          queue.current.add(blob)
          setPlayState('playing-briefing')
          queue.current.play(0, () => { setPlayState('idle'); setCacheReady(true) })
        }
      } catch {}
    }, 3_000)
  }

  const isPlaying = playState === 'playing-intro' || playState === 'playing-briefing'

  return (
    <div className="flex flex-col items-end">
      <div className="flex items-center gap-1.5">
        {/* Cache status dot */}
        <span
          title={cacheReady ? 'Briefing gotowy' : 'Generuję briefing...'}
          className={`w-2 h-2 rounded-full ${cacheReady ? 'bg-green-400' : 'bg-gray-300 animate-pulse'}`}
        />
        <button
          onClick={handleClick}
          disabled={playState === 'loading'}
          className={`text-xs px-3 py-1.5 rounded-lg font-medium border transition-colors disabled:opacity-50
            ${isPlaying || playState === 'waiting-cache'
              ? 'bg-green-50 text-green-700 border-green-300 hover:bg-green-100'
              : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
        >
          {playState === 'idle'             && '▶ Odsłuchaj briefing'}
          {playState === 'loading'          && 'Ładuję...'}
          {playState === 'playing-intro'    && '⏸ Intro...'}
          {playState === 'playing-briefing' && '⏸ Briefing...'}
          {playState === 'waiting-cache'    && '⏸ Szczegółowy briefing...'}
        </button>
      </div>
      {error && <p className="text-xs text-red-500 mt-1 text-right max-w-[240px]">{error}</p>}
    </div>
  )
}
