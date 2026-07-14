import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchAreas, resetSession, sendFeedback, streamChat } from '../api/client.js'

// Stable session id per browser tab (matches the old Vue store behaviour).
const SESSION_ID = 'sess-' + Math.random().toString(36).slice(2)

let _uid = 0
const nextId = () => `m${++_uid}`

// Fallback used only until GET /api/areas responds (keeps the three tabs from
// the design visible on first paint). The backend is the source of truth.
const FALLBACK_AREAS = [
  { key: 'normativa', label: 'Normativa General' },
  { key: 'edpr', label: 'Documentación EDPr' },
  { key: 'tecnologo', label: 'Especificaciones Tecnólogo' },
]

/**
 * Central chat state. Mirrors the Pinia store:
 *   - history is kept PER AREA so what the user sees always matches what the
 *     model remembers (switching tabs never resumes an invisible conversation);
 *   - one vote per answer;
 *   - the UI lock (busy) is always released, even on error.
 */
export function useChat() {
  const sessionId = useRef(SESSION_ID).current

  const [areas, setAreas] = useState(FALLBACK_AREAS)
  const [area, setAreaState] = useState('normativa')
  const [messagesByArea, setMessagesByArea] = useState({ normativa: [] })
  const [busy, setBusy] = useState(false)
  // Id of the message whose sources are shown in the right-hand panel.
  const [activeSourcesId, setActiveSourcesId] = useState(null)

  const messages = messagesByArea[area] || []

  // Load the real area list / labels from the backend.
  useEffect(() => {
    let alive = true
    fetchAreas()
      .then((list) => {
        if (alive && Array.isArray(list) && list.length) setAreas(list)
      })
      .catch(() => {
        /* keep fallback areas; a banner is not worth it for a cosmetic list */
      })
    return () => {
      alive = false
    }
  }, [])

  const setArea = useCallback((key) => {
    setAreaState(key)
    setMessagesByArea((prev) => (prev[key] ? prev : { ...prev, [key]: [] }))
  }, [])

  // Update a single message (by id) inside the given area, immutably.
  const patchMessage = useCallback((areaKey, id, patch) => {
    setMessagesByArea((prev) => {
      const list = prev[areaKey] || []
      const next = list.map((m) =>
        m.id === id ? { ...m, ...(typeof patch === 'function' ? patch(m) : patch) } : m,
      )
      return { ...prev, [areaKey]: next }
    })
  }, [])

  const ask = useCallback(
    async (question) => {
      const q = (question || '').trim()
      if (!q || busy) return

      const areaKey = area
      const list = messagesByArea[areaKey] || []
      const isFollowup = list.some((m) => m.role === 'assistant')

      const userMsg = { id: nextId(), role: 'user', text: q }
      const assistantId = nextId()
      const assistantMsg = {
        id: assistantId,
        role: 'assistant',
        text: '',
        sources: [],
        vote: null,
        error: false,
        done: false, // flips true on the SSE "done"/"error" event
      }

      setMessagesByArea((prev) => ({
        ...prev,
        [areaKey]: [...(prev[areaKey] || []), userMsg, assistantMsg],
      }))
      setBusy(true)

      try {
        await streamChat(
          { session_id: sessionId, area: areaKey, question: q, is_followup: isFollowup },
          {
            onSources: (s) => {
              patchMessage(areaKey, assistantId, { sources: s })
              setActiveSourcesId(assistantId) // auto-reveal fresh sources
            },
            onToken: (t) => patchMessage(areaKey, assistantId, (m) => ({ text: m.text + t })),
            onError: (e) => patchMessage(areaKey, assistantId, { text: e, error: true, done: true }),
            onDone: () => patchMessage(areaKey, assistantId, { done: true }),
          },
        )
      } finally {
        // Ensure the message is marked finished even if the stream ended
        // without an explicit done/error event.
        patchMessage(areaKey, assistantId, { done: true })
        setBusy(false)
      }
    },
    [area, busy, messagesByArea, patchMessage, sessionId],
  )

  const vote = useCallback(
    async (messageId, voteValue) => {
      const areaKey = area
      const list = messagesByArea[areaKey] || []
      const idx = list.findIndex((m) => m.id === messageId)
      const a = list[idx]
      if (!a || a.vote) return // one vote per answer
      const question = list[idx - 1]?.text || ''
      patchMessage(areaKey, messageId, { vote: voteValue })
      await sendFeedback({
        session_id: sessionId,
        area: areaKey,
        question,
        answer: a.text,
        vote: voteValue,
      })
    },
    [area, messagesByArea, patchMessage, sessionId],
  )

  // "Nuevo Análisis" / clear history for the current area.
  const newAnalysis = useCallback(async () => {
    const areaKey = area
    setMessagesByArea((prev) => ({ ...prev, [areaKey]: [] }))
    setActiveSourcesId(null)
    try {
      await resetSession(sessionId)
    } catch {
      /* backend memory eviction is best-effort */
    }
  }, [area, sessionId])

  // Sources currently shown in the right panel: the explicitly selected
  // message, else the most recent assistant message that has any.
  const activeMsg =
    messages.find((m) => m.id === activeSourcesId) ||
    [...messages].reverse().find((m) => m.role === 'assistant' && m.sources?.length)
  const activeSources = activeMsg?.sources || []

  return {
    sessionId,
    areas,
    area,
    setArea,
    messages,
    busy,
    ask,
    vote,
    newAnalysis,
    activeSources,
    showSourcesFor: setActiveSourcesId,
  }
}
