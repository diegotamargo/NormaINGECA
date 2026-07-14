// Sticky chat header. Shows the active area and the current question so the
// user always knows the scope of the conversation, plus a toggle to show/hide
// the source-verification panel (so closing it is never a dead end).
export default function ChatHeader({
  areaLabel,
  currentQuestion,
  sourcePanelOpen,
  onToggleSources,
}) {
  return (
    <div className="py-md border-b border-outline-variant/30 sticky top-0 z-10 flex items-center justify-between gap-3 w-full bg-surface-container-lowest/90 backdrop-blur-md">
      <div className="min-w-0">
        <h2 className="font-body-sm text-body-sm text-on-surface-variant">Consulta Actual</h2>
        <p className="font-code-md text-code-md text-primary mt-1 truncate">
          {currentQuestion || areaLabel}
        </p>
      </div>

      {onToggleSources && (
        <button
          onClick={onToggleSources}
          aria-label={sourcePanelOpen ? 'Ocultar fuentes' : 'Mostrar fuentes'}
          aria-pressed={sourcePanelOpen}
          title={sourcePanelOpen ? 'Ocultar fuentes' : 'Mostrar fuentes'}
          className={
            'shrink-0 hidden lg:flex items-center gap-2 px-md py-sm rounded-xl border text-body-sm font-body-sm transition-all interactive-element ' +
            (sourcePanelOpen
              ? 'bg-primary-container/20 border-primary-container/50 text-primary'
              : 'bg-surface-container-high border-outline-variant/50 text-on-surface-variant hover:text-primary hover:border-primary-container/50')
          }
        >
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
            {sourcePanelOpen ? 'right_panel_close' : 'right_panel_open'}
          </span>
          <span>Fuentes</span>
        </button>
      )}
    </div>
  )
}
