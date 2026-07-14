import { useCallback, useEffect, useState } from 'react'
import Sidebar from './components/layout/Sidebar.jsx'
import MobileHeader from './components/layout/MobileHeader.jsx'
import ChatView from './components/chat/ChatView.jsx'
import SourcePanel from './components/sources/SourcePanel.jsx'
import { useChat } from './hooks/useChat.js'

export default function App() {
  const {
    areas,
    area,
    setArea,
    messages,
    busy,
    ask,
    vote,
    newAnalysis,
    activeSources,
    showSourcesFor,
    suggestions,
  } = useChat()

  // Layout / UI state (kept out of the chat hook on purpose).
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [sourcePanelOpen, setSourcePanelOpen] = useState(true)
  const [dark, setDark] = useState(false)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  const areaLabel = areas.find((a) => a.key === area)?.label || area

  const openSources = useCallback(
    (messageId) => {
      showSourcesFor(messageId)
      setSourcePanelOpen(true)
    },
    [showSourcesFor],
  )

  return (
    <div className="bg-surface-container-lowest text-on-surface h-screen w-screen overflow-hidden flex font-body-md text-body-md antialiased selection:bg-primary-container selection:text-on-primary-container">
      <Sidebar
        areas={areas}
        area={area}
        onSelectArea={setArea}
        collapsed={sidebarCollapsed}
        onToggleCollapsed={() => setSidebarCollapsed((v) => !v)}
        onNewAnalysis={newAnalysis}
        onToggleTheme={() => setDark((v) => !v)}
        dark={dark}
      />

      <MobileHeader onNewAnalysis={newAnalysis} />

      <main
        className={
          'flex-1 flex h-full pt-16 md:pt-0 relative overflow-hidden transition-all duration-300 ease-in-out w-full ' +
          (sidebarCollapsed ? 'md:ml-[80px]' : 'md:ml-sidebar-width')
        }
      >
        <ChatView
          areaLabel={areaLabel}
          messages={messages}
          busy={busy}
          onAsk={ask}
          onVote={vote}
          onOpenSources={openSources}
          sourcePanelOpen={sourcePanelOpen}
          onToggleSources={() => setSourcePanelOpen((v) => !v)}
          suggestions={suggestions}
        />

        <SourcePanel
          open={sourcePanelOpen}
          sources={activeSources}
          areaLabel={areaLabel}
          onClose={() => setSourcePanelOpen(false)}
        />
      </main>
    </div>
  )
}
