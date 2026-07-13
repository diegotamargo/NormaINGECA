import { useState } from 'react'

// Floating input bar. Enter (without Shift) or the send button submits.
// Disabled while a request is in flight so the queue never gets double-hit.
export default function ChatInput({ onSend, busy }) {
  const [value, setValue] = useState('')

  const submit = () => {
    const q = value.trim()
    if (!q || busy) return
    onSend(q)
    setValue('')
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="absolute bottom-lg left-0 right-0 w-full px-lg z-20 flex justify-center pointer-events-none">
      <div className="w-full max-w-[1000px] pointer-events-auto">
        <div className="glass-panel rounded-xl p-2 flex flex-col gap-2 glow-effect input-glow transition-all duration-300">
          <div className="flex items-center gap-2 w-full">
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={busy}
              placeholder="Consultar Norma o hacer una pregunta técnica..."
              className="flex-1 bg-transparent border-none text-on-surface font-body-md text-body-md focus:ring-0 placeholder:text-on-surface-variant/50 min-w-0 pl-4 disabled:opacity-60"
            />
            <button
              onClick={submit}
              disabled={busy || !value.trim()}
              className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-lg hover:bg-surface-container-highest shrink-0 interactive-element disabled:opacity-40 disabled:hover:text-on-surface-variant"
              aria-label="Enviar consulta"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
                {busy ? 'hourglass_empty' : 'send'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
