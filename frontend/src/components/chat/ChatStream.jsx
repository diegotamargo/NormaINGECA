import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble.jsx'
import ThinkingIndicator from './ThinkingIndicator.jsx'

// The scrolling conversation. Renders bubbles, auto-scrolls to the newest
// content, and shows the "Analizando" indicator while the assistant reply is
// still empty (i.e. before the first streamed token).
export default function ChatStream({ messages, busy, areaLabel, onVote, onOpenSources, onSuggest }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, busy])

  const last = messages[messages.length - 1]
  const awaitingFirstToken =
    busy && last?.role === 'assistant' && !last.text && !last.error

  const isEmpty = messages.length === 0

  return (
    <div className="flex-1 overflow-y-auto flex flex-col pb-32 items-center w-full custom-scrollbar">
      {isEmpty ? (
        <EmptyState areaLabel={areaLabel} onSuggest={onSuggest} />
      ) : (
        <div className="w-full max-w-[1000px] py-lg flex flex-col gap-xl">
          {messages.map((m) => {
            // Don't render the still-empty assistant placeholder — the
            // ThinkingIndicator stands in for it until the first token.
            if (m.role === 'assistant' && !m.text && !m.error) return null
            return (
              <MessageBubble
                key={m.id}
                message={m}
                onVote={onVote}
                onOpenSources={onOpenSources}
              />
            )
          })}
          {awaitingFirstToken && <ThinkingIndicator />}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  )
}

const SUGGESTIONS = [
  '¿Resistencia máxima de un conductor de cobre de 2,5 mm²?',
  '¿Qué exige la normativa para instalaciones fijas?',
  'Resume los requisitos de aislamiento aplicables.',
]

function EmptyState({ areaLabel, onSuggest }) {
  return (
    <div className="w-full max-w-[720px] flex-1 flex flex-col items-center justify-center text-center py-lg gap-md">
      <div className="w-16 h-16 rounded-xl bg-primary-container/20 border border-primary-container/30 flex items-center justify-center">
        <span
          className="material-symbols-outlined text-primary"
          style={{ fontSize: '32px', fontVariationSettings: "'FILL' 1" }}
        >
          precision_manufacturing
        </span>
      </div>
      <h2 className="font-headline-lg text-headline-lg text-on-surface">
        Asistente Técnico NormaINGECA
      </h2>
      <p className="font-body-md text-body-md text-on-surface-variant max-w-[480px]">
        Consulta la normativa técnica del área <span className="text-primary">{areaLabel}</span>. Las
        respuestas se generan a partir de los documentos indexados y muestran sus fuentes.
      </p>
      <div className="flex flex-col gap-2 w-full max-w-[520px] mt-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSuggest(s)}
            className="px-md py-sm rounded-xl bg-surface-container-high border border-outline-variant/50 text-on-surface-variant hover:text-primary hover:border-primary-container/50 text-left font-body-sm text-body-sm transition-all interactive-element"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
