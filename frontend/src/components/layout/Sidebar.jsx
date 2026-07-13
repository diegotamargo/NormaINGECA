// Left navigation. Collapsible. The tabs are the backend "areas"
// (normativa / edpr / tecnologo) — the same keys POST /api/chat expects.

const AREA_ICONS = {
  normativa: 'verified_user',
  edpr: 'description',
  tecnologo: 'engineering',
}

export default function Sidebar({
  areas,
  area,
  onSelectArea,
  collapsed,
  onToggleCollapsed,
  onNewAnalysis,
  onToggleTheme,
}) {
  return (
    <nav
      className={
        'bg-surface-container-low/90 backdrop-blur-xl h-full fixed left-0 top-0 border-r border-outline-variant flex flex-col p-lg gap-sm z-40 hidden md:flex transition-all duration-300 ease-in-out ' +
        (collapsed ? 'sidebar-collapsed w-[80px]' : 'sidebar-expanded w-sidebar-width')
      }
      id="sidebar"
    >
      {/* Collapse toggle */}
      <button
        className="absolute -right-3 top-6 bg-surface-container border border-outline-variant rounded-full p-1 text-on-surface-variant hover:text-primary z-50 flex items-center justify-center interactive-element hover:scale-110"
        onClick={onToggleCollapsed}
        aria-label={collapsed ? 'Expandir panel' : 'Colapsar panel'}
      >
        <span className="material-symbols-outlined text-[16px]">
          {collapsed ? 'chevron_right' : 'chevron_left'}
        </span>
      </button>

      {/* Header */}
      <div className="flex items-center gap-sm mb-lg px-xs overflow-hidden">
        <div className="w-10 h-10 rounded-lg bg-primary-container flex items-center justify-center text-on-error-container shrink-0">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
            precision_manufacturing
          </span>
        </div>
        {!collapsed && (
          <div className="transition-opacity duration-300 whitespace-nowrap">
            <h1 className="font-headline-lg text-primary-container text-xl font-bold leading-tight">
              NormaINGECA
            </h1>
            <p className="font-label-caps text-label-caps text-on-surface-variant uppercase">
              Asistente Técnico IA
            </p>
          </div>
        )}
      </div>

      {/* CTA: new analysis (clears current area history) */}
      <button
        onClick={onNewAnalysis}
        className="w-full py-sm px-md bg-gradient-to-r from-primary-container to-[#b3232d] text-on-error-container rounded-xl font-label-caps text-label-caps flex items-center justify-center gap-sm mb-md hover:brightness-110 transition-all duration-300 glow-effect overflow-hidden interactive-element active:scale-95"
      >
        <span className="material-symbols-outlined shrink-0" style={{ fontSize: '18px' }}>
          add
        </span>
        {!collapsed && <span className="whitespace-nowrap">NUEVO ANÁLISIS</span>}
      </button>

      {/* Area tabs */}
      <div className="flex flex-col gap-xs flex-1 overflow-x-hidden">
        {areas.map((a) => {
          const active = a.key === area
          return (
            <button
              key={a.key}
              onClick={() => onSelectArea(a.key)}
              title={a.label}
              className={
                'flex items-center gap-md px-md py-sm rounded-xl w-full text-left font-label-caps text-label-caps interactive-element ' +
                (active
                  ? 'bg-gradient-to-r from-primary-container to-[#b3232d] text-on-error-container glow-effect hover:brightness-110'
                  : 'text-on-surface-variant hover:bg-surface-container-high transition-all duration-200 ease-in-out')
              }
            >
              <span className="material-symbols-outlined shrink-0" style={{ fontSize: '20px' }}>
                {AREA_ICONS[a.key] || 'description'}
              </span>
              {!collapsed && <span className="whitespace-nowrap">{a.label}</span>}
            </button>
          )
        })}
      </div>

      {/* Theme toggle */}
      <div className="mt-auto pt-4 border-t border-outline-variant/30">
        <button
          className="flex items-center gap-md px-md py-sm text-on-surface-variant hover:bg-surface-container-high rounded-xl w-full text-left transition-all duration-200 ease-in-out font-label-caps text-label-caps interactive-element"
          onClick={onToggleTheme}
        >
          <span
            className="material-symbols-outlined shrink-0 hidden dark:block"
            style={{ fontSize: '20px' }}
          >
            dark_mode
          </span>
          <span
            className="material-symbols-outlined shrink-0 block dark:hidden"
            style={{ fontSize: '20px' }}
          >
            light_mode
          </span>
          {!collapsed && (
            <div className="whitespace-nowrap">
              <span className="hidden dark:inline">Tema Oscuro</span>
              <span className="inline dark:hidden">Tema Claro</span>
            </div>
          )}
        </button>
      </div>
    </nav>
  )
}
