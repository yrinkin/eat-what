import { useState } from 'react'
import { api } from '../api'
import { CATEGORY_LABELS, PRICE_LABELS, VISITED_OPTIONS } from '../labels'

const WALK_OPTIONS = [5, 10, 15, 20, 30]

// F07: 뽑기 조건. 지정하지 않은 조건은 보내지 않아 서버에서 무시된다.
function DrawForm({ groupId, onDrawn, onConflict }) {
  const [excluded, setExcluded] = useState([])
  const [maxPrice, setMaxPrice] = useState('')
  const [maxWalk, setMaxWalk] = useState('')
  const [visited, setVisited] = useState('')
  const [error, setError] = useState('')
  const [noCandidates, setNoCandidates] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  function toggleCategory(category) {
    setNoCandidates(false)
    setExcluded((prev) => (prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setNoCandidates(false)
    const body = { exclude_categories: excluded }
    if (maxPrice) body.max_price_level = Number(maxPrice)
    if (maxWalk) body.max_walk_minutes = Number(maxWalk)
    if (visited) body.visited = visited === 'true'

    setSubmitting(true)
    try {
      onDrawn(await api(`/groups/${groupId}/draws`, { method: 'POST', body }))
    } catch (err) {
      if (err.code === 'NO_CANDIDATES') setNoCandidates(true)
      else if (err.code === 'ACTIVE_DRAW_EXISTS') onConflict()
      else setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="draw-form" onSubmit={handleSubmit}>
      <fieldset>
        <legend>빼고 싶은 카테고리</legend>
        <div className="chips">
          {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
            <label key={value} className={excluded.includes(value) ? 'chip selected' : 'chip'}>
              <input type="checkbox" checked={excluded.includes(value)} onChange={() => toggleCategory(value)} />
              {label}
            </label>
          ))}
        </div>
      </fieldset>
      <fieldset>
        <legend>방문 여부</legend>
        <div className="chips">
          {VISITED_OPTIONS.map((option) => (
            <label key={option.value} className={visited === option.value ? 'chip picked' : 'chip'}>
              <input
                type="radio"
                name="draw-visited"
                value={option.value}
                checked={visited === option.value}
                onChange={() => {
                  setNoCandidates(false)
                  setVisited(option.value)
                }}
              />
              {option.draw}
            </label>
          ))}
        </div>
      </fieldset>
      <div className="form-row two">
        <label>
          최대 가격대
          <select
            value={maxPrice}
            onChange={(e) => {
              setNoCandidates(false)
              setMaxPrice(e.target.value)
            }}
          >
            <option value="">상관없음</option>
            {Object.entries(PRICE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}까지
              </option>
            ))}
          </select>
        </label>
        <label>
          최대 도보 시간
          <select
            value={maxWalk}
            onChange={(e) => {
              setNoCandidates(false)
              setMaxWalk(e.target.value)
            }}
          >
            <option value="">상관없음</option>
            {WALK_OPTIONS.map((minutes) => (
              <option key={minutes} value={minutes}>
                {minutes}분 이내
              </option>
            ))}
          </select>
        </label>
      </div>
      {maxWalk && <p className="hint">도보 시간을 정하지 않은 식당은 후보에서 빠져요.</p>}

      {noCandidates && (
        <div className="notice" role="alert">
          <strong>조건에 맞는 식당이 없어요.</strong>
          <span>빼는 카테고리를 줄이거나 가격대·도보 시간·방문 여부를 "상관없음"으로 바꿔 보세요.</span>
        </div>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <button type="submit" className="primary" disabled={submitting}>
        {submitting ? '뽑는 중...' : '카드 뽑기'}
      </button>
    </form>
  )
}

export default DrawForm
