import { useEffect, useState } from 'react'
import { api } from '../api'

const RATINGS = [1, 2, 3, 4, 5]

function formatDate(isoDate) {
  const [, month, day] = isoDate.split('-').map(Number)
  return `${month}월 ${day}일`
}

// F12: 내가 아직 평가하지 않은 방문. 별점을 등록하면 목록에서 사라진다.
// reloadKey가 바뀌면(뽑기 마감 등) 다시 불러온다.
function PendingReviews({ groupId, reloadKey }) {
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [refresh, setRefresh] = useState(0)

  useEffect(() => {
    let cancelled = false
    api(`/groups/${groupId}/visits/pending-review`)
      .then((data) => {
        if (cancelled) return
        setError('')
        setItems(data.items)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [groupId, reloadKey, refresh])

  function handleDone(message) {
    setNotice(message)
    setRefresh((n) => n + 1)
  }

  if (error) return <p className="error">{error}</p>
  if (!items || (items.length === 0 && !notice)) return null

  return (
    <section className="pending-reviews">
      <h3>별점을 남겨 주세요</h3>
      {notice && (
        <p className="hint" role="status">
          {notice}
        </p>
      )}
      {items.map((item) => (
        <ReviewCard key={item.visit_id} groupId={groupId} item={item} onDone={handleDone} />
      ))}
    </section>
  )
}

function ReviewCard({ groupId, item, onDone }) {
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const name = item.restaurant.name

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    if (!RATINGS.includes(rating)) return setError('별점을 1~5개 골라 주세요.')
    if (comment.trim().length > 100) return setError('한 줄 평은 100자까지 쓸 수 있어요.')

    setSubmitting(true)
    try {
      await api(`/groups/${groupId}/visits/${item.visit_id}/reviews`, {
        method: 'POST',
        body: { rating, comment },
      })
      onDone(`'${name}'에 별점 ${rating}점을 남겼어요.`)
    } catch (err) {
      if (err.code === 'ALREADY_REVIEWED') onDone(`'${name}'에는 이미 별점을 남겼어요.`)
      else {
        setError(err.message)
        setSubmitting(false)
      }
    }
  }

  return (
    <form className="review-card" onSubmit={handleSubmit}>
      <p className="review-title">
        {formatDate(item.visited_on)}에 간 <strong>{name}</strong>
        {item.restaurant.deleted && <span className="hint"> (삭제된 식당)</span>}, 어땠나요?
      </p>
      <fieldset className="stars">
        <legend className="visually-hidden">별점</legend>
        {RATINGS.map((value) => (
          <label key={value} className={value <= rating ? 'star on' : 'star'}>
            <input
              type="radio"
              name={`rating-${item.visit_id}`}
              value={value}
              checked={rating === value}
              onChange={() => setRating(value)}
            />
            <span aria-hidden="true">★</span>
            <span className="visually-hidden">{value}점</span>
          </label>
        ))}
        <span className="star-value">{rating ? `${rating}점` : '별을 눌러 주세요'}</span>
      </fieldset>
      <div className="row">
        <input
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          maxLength={100}
          placeholder="한 줄 평 (선택)"
          aria-label="한 줄 평"
        />
        <button type="submit" className="primary" disabled={submitting}>
          {submitting ? '등록 중...' : '등록'}
        </button>
      </div>
      <p className="counter-line">{comment.length}/100</p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </form>
  )
}

export default PendingReviews
