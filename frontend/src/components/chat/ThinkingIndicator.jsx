// The "Analizando" placeholder shown while the backend retrieves + generates,
// before the first token arrives. Ported from the Stitch thinking state.
export default function ThinkingIndicator() {
  return (
    <div className="flex justify-start w-full animate-slide-up-fade">
      <div className="glass-panel rounded-chat rounded-tl-lg px-lg py-md w-48 border-l-4 border-l-primary-container/30 relative flex gap-1 items-center thinking-indicator overflow-hidden">
        <span className="w-2 h-2 rounded-full bg-primary-container/40 animate-bounce [animation-delay:-0.3s]" />
        <span className="w-2 h-2 rounded-full bg-primary-container/60 animate-bounce [animation-delay:-0.15s]" />
        <span className="w-2 h-2 rounded-full bg-primary-container animate-bounce" />
        <span className="ml-2 font-label-caps text-[10px] text-on-surface-variant/70 tracking-widest uppercase">
          Analizando
        </span>
      </div>
    </div>
  )
}
