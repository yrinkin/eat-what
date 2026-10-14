import { useEffect, useRef } from 'react'

// callback을 바로 한 번 실행하고, 끝날 때마다 intervalMs 뒤에 다시 실행한다.
// - 요청이 끝난 뒤에 다음 예약을 하므로 서버가 느려도 요청이 겹치지 않는다.
// - 탭이 가려지면(document.hidden) 예약을 멈추고, 다시 보이면 바로 한 번 실행한 뒤 이어 간다.
// - enabled가 false이거나 key가 바뀌면 지금 주기를 멈추고 새로 시작한다.
export default function usePolling(callback, intervalMs, { enabled = true, key } = {}) {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  })

  useEffect(() => {
    if (!enabled) return undefined
    let timer = null
    let running = false
    let stopped = false

    async function tick() {
      timer = null
      if (stopped || document.hidden || running) return
      running = true
      try {
        await savedCallback.current()
      } catch {
        // 오류 표시는 callback이 맡는다. 다음 주기에 다시 시도한다.
      } finally {
        running = false
      }
      if (!stopped && !document.hidden) timer = setTimeout(tick, intervalMs)
    }

    function handleVisibility() {
      if (document.hidden) {
        clearTimeout(timer)
        timer = null
      } else if (timer === null) {
        tick()
      }
    }

    tick()
    document.addEventListener('visibilitychange', handleVisibility)
    return () => {
      stopped = true
      clearTimeout(timer)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [intervalMs, enabled, key])
}
