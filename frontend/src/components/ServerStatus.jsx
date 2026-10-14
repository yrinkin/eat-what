import { useEffect, useState } from 'react'

// T03의 health 표시. 화면 아래에 서버와 DB 상태를 작게 보여 준다.
function ServerStatus() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/v1/health')
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setError(true))
  }, [])

  let text = '서버 상태 확인 중...'
  let ok = null
  if (error) {
    text = '서버에 연결할 수 없습니다.'
    ok = false
  } else if (health) {
    text = `status ${health.status} · db ${health.db}`
    ok = health.db === 'ok'
  }

  return (
    <footer className="server-status">
      <span className={ok === null ? '' : ok ? 'ok' : 'error'}>{text}</span>
    </footer>
  )
}

export default ServerStatus
