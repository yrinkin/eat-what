import { useState } from 'react'
import { api } from '../api'
import { CATEGORY_LABELS, PRICE_LABELS } from '../labels'

const EMPTY = { name: '', category: '', price_level: 2, walk_minutes: null, map_url: null, memo: '' }

function toForm(restaurant) {
  return {
    name: restaurant.name,
    category: restaurant.category,
    price_level: String(restaurant.price_level),
    walk_minutes: restaurant.walk_minutes === null ? '' : String(restaurant.walk_minutes),
    map_url: restaurant.map_url ?? '',
    memo: restaurant.memo,
  }
}

// 폼 값을 API 값으로 바꾼다. 빈 도보 시간·지도 링크는 null(미지정)이다.
function toPayload(form) {
  return {
    name: form.name.trim(),
    category: form.category,
    price_level: Number(form.price_level),
    walk_minutes: form.walk_minutes.trim() === '' ? null : Number(form.walk_minutes),
    map_url: form.map_url.trim() === '' ? null : form.map_url.trim(),
    memo: form.memo,
  }
}

// API-SPEC.md 식당 객체 규칙과 같은 검사. 서버도 같은 규칙으로 다시 검사한다.
function validate(payload) {
  if (!payload.name) return '이름을 입력해 주세요.'
  if (payload.name.length > 50) return '이름은 50자까지 입력할 수 있어요.'
  if (!payload.category) return '카테고리를 골라 주세요.'
  const walk = payload.walk_minutes
  if (walk !== null && (!Number.isInteger(walk) || walk < 0 || walk > 60))
    return '도보 시간은 0~60 사이의 정수로 입력해 주세요.'
  if (payload.map_url !== null) {
    if (payload.map_url.length > 500) return '지도 링크는 500자까지 입력할 수 있어요.'
    if (!/^https?:\/\/[^\s/]+/i.test(payload.map_url))
      return '지도 링크는 http:// 또는 https://로 시작해야 해요.'
  }
  if (payload.memo.length > 200) return '메모는 200자까지 입력할 수 있어요.'
  return ''
}

// F03, F04: 식당 등록·수정 폼. restaurant가 있으면 수정, 없으면 등록이다.
function RestaurantForm({ groupId, restaurant, onSaved, onCancel }) {
  const isEdit = Boolean(restaurant)
  const [form, setForm] = useState(() => toForm(restaurant ?? EMPTY))
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function update(field) {
    return (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    const payload = toPayload(form)
    const message = validate(payload)
    if (message) return setError(message)

    let body = payload
    if (isEdit) {
      // 바뀐 필드만 보낸다. 보내지 않은 필드는 서버에서 그대로 유지된다.
      const original = toPayload(toForm(restaurant))
      body = Object.fromEntries(Object.entries(payload).filter(([key, value]) => value !== original[key]))
      if (Object.keys(body).length === 0) return onCancel()
    }

    setSubmitting(true)
    try {
      const saved = isEdit
        ? await api(`/groups/${groupId}/restaurants/${restaurant.id}`, { method: 'PATCH', body })
        : await api(`/groups/${groupId}/restaurants`, { method: 'POST', body })
      onSaved(saved)
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <form className="restaurant-form" onSubmit={handleSubmit}>
      <label>
        이름 <span className="required">필수</span>
        <input value={form.name} onChange={update('name')} maxLength={50} autoComplete="off" />
      </label>
      <div className="form-row">
        <label>
          카테고리 <span className="required">필수</span>
          <select value={form.category} onChange={update('category')}>
            <option value="">선택</option>
            {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          가격대
          <select value={form.price_level} onChange={update('price_level')}>
            {Object.entries(PRICE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          도보 시간(분)
          <input
            type="number"
            inputMode="numeric"
            min={0}
            max={60}
            step={1}
            value={form.walk_minutes}
            onChange={update('walk_minutes')}
            placeholder="모름"
          />
        </label>
      </div>
      <label>
        지도 링크
        <input
          type="url"
          value={form.map_url}
          onChange={update('map_url')}
          maxLength={500}
          placeholder="https://..."
          autoComplete="off"
        />
      </label>
      <label>
        메모 <span className="counter">{form.memo.length}/200</span>
        <textarea value={form.memo} onChange={update('memo')} maxLength={200} rows={2} />
      </label>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <div className="form-actions">
        <button type="button" onClick={onCancel} disabled={submitting}>
          취소
        </button>
        <button type="submit" className="primary" disabled={submitting}>
          {submitting ? '저장 중...' : isEdit ? '수정' : '등록'}
        </button>
      </div>
    </form>
  )
}

export default RestaurantForm
