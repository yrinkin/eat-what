import { useState } from 'react'
import { api } from '../api'

const MODES = {
  create: '그룹 만들기',
  join: '초대 코드로 입장',
}

function EntryPage({ onEnter }) {
  const [mode, setMode] = useState('join')
  const [groupName, setGroupName] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [nickname, setNickname] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function changeMode(next) {
    setMode(next)
    setError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    const name = nickname.trim()
    if (!name) return setError('닉네임을 입력해 주세요.')
    if (mode === 'create' && !groupName.trim()) return setError('그룹 이름을 입력해 주세요.')
    if (mode === 'join' && !inviteCode.trim()) return setError('초대 코드를 입력해 주세요.')

    setSubmitting(true)
    try {
      const result =
        mode === 'create'
          ? await api('/groups', { method: 'POST', body: { group_name: groupName, nickname } })
          : await api('/groups/join', { method: 'POST', body: { invite_code: inviteCode, nickname } })
      onEnter(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="entry">
      <div className="tabs" role="tablist">
        {Object.entries(MODES).map(([key, label]) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={mode === key}
            className={mode === key ? 'tab active' : 'tab'}
            onClick={() => changeMode(key)}
          >
            {label}
          </button>
        ))}
      </div>

      <form className="entry-form" onSubmit={handleSubmit}>
        {mode === 'create' ? (
          <label>
            그룹 이름
            <input
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              maxLength={30}
              placeholder="예: 개발팀 점심"
              autoComplete="off"
            />
          </label>
        ) : (
          <label>
            초대 코드
            <input
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
              maxLength={6}
              placeholder="6자리 코드"
              autoComplete="off"
              autoCapitalize="characters"
              className="code-input"
            />
          </label>
        )}
        <label>
          닉네임
          <input
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            maxLength={20}
            placeholder="그룹에서 쓸 이름"
            autoComplete="off"
          />
        </label>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="primary" disabled={submitting}>
          {submitting ? '처리 중...' : MODES[mode]}
        </button>
      </form>
    </section>
  )
}

export default EntryPage
