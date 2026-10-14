import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/v1/health')
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setError('API 서버에 연결할 수 없습니다.'))
  }, [])

  return (
    <main className="app">
      <h1>오늘 뭐 먹지?</h1>
      <section className="health">
        <h2>서버 상태</h2>
        {error && <p className="error">{error}</p>}
        {!error && !health && <p>확인 중...</p>}
        {health && (
          <dl>
            <dt>status</dt>
            <dd>{health.status}</dd>
            <dt>db</dt>
            <dd className={health.db === 'ok' ? 'ok' : 'error'}>{health.db}</dd>
          </dl>
        )}
      </section>
    </main>
  )
}

export default App
