import { useState } from 'react'
import { renderMarkdown } from '../../lib/markdown.js'
import { useSmoothText } from '../../hooks/useSmoothText.js'

// A single chat turn. User messages are plain text on the right; assistant
// messages render Markdown on the left with a citation chip (opens the source
// panel), a copy button and thumbs up/down feedback.
export default function MessageBubble({ message, onVote, onOpenSources }) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'
  const sourceCount = message.sources?.length || 0

  // While the answer streams, reveal it progressively as plain text (fast, no
  // per-frame Markdown/KaTeX reparse). Once finished, render full Markdown.
  const streaming = !isUser && !message.done && !message.error
  const smoothText = useSmoothText(message.text, streaming)

  if (isUser) {
    return (
      <div className="flex justify-end w-full animate-slide-up-fade">
        <div className="bg-surface-container-high rounded-chat rounded-tr-lg px-lg py-md max-w-[80%] border border-outline-variant/50 chat-bubble">
          <p className="font-body-md text-body-md text-on-surface whitespace-pre-wrap">
            {message.text}
          </p>
        </div>
      </div>
    )
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.text || '')
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard blocked (e.g. non-secure context) — silently ignore */
    }
  }

  return (
    <div className="flex justify-start w-full animate-slide-up-fade">
      <div
        className={
          'glass-panel rounded-chat rounded-tl-lg px-lg py-md max-w-[85%] border-l-4 relative chat-bubble ' +
          (message.error ? 'border-l-error' : 'border-l-primary-container')
        }
      >
        {/* Timeline node */}
        <div className="absolute -left-[14px] top-6 w-6 h-6 rounded-full bg-surface border-2 border-primary-container flex items-center justify-center z-10">
          <div className="w-2.5 h-2.5 rounded-full bg-primary-container shadow-[0_0_8px_#861a22]" />
        </div>

        {message.error ? (
          <p className="font-body-md text-body-md text-error leading-relaxed font-semibold">
            {message.text}
          </p>
        ) : streaming ? (
          <p className="markdown font-body-md text-body-md text-on-surface leading-relaxed whitespace-pre-wrap stream-caret">
            {smoothText}
          </p>
        ) : (
          <div
            className="markdown font-body-md text-body-md text-on-surface leading-relaxed"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(message.text) }}
          />
        )}

        {/* Action row — only once the answer is complete */}
        {!message.error && message.done && message.text && (
          <div className="mt-4 flex flex-wrap gap-2 items-center">
            {sourceCount > 0 && (
              <button
                onClick={() => onOpenSources(message.id)}
                className="inline-flex items-center gap-1 bg-primary-container/20 text-primary border border-primary-container/30 px-2 py-0.5 rounded-full font-label-caps text-label-caps hover:bg-primary-container/40 transition-colors cursor-pointer interactive-element"
              >
                <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>
                  find_in_page
                </span>
                {sourceCount} {sourceCount === 1 ? 'fuente' : 'fuentes'}
              </button>
            )}

            <button
              onClick={copy}
              className="px-3 py-1.5 rounded-lg bg-surface-container-highest border border-outline-variant/50 font-label-caps text-label-caps text-on-surface-variant hover:text-primary hover:border-primary-container/50 transition-all flex items-center gap-1 interactive-element"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
                {copied ? 'check' : 'content_copy'}
              </span>
              {copied ? 'Copiado' : 'Copiar'}
            </button>

            <div className="flex items-center gap-1 ml-auto">
              <button
                onClick={() => onVote(message.id, 'POSITIVO')}
                disabled={!!message.vote}
                title="Respuesta útil"
                className={
                  'p-1.5 rounded-lg border transition-all interactive-element ' +
                  (message.vote === 'POSITIVO'
                    ? 'border-primary-container text-primary bg-primary-container/20'
                    : 'border-outline-variant/50 text-on-surface-variant hover:text-primary disabled:opacity-40')
                }
              >
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
                  thumb_up
                </span>
              </button>
              <button
                onClick={() => onVote(message.id, 'NEGATIVO')}
                disabled={!!message.vote}
                title="Contiene errores o está incompleta"
                className={
                  'p-1.5 rounded-lg border transition-all interactive-element ' +
                  (message.vote === 'NEGATIVO'
                    ? 'border-error text-error bg-error/10'
                    : 'border-outline-variant/50 text-on-surface-variant hover:text-error disabled:opacity-40')
                }
              >
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
                  thumb_down
                </span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
