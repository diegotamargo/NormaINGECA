// Right-hand "source verification" panel. Where the Stitch mockup drew a faux
// PDF page, this renders the REAL sources returned by the backend for the
// active answer: file name, page label and full path (each Source is
// { archivo, ruta_completa, pagina, score }).
export default function SourcePanel({ open, sources, areaLabel, onClose }) {
  if (!open) return null

  return (
    <aside
      className="w-[400px] h-full hidden lg:flex flex-col border-l border-outline-variant/30 glass-panel z-30 transition-all duration-300 p-lg !rounded-none"
      id="source-panel"
    >
      {/* Header */}
      <div className="py-sm border-b border-outline-variant/30 flex justify-between items-center mb-md">
        <div className="flex items-center gap-2 text-on-surface">
          <span className="material-symbols-outlined text-primary-container" style={{ fontSize: '20px' }}>
            description
          </span>
          <span className="font-label-caps text-label-caps font-bold">VERIFICACIÓN DE FUENTES</span>
        </div>
        <button
          className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant hover:text-error transition-colors ml-2 interactive-element"
          onClick={onClose}
          aria-label="Cerrar panel de fuentes"
        >
          <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
            close
          </span>
        </button>
      </div>

      {/* Context line */}
      <div className="pb-md mb-md border-b border-outline-variant/30">
        <h3 className="font-code-md text-code-md text-primary font-bold mb-1">{areaLabel}</h3>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          {sources.length
            ? `${sources.length} ${sources.length === 1 ? 'documento citado' : 'documentos citados'} en la última respuesta.`
            : 'Aún no hay fuentes para mostrar.'}
        </p>
      </div>

      {/* Source list */}
      <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-sm">
        {sources.length === 0 && (
          <div className="flex flex-col items-center justify-center text-center h-full gap-2 text-on-surface-variant/60">
            <span className="material-symbols-outlined" style={{ fontSize: '40px' }}>
              find_in_page
            </span>
            <p className="font-body-sm text-body-sm">
              Envía una consulta para ver los documentos que respaldan la respuesta.
            </p>
          </div>
        )}

        {sources.map((s, i) => (
          <div
            key={`${s.archivo}-${s.pagina}-${i}`}
            className="bg-surface-container-lowest border border-outline-variant/40 rounded-none p-md flex flex-col gap-2 hover:border-primary-container/50 transition-colors"
          >
            <div className="flex items-start gap-2">
              <span
                className="material-symbols-outlined text-primary-container shrink-0"
                style={{ fontSize: '18px' }}
              >
                picture_as_pdf
              </span>
              <span
                className="font-code-md text-code-md text-on-surface break-words leading-snug"
                title={s.archivo}
              >
                {s.archivo}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-on-surface-variant font-code-md">
              <span className="bg-surface-container px-2 py-0.5 rounded-none border border-outline-variant/50">
                Página {s.pagina}
              </span>
            </div>
            {s.ruta_completa && (
              <p
                className="font-body-sm text-[11px] text-on-surface-variant/70 break-all"
                title={s.ruta_completa}
              >
                {s.ruta_completa}
              </p>
            )}
          </div>
        ))}
      </div>
    </aside>
  )
}
