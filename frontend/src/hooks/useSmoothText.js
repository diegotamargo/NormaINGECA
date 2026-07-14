import { useEffect, useRef, useState } from 'react'

// Reveals `target` progressively so a streamed answer types out smoothly
// instead of appearing in the bursts the SSE tokens arrive in.
//
//   - While `active` is true it catches up to the latest target a few
//     characters per animation frame, revealing faster when it has fallen
//     further behind so it never lags noticeably behind the real stream.
//   - When `active` becomes false (answer finished) it snaps to the full text.
//   - If the target diverges from what's shown (new answer, history cleared)
//     it snaps to avoid showing stale characters.
export function useSmoothText(target, active) {
  const [shown, setShown] = useState(target || '')
  const targetRef = useRef(target || '')
  targetRef.current = target || ''

  useEffect(() => {
    if (!active) {
      setShown(targetRef.current)
      return
    }
    let raf = 0
    let mounted = true
    const tick = () => {
      if (!mounted) return
      setShown((prev) => {
        const t = targetRef.current
        if (prev === t) return prev
        if (!t.startsWith(prev)) return t // diverged -> snap
        const remaining = t.length - prev.length
        const step = Math.max(2, Math.ceil(remaining / 6))
        return t.slice(0, prev.length + step)
      })
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => {
      mounted = false
      cancelAnimationFrame(raf)
    }
  }, [active])

  return shown
}
