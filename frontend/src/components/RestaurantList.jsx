import { useEffect, useState } from 'react'
import { api } from '../api'
import { CATEGORY_LABELS, PRICE_LABELS, ratingLabel, visitLabel, walkLabel } from '../labels'

const SEARCH_DELAY_MS = 300

// F06: 식당 목록. 이름 검색과 카테고리 필터를 AND로 적용한다.
function RestaurantList({ groupId }) {
  const [keyword, setKeyword] = useState('')
  const [category, setCategory] = useState('')
  const [restaurants, setRestaurants] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    const params = new URLSearchParams()
    if (keyword.trim()) params.set('q', keyword.trim())
    if (category) params.set('category', category)
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
  }, [groupId, keyword, category])

  const filtered = keyword.trim() !== '' || category !== ''

  return (
    <section className="restaurants">
      <h3>식당 목록</h3>
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
      </div>

      {error && <p className="error">{error}</p>}
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
          {restaurants.map((r) => (
            <li key={r.id} className="restaurant-card">
              <div className="restaurant-head">
                <span className="restaurant-name">{r.name}</span>
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
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default RestaurantList
