// Top app bar shown only on mobile (md:hidden). The desktop sidebar is hidden
// below md, so this gives small screens a title and the new-analysis action.
export default function MobileHeader({ onNewAnalysis }) {
  return (
    <header className="bg-surface/80 backdrop-blur-xl fixed top-0 w-full z-50 flex justify-between items-center px-lg py-md border-b border-outline-variant shadow-sm md:hidden">
      <div className="font-headline-lg-mobile text-headline-lg-mobile font-bold text-primary-container">
        NormaINGECA IA
      </div>
      <div className="flex items-center gap-md">
        <button
          onClick={onNewAnalysis}
          className="text-on-surface-variant hover:text-primary interactive-element"
          title="Nuevo análisis"
          aria-label="Nuevo análisis"
        >
          <span className="material-symbols-outlined">add</span>
        </button>
      </div>
    </header>
  )
}
