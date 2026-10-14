import { useEffect, useState } from 'react'
import { api } from '../api'

// 내 그룹 목록. 넓은 화면에서는 왼쪽에 늘 보이고, 좁은 화면에서는 그룹 화면과 번갈아 보인다.
function GroupListPage({ selectedId, onSelect }) {
  const [groups, setGroups] = useState(null)
  const [loadError, setLoadError] = useState('')
  const [groupName, setGroupName] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    api('/groups')
      .then((data) => {
        if (cancelled) return
        setLoadError('')
        setGroups(data.items)
      })
      .catch((err) => {
        if (!cancelled) setLoadError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  async function submit(request) {
    setFormError('')
    setSubmitting(true)
    try {
      const group = await request()
      setGroupName('')
      setInviteCode('')
      setReloadKey((n) => n + 1) // 새로 만들거나 참여한 그룹이 목록에 바로 보이게
      onSelect(group.id)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  function handleCreate(event) {
    event.preventDefault()
    if (!groupName.trim()) return setFormError('그룹 이름을 입력해 주세요.')
    submit(() => api('/groups', { method: 'POST', body: { group_name: groupName } }))
  }

  function handleJoin(event) {
    event.preventDefault()
    if (!inviteCode.trim()) return setFormError('초대 코드를 입력해 주세요.')
    submit(() => api('/groups/join', { method: 'POST', body: { invite_code: inviteCode } }))
  }

  return (
    <section className="group-list">
      <h2>내 그룹</h2>
      {loadError && <p className="error">{loadError}</p>}
      {!loadError && groups === null && <p>불러오는 중...</p>}
      {groups?.length === 0 && (
        <p className="hint">아직 속한 그룹이 없어요. 그룹을 만들거나 초대 코드로 참여해 보세요.</p>
      )}
      {groups?.length > 0 && (
        <ul className="cards">
          {groups.map((group) => (
            <li key={group.id}>
              <button
                type="button"
                className={group.id === selectedId ? 'card-button selected' : 'card-button'}
                aria-current={group.id === selectedId ? 'true' : undefined}
                onClick={() => onSelect(group.id)}
              >
                <span className="card-title">{group.name}</span>
                <span className="card-meta">멤버 {group.member_count}명</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="group-forms">
        <form className="inline-form" onSubmit={handleJoin}>
          <label htmlFor="invite-code">초대 코드로 참여</label>
          <div className="row">
            <input
              id="invite-code"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
              maxLength={6}
              placeholder="6자리 코드"
              autoComplete="off"
              autoCapitalize="characters"
              className="code-input"
            />
            <button type="submit" disabled={submitting}>
              참여
            </button>
          </div>
        </form>
        <form className="inline-form" onSubmit={handleCreate}>
          <label htmlFor="group-name">새 그룹 만들기</label>
          <div className="row">
            <input
              id="group-name"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              maxLength={30}
              placeholder="예: 개발팀 점심"
              autoComplete="off"
            />
            <button type="submit" disabled={submitting}>
              만들기
            </button>
          </div>
        </form>
        {formError && (
          <p className="error" role="alert">
            {formError}
          </p>
        )}
      </div>
    </section>
  )
}

export default GroupListPage
