// Sticky chat header. Shows the active area and the current question so the
// user always knows the scope of the conversation.
export default function ChatHeader({ areaLabel, currentQuestion }) {
  return (
    <div className="py-md border-b border-outline-variant/30 sticky top-0 z-10 flex items-center justify-between w-full bg-surface-container-lowest/90 backdrop-blur-md">
      <div className="min-w-0">
        <h2 className="font-body-sm text-body-sm text-on-surface-variant">Consulta Actual</h2>
        <p className="font-code-md text-code-md text-primary mt-1 truncate">
          {currentQuestion || areaLabel}
        </p>
      </div>
    </div>
  )
}
