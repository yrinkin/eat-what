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
