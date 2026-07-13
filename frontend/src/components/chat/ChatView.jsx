import ChatHeader from './ChatHeader.jsx'
import ChatStream from './ChatStream.jsx'
import ChatInput from './ChatInput.jsx'

// Center column: header + scrolling stream + floating input.
export default function ChatView({
  areaLabel,
  messages,
  busy,
  onAsk,
  onVote,
  onOpenSources,
}) {
  const lastUser = [...messages].reverse().find((m) => m.role === 'user')

  return (
    <section className="flex-1 flex flex-col mx-auto w-full relative h-full border-r border-outline-variant/30 px-lg">
      <ChatHeader areaLabel={areaLabel} currentQuestion={lastUser?.text} />
      <ChatStream
        messages={messages}
        busy={busy}
        areaLabel={areaLabel}
        onVote={onVote}
        onOpenSources={onOpenSources}
        onSuggest={onAsk}
      />
      <ChatInput onSend={onAsk} busy={busy} />
    </section>
  )
}
