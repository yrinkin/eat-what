// API 값을 화면용 한국어로 바꾼다.
export const CATEGORY_LABELS = {
  KOREAN: '한식',
  CHINESE: '중식',
  JAPANESE: '일식',
  WESTERN: '양식',
  SNACK: '분식',
  ASIAN: '아시안',
  ETC: '기타',
}

export const PRICE_LABELS = {
  1: '1만 원 이하',
  2: '1~1.5만 원',
  3: '1.5만 원 초과',
}

export function walkLabel(minutes) {
  return minutes === null ? '도보 시간 미정' : `도보 ${minutes}분`
}

export function ratingLabel(avg, count) {
  return avg === null ? '별점 없음' : `★ ${avg.toFixed(1)} (${count})`
}

export function visitLabel(date) {
  return date === null ? '방문 기록 없음' : `최근 방문 ${date}`
}

// 마감 결과가 어떻게 정해졌는지 설명한다 (F11: 최다 득표, 동점이면 동점 후보 중, 표가 없으면 전체 후보 중 무작위).
export function decisionNote(candidates) {
  const total = candidates.reduce((sum, c) => sum + c.vote_count, 0)
  if (total === 0) return '표가 없어 후보 중에서 무작위로 정했어요.'
  const top = Math.max(...candidates.map((c) => c.vote_count))
  const tied = candidates.filter((c) => c.vote_count === top).length
  if (tied > 1) return `${tied}곳이 ${top}표로 동점이라 그중에서 무작위로 정했어요.`
  return `가장 많은 ${top}표를 받은 곳으로 정했어요.`
}
