import { getToken } from './token'

// API 오류. status와 API-SPEC.md의 code를 함께 담는다.
export class ApiError extends Error {
  constructor(status, code, message) {
    super(message)
    this.status = status
    this.code = code
  }
}

// 토큰을 보낸 요청이 401이면 이 이벤트를 보내 App이 로그인 화면으로 돌아가게 한다.
export const UNAUTHORIZED_EVENT = 'lunch:unauthorized'

export async function api(path, { method = 'GET', body } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let res
  try {
    res = await fetch(`/api/v1${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'NETWORK', '서버에 연결할 수 없습니다.')
  }

  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (res.ok) return data

  if (res.status === 401 && token) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))

  const detail = data?.detail
  if (Array.isArray(detail)) {
    throw new ApiError(res.status, 'VALIDATION', '입력값을 확인해 주세요.')
  }
  throw new ApiError(res.status, detail?.code ?? 'UNKNOWN', detail?.message ?? '요청을 처리하지 못했습니다.')
}
