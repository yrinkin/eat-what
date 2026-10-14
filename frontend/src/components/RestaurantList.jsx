import { useEffect, useState } from 'react'
import { api } from '../api'
import RestaurantForm from './RestaurantForm'
import { CATEGORY_LABELS, PRICE_LABELS, VISITED_OPTIONS, ratingLabel, visitLabel, walkLabel } from '../labels'

const SEARCH_DELAY_MS = 300

// F06: 식당 목록. 이름 검색, 카테고리, 방문 여부 필터를 AND로 적용한다.
// F03~F05: 등록·수정 폼과 삭제 확인. 수정·삭제는 화면 순번이 아니라 식당 id로 요청한다.
function RestaurantList({ groupId, onOpen }) {
  const [keyword, setKeyword] = useState('')
  const [category, setCategory] = useState('')
  const [visited, setVisited] = useState('')
  const [restaurants, setRestaurants] = useState(null)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [actionError, setActionError] = useState('')

  useEffect(() => {
    let cancelled = false
    const params = new URLSearchParams()
    if (keyword.trim()) params.set('q', keyword.trim())
    if (category) params.set('category', category)
    if (visited) params.set('visited', visited)
    const query = params.toString()

    // 입력할 때마다 요청하지 않도록 잠시 기다린다. 늦게 도착한 이전 응답은 무시한다.
    const timer = setTimeout(() => {
      api(`/groups/${groupId}/restaurants${query ? `?${query}` : ''}`)
        .then((data) => {
          if (cancelled) return
          setError('')
          setRestaurants(data.items)
        })
        .catch((err) => {
          if (!cancelled) setError(err.message)
        })
    }, SEARCH_DELAY_MS)

    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [groupId, keyword, category, visited, reloadKey])

  // 저장·삭제 후 지금 걸린 검색·필터 그대로 목록을 다시 불러온다.
  const reload = () => setReloadKey((key) => key + 1)

  function handleCreated() {
    setCreating(false)
    reload()
  }

  function handleUpdated() {
    setEditingId(null)
    reload()
  }

  async function handleDelete(restaurant) {
    setActionError('')
    // confirm은 글자만 보여 주므로 이름에 태그가 있어도 실행되지 않는다.
    if (!window.confirm(`'${restaurant.name}' 식당을 삭제할까요?\n방문 기록과 별점은 남습니다.`)) return
    try {
      await api(`/groups/${groupId}/restaurants/${restaurant.id}`, { method: 'DELETE' })
      reload()
    } catch (err) {
      setActionError(err.message)
      reload()
    }
  }

  const filtered = keyword.trim() !== '' || category !== '' || visited !== ''

  return (
    <section className="restaurants">
      <div className="section-head">
        <h3>식당 목록</h3>
        {!creating && (
          <button type="button" onClick={() => setCreating(true)}>
            + 식당 등록
          </button>
        )}
      </div>
      {creating && (
        <RestaurantForm groupId={groupId} onSaved={handleCreated} onCancel={() => setCreating(false)} />
      )}
      <div className="filters">
        <input
          type="search"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          maxLength={50}
          placeholder="이름 검색"
          aria-label="식당 이름 검색"
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="카테고리">
          <option value="">전체 카테고리</option>
          {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select value={visited} onChange={(e) => setVisited(e.target.value)} aria-label="방문 여부">
          {VISITED_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.list}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="error">{error}</p>}
      {actionError && (
        <p className="error" role="alert">
          {actionError}
        </p>
      )}
      {!error && restaurants === null && <p>불러오는 중...</p>}
      {restaurants !== null && (
        <p className="result-count">
          {filtered ? '조건에 맞는 식당' : '전체'} {restaurants.length}곳
        </p>
      )}
      {restaurants?.length === 0 && (
        <p className="hint">{filtered ? '조건에 맞는 식당이 없어요.' : '아직 등록된 식당이 없어요.'}</p>
      )}
      {restaurants?.length > 0 && (
        <ul className="restaurant-list">
          {restaurants.map((r) =>
            editingId === r.id ? (
              <li key={r.id} className="restaurant-card editing">
                <RestaurantForm
                  groupId={groupId}
                  restaurant={r}
                  onSaved={handleUpdated}
                  onCancel={() => setEditingId(null)}
                />
              </li>
            ) : (
              <li key={r.id} className="restaurant-card">
                <div className="restaurant-head">
                  <button type="button" className="link-button restaurant-name" onClick={() => onOpen(r.id)}>
                    {r.name}
                  </button>
                  <span className="badge">{CATEGORY_LABELS[r.category]}</span>
                </div>
                <p className="restaurant-meta">
                  {PRICE_LABELS[r.price_level]} · {walkLabel(r.walk_minutes)}
                </p>
                <p className="restaurant-meta">
                  {ratingLabel(r.avg_rating, r.review_count)} · {visitLabel(r.last_visited_on)}
                </p>
                {r.memo && <p className="restaurant-memo">{r.memo}</p>}
                <p className="restaurant-foot">
                  등록 {r.created_by.nickname}
                  {r.map_url && (
                    <>
                      {' · '}
                      <a href={r.map_url} target="_blank" rel="noopener noreferrer">
                        지도 보기
                      </a>
                    </>
                  )}
                </p>
                <div className="card-actions">
                  <button type="button" className="small" onClick={() => setEditingId(r.id)}>
                    수정
                  </button>
                  <button type="button" className="small danger" onClick={() => handleDelete(r)}>
                    삭제
                  </button>
                </div>
              </li>
            ),
          )}
        </ul>
      )}
    </section>
  )
}

export default RestaurantList
