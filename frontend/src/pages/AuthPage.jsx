import { useState } from 'react'
import { api } from '../api'

const MODES = {
  login: '로그인',
  signup: '회원가입',
}

const LOGIN_ID_PATTERN = /^[a-z0-9_]{4,20}$/

function AuthPage({ onAuth }) {
  const [mode, setMode] = useState('login')
  const [loginId, setLoginId] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [nickname, setNickname] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function changeMode(next) {
    setMode(next)
    setError('')
    setPassword('')
    setPasswordConfirm('')
  }

  function validateSignup() {
    if (!LOGIN_ID_PATTERN.test(loginId.trim().toLowerCase()))
      return '아이디는 영문 소문자, 숫자, 밑줄(_)로 4~20자입니다.'
    if (password.length < 8 || password.length > 64) return '비밀번호는 8~64자입니다.'
    if (password !== passwordConfirm) return '비밀번호 확인이 일치하지 않습니다.'
    if (!nickname.trim()) return '닉네임을 입력해 주세요.'
    return ''
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (mode === 'login' && (!loginId.trim() || !password))
      return setError('아이디와 비밀번호를 입력해 주세요.')
    if (mode === 'signup') {
      const message = validateSignup()
      if (message) return setError(message)
    }

    setSubmitting(true)
    try {
      const result =
        mode === 'login'
          ? await api('/auth/login', { method: 'POST', body: { login_id: loginId, password } })
          : await api('/auth/signup', {
              method: 'POST',
              body: { login_id: loginId, password, nickname },
            })
      onAuth(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="auth">
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

      <form className="stack-form" onSubmit={handleSubmit}>
        <label>
          아이디
          <input
            value={loginId}
            onChange={(e) => setLoginId(e.target.value)}
            maxLength={20}
            autoComplete="username"
            autoCapitalize="none"
            placeholder={mode === 'signup' ? '영문 소문자·숫자·_ 4~20자' : ''}
          />
        </label>
        <label>
          비밀번호
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            maxLength={64}
            autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            placeholder={mode === 'signup' ? '8자 이상' : ''}
          />
        </label>
        {mode === 'signup' && (
          <>
            <label>
              비밀번호 확인
              <input
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                maxLength={64}
                autoComplete="new-password"
              />
            </label>
            <label>
              닉네임
              <input
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                maxLength={20}
                autoComplete="off"
                placeholder="그룹에서 보일 이름"
              />
            </label>
            <p className="hint">비밀번호 찾기 기능이 없으니 잊지 않게 기억해 두세요.</p>
          </>
        )}

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

export default AuthPage
