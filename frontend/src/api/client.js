// Thin API layer. The browser ONLY talks to our FastAPI server — never to an
// LLM provider directly, so no keys or model config ever reach the client.
// (Code in English; every user-visible string in Spanish.)
//
// All paths are relative to API_BASE. By default that is "" -> requests go to
// "/api/...", which the Vite dev proxy forwards to the backend and which the
// production StaticFiles mount serves from the same origin. Set VITE_API_BASE
// (e.g. "http://localhost:58734") only if you must call the backend on a
// different origin directly (then the backend CORS must allow this origin).

const API_BASE = import.meta.env.VITE_API_BASE || ''
const url = (path) => `${API_BASE}${path}`

// GET /api/areas -> [{ key, label }]
export async function fetchAreas() {
  const r = await fetch(url('/api/areas'))
  if (!r.ok) throw new Error('No se pudieron cargar las áreas.')
  return r.json()
}

// GET /api/health -> { status, backend, queue_depth, active_sessions }
export async function fetchHealth() {
  const r = await fetch(url('/api/health'))
  if (!r.ok) throw new Error('health check failed')
  return r.json()
}

// GET /api/suggestions?area=X -> ["...", "...", "..."] (example questions
// generated at ingest from that area's documents; [] if none yet).
export async function fetchSuggestions(area) {
  try {
    const r = await fetch(url(`/api/suggestions?area=${encodeURIComponent(area)}`))
    if (!r.ok) return []
    const list = await r.json()
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

// POST /api/feedback  { session_id, area, question, answer, vote }
export async function sendFeedback(payload) {
  await fetch(url('/api/feedback'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

// POST /api/reset  { session_id }  -> clears the session's per-area memory
export async function resetSession(sessionId) {
  await fetch(url('/api/reset'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  })
}

// Streams an answer via SSE. Uses fetch + ReadableStream so we can POST a body
// (the native EventSource can only GET). The backend emits four event types:
//   event: sources -> JSON array of { archivo, ruta_completa, pagina, score }
//   event: token   -> a chunk of the answer text
//   event: error   -> a Spanish user-facing error message
//   event: done    -> end of stream
export async function streamChat(payload, { onSources, onToken, onDone, onError }) {
  let resp
  try {
    resp = await fetch(url('/api/chat'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch {
    onError?.('No se ha podido conectar con el servidor.')
    return
  }

  if (!resp.ok || !resp.body) {
    // The backend sheds load with a real HTTP 503 whose JSON "detail" is
    // already a Spanish user-facing message.
    let detail = 'Error de red al contactar con el servidor.'
    try {
      detail = (await resp.json()).detail || detail
    } catch {
      /* keep default */
    }
    onError?.(detail)
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      // Normalize CRLF: the SSE spec allows \r\n line endings; splitting on
      // '\n\n' alone would break if the server emits them.
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')

      // SSE frames are separated by a blank line.
      const frames = buffer.split('\n\n')
      buffer = frames.pop() || ''
      for (const frame of frames) {
        let event = 'message'
        const dataLines = []
        for (const line of frame.split('\n')) {
          if (line.startsWith('event:')) event = line.slice(6).trim()
          else if (line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''))
        }
        // Per the SSE spec, multiple data: lines in one frame are the payload
        // split on '\n' and must be re-joined with '\n' (otherwise every
        // newline the model emitted — Markdown paragraphs, lists — is lost).
        const data = dataLines.join('\n')

        if (event === 'sources') onSources?.(JSON.parse(data))
        else if (event === 'token') onToken?.(data)
        else if (event === 'error') onError?.(data)
        else if (event === 'done') onDone?.()
      }
    }
  } catch {
    // Connection dropped mid-stream (server crash, network loss, etc.).
    onError?.('Se ha perdido la conexión con el servidor durante la respuesta.')
  }
}
