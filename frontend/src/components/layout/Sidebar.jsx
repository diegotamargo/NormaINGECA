import { useState } from 'react'

// Left navigation. Collapsible. The tabs are the backend "areas"
// (normativa / edpr / tecnologo) — the same keys POST /api/chat expects.

const AREA_ICONS = {
  normativa: 'verified_user',
  edpr: 'description',
  tecnologo: 'engineering',
}

// Company logo lives in /public. If the file isn't present yet we fall back to
// the built-in icon so the header never shows a broken image.
const LOGO_SRC = '/ingeca-logo.png'

export default function Sidebar({
  areas,
  area,
  onSelectArea,
  collapsed,
  onToggleCollapsed,
  onNewAnalysis,
  onToggleTheme,
  dark,
}) {
  const [logoOk, setLogoOk] = useState(true)

  return (
    <nav
      className={
        'bg-surface-container-low/90 backdrop-blur-xl h-full fixed left-0 top-0 border-r border-outline-variant flex flex-col gap-sm z-40 hidden md:flex transition-all duration-300 ease-in-out py-lg ' +
        (collapsed ? 'w-[80px] px-3' : 'w-sidebar-width px-lg')
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

      {/* Header: company logo + product name */}
      <div
        className={
          'flex items-center mb-lg overflow-hidden ' +
          (collapsed ? 'justify-center' : 'gap-sm px-xs')
        }
      >
        {logoOk && !collapsed ? (
          <img
            src={LOGO_SRC}
            alt="Ingeca"
            onError={() => setLogoOk(false)}
            className="h-9 w-auto object-contain shrink-0"
          />
        ) : (
          <div className="w-10 h-10 rounded-lg bg-primary-container flex items-center justify-center text-on-error-container shrink-0">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
              precision_manufacturing
            </span>
          </div>
        )}
        {!collapsed && (
          <div className="whitespace-nowrap min-w-0">
            <h1 className="font-headline-lg text-primary-container text-xl font-bold leading-tight truncate">
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
        title="Nuevo análisis"
        className={
          'w-full py-sm bg-gradient-to-r from-primary-container to-[#b3232d] text-on-error-container rounded-xl font-label-caps text-label-caps flex items-center mb-md hover:brightness-110 transition-all duration-300 glow-effect overflow-hidden interactive-element active:scale-95 ' +
          (collapsed ? 'justify-center px-0' : 'justify-center gap-sm px-md')
        }
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
                'flex items-center rounded-xl w-full font-label-caps text-label-caps interactive-element ' +
                (collapsed ? 'justify-center px-0 py-sm ' : 'gap-md px-md py-sm text-left ') +
                (active
                  ? 'bg-gradient-to-r from-primary-container to-[#b3232d] text-on-error-container glow-effect hover:brightness-110'
                  : 'text-on-surface-variant hover:bg-surface-container-high transition-all duration-200 ease-in-out')
              }
            >
              <span className="material-symbols-outlined shrink-0" style={{ fontSize: '20px' }}>
                {AREA_ICONS[a.key] || 'description'}
              </span>
              {!collapsed && <span className="truncate min-w-0 flex-1">{a.label}</span>}
            </button>
          )
        })}
      </div>

      {/* Theme toggle */}
      <div className="mt-auto pt-4 border-t border-outline-variant/30">
        <button
          onClick={onToggleTheme}
          title={dark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
          className={
            'flex items-center rounded-xl w-full text-on-surface-variant hover:bg-surface-container-high transition-all duration-200 ease-in-out font-label-caps text-label-caps interactive-element ' +
            (collapsed ? 'justify-center px-0 py-sm' : 'gap-md px-md py-sm text-left')
          }
        >
          <span className="material-symbols-outlined shrink-0" style={{ fontSize: '20px' }}>
            {dark ? 'dark_mode' : 'light_mode'}
          </span>
          {!collapsed && (
            <span className="whitespace-nowrap">{dark ? 'Modo Oscuro' : 'Modo Claro'}</span>
          )}
        </button>
      </div>
    </nav>
  )
}
