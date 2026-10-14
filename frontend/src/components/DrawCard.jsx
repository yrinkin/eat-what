import { CATEGORY_LABELS, PRICE_LABELS, ratingLabel, walkLabel } from '../labels'

// 뒤집힌 카드. 누르면 앞면(식당 정보)이 보인다. 한 번 공개하면 다시 덮지 않는다.
function DrawCard({ candidate, index, revealed, onReveal }) {
  return (
    <button
      type="button"
      className={revealed ? 'draw-card revealed' : 'draw-card'}
      onClick={onReveal}
      disabled={revealed}
      aria-label={revealed ? `${index + 1}번 카드: ${candidate.name}` : `${index + 1}번 카드 뒤집기`}
    >
      <span className="draw-card-inner">
        <span className="draw-card-face draw-card-back" aria-hidden={revealed}>
          <span className="draw-card-mark">?</span>
          <span className="draw-card-hint">눌러서 공개</span>
        </span>
        <span className="draw-card-face draw-card-front" aria-hidden={!revealed}>
          <span className="badge">{CATEGORY_LABELS[candidate.category]}</span>
          <span className="draw-card-name">{candidate.name}</span>
          <span className="draw-card-meta">{PRICE_LABELS[candidate.price_level]}</span>
          <span className="draw-card-meta">{walkLabel(candidate.walk_minutes)}</span>
          <span className="draw-card-meta">{ratingLabel(candidate.avg_rating)}</span>
        </span>
      </span>
    </button>
  )
}

export default DrawCard
