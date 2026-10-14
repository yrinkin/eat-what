import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import ServerStatus from './components/ServerStatus'
import EntryPage from './pages/EntryPage'
import HomePage from './pages/HomePage'
import { TOKEN_KEY, clearToken, getToken, saveToken } from './token'
import './App.css'

async function loadMe() {
  if (!getToken()) return { data: null }
  try {
    return { data: await api('/me') }
  } catch (error) {
    return { error }
  }
}

function App() {
  // undefined: 확인 중, null: 입장 전, 객체: 입장 완료
  const [me, setMe] = useState(() => (getToken() ? undefined : null))
  const [loadError, setLoadError] = useState('')

  // 저장된 토큰으로 /me를 불러온 결과를 화면 상태에 반영한다.
  // 토큰이 없거나 401이면 토큰을 지우고 입장 화면으로 보낸다.
  const applyResult = useCallback(({ data, error }) => {
    if (error && error.status !== 401) {
      setLoadError(error.message)
      return
    }
    if (error) clearToken()
    setLoadError('')
    setMe(data ?? null)
  }, [])

  const restore = useCallback(() => loadMe().then(applyResult), [applyResult])

  useEffect(() => {
    if (getToken()) loadMe().then(applyResult)
  }, [applyResult])

  // 다른 탭에서 토큰이 바뀌거나 지워지면 다시 확인한다.
  useEffect(() => {
    function handleStorage(event) {
      if (event.key === TOKEN_KEY || event.key === null) restore()
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [restore])

  function handleEnter({ token, member, group }) {
    saveToken(token)
    setMe({ member, group })
  }

  let content
  if (loadError) {
    content = (
      <div className="load-error">
        <p className="error">{loadError}</p>
        <button type="button" onClick={restore}>
          다시 시도
        </button>
      </div>
    )
  } else if (me === undefined) {
    content = <p>불러오는 중...</p>
  } else if (me === null) {
    content = <EntryPage onEnter={handleEnter} />
  } else {
    content = <HomePage me={me} />
  }

  return (
    <div className="app">
      <header>
        <h1>오늘 뭐 먹지?</h1>
      </header>
      <main>{content}</main>
      <ServerStatus />
    </div>
  )
}

export default App
