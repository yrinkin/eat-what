import { useEffect, useState } from 'react'
import { api } from '../api'
import { CATEGORY_LABELS, PRICE_LABELS, ratingLabel, visitLabel, walkLabel } from '../labels'

function formatDate(isoDate) {
  const [year, month, day] = isoDate.split('-').map(Number)
  return `${year}년 ${month}월 ${day}일`
}

// F13: 식당 상세. 팀 평균 별점(소수 첫째 자리), 방문 이력, 방문별 한 줄 평.
function RestaurantDetail({ groupId, restaurantId, onBack }) {
  const [restaurant, setRestaurant] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    api(`/groups/${groupId}/restaurants/${restaurantId}`)
      .then((data) => {
        if (!cancelled) setRestaurant(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.status === 404 ? '삭제되었거나 찾을 수 없는 식당이에요.' : err.message)
      })
    return () => {
      cancelled = true
    }
  }, [groupId, restaurantId])

  const back = (
    <button type="button" className="link-button" onClick={onBack}>
      ← 그룹 홈
    </button>
  )

  if (error)
    return (
      <section className="restaurant-detail">
        {back}
        <p className="error">{error}</p>
      </section>
    )
  if (!restaurant) return <p className="loading">불러오는 중...</p>

  const r = restaurant
  return (
    <section className="restaurant-detail">
      {back}
      <div className="restaurant-head">
        <h2>{r.name}</h2>
        <span className="badge">{CATEGORY_LABELS[r.category]}</span>
      </div>
      <p className="detail-rating">{ratingLabel(r.avg_rating, r.review_count)}</p>
      <p className="restaurant-meta">
        {PRICE_LABELS[r.price_level]} · {walkLabel(r.walk_minutes)} · {visitLabel(r.last_visited_on)}
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

      <h3>방문 이력</h3>
      {r.visits.length === 0 && <p className="hint">아직 뽑기로 방문한 적이 없어요.</p>}
      <ul className="visit-list">
        {r.visits.map((visit) => (
          <li key={visit.id} className="visit-item">
            <p className="visit-date">{formatDate(visit.visited_on)}</p>
            {visit.reviews.length === 0 ? (
              <p className="hint">아직 남긴 별점이 없어요.</p>
            ) : (
              <ul className="review-list">
                {visit.reviews.map((review) => (
                  <li key={review.id}>
                    <span className="review-stars" aria-label={`${review.rating}점`}>
                      {'★'.repeat(review.rating)}
                      <span className="off">{'★'.repeat(5 - review.rating)}</span>
                    </span>
                    <span className="review-author">{review.member.nickname}</span>
                    {review.comment && <span className="review-comment">{review.comment}</span>}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

export default RestaurantDetail
