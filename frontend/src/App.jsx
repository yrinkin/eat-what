import { useCallback, useEffect, useState } from 'react'
import { UNAUTHORIZED_EVENT, api } from './api'
import ServerStatus from './components/ServerStatus'
import AuthPage from './pages/AuthPage'
import GroupListPage from './pages/GroupListPage'
import GroupPage from './pages/GroupPage'
import {
  TOKEN_KEY,
  clearToken,
  getSavedGroupId,
  getToken,
  saveGroupId,
  saveToken,
} from './token'
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
  // undefined: 확인 중, null: 로그인 전, 객체: 로그인한 계정
  const [user, setUser] = useState(() => (getToken() ? undefined : null))
  const [groupId, setGroupId] = useState(getSavedGroupId)
  const [loadError, setLoadError] = useState('')

  const signOutLocally = useCallback(() => {
    clearToken()
    saveGroupId(null)
    setGroupId(null)
    setLoadError('')
    setUser(null)
  }, [])

  // /me 결과를 화면 상태에 반영한다. 토큰이 없거나 401이면 로그인 화면으로 보낸다.
  const applyResult = useCallback(
    ({ data, error }) => {
      if (error && error.status !== 401) {
        setLoadError(error.message)
        return
      }
      if (error || !data) {
        signOutLocally()
        return
      }
      setLoadError('')
      setUser(data.user)
    },
    [signOutLocally],
  )

  const restore = useCallback(() => loadMe().then(applyResult), [applyResult])

  useEffect(() => {
    if (getToken()) loadMe().then(applyResult)
  }, [applyResult])

  useEffect(() => {
    // 다른 탭에서 로그인·로그아웃하면 다시 확인한다.
    function handleStorage(event) {
      if (event.key === TOKEN_KEY || event.key === null) restore()
    }
    window.addEventListener('storage', handleStorage)
    window.addEventListener(UNAUTHORIZED_EVENT, signOutLocally)
    return () => {
      window.removeEventListener('storage', handleStorage)
      window.removeEventListener(UNAUTHORIZED_EVENT, signOutLocally)
    }
  }, [restore, signOutLocally])

  function handleAuth({ token, user: nextUser }) {
    saveToken(token)
    saveGroupId(null)
    setGroupId(null)
    setUser(nextUser)
  }

  async function handleLogout() {
    try {
      await api('/auth/logout', { method: 'POST' })
    } catch {
      // 서버 세션이 이미 없어도 브라우저에서는 로그아웃한다.
    }
    signOutLocally()
  }

  function selectGroup(id) {
    saveGroupId(id)
    setGroupId(id)
  }

  const backToList = useCallback(() => {
    saveGroupId(null)
    setGroupId(null)
  }, [])

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
  } else if (user === undefined) {
    content = <p>불러오는 중...</p>
  } else if (user === null) {
    content = <AuthPage onAuth={handleAuth} />
  } else {
    // 넓은 화면: 왼쪽 그룹 목록 + 오른쪽 그룹 화면. 좁은 화면: 선택 여부에 따라 둘 중 하나만 보인다(CSS).
    content = (
      <div className={groupId === null ? 'workspace' : 'workspace has-selection'}>
        <aside className="sidebar">
          <GroupListPage selectedId={groupId} onSelect={selectGroup} />
        </aside>
        <div className="main-panel">
          {groupId === null ? (
            <p className="empty-panel">왼쪽에서 그룹을 골라 주세요.</p>
          ) : (
            <GroupPage key={groupId} groupId={groupId} onBack={backToList} />
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>오늘 뭐 먹지?</h1>
        {user && (
          <div className="account">
            <span className="nickname">{user.nickname}</span>
            <button type="button" className="link-button" onClick={handleLogout}>
              로그아웃
            </button>
          </div>
        )}
      </header>
      <main>{content}</main>
      <ServerStatus />
    </div>
  )
}

export default App
