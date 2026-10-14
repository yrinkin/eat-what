// 브라우저에 멤버 토큰을 저장한다. 저장소를 쓸 수 없는 환경(차단, 시크릿 제한)에서도 앱이 멈추지 않게 한다.
const TOKEN_KEY = 'lunch-token-v1'

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function saveToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // 저장하지 못하면 새로고침 후 다시 입장해야 한다.
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    // 무시
  }
}

export { TOKEN_KEY }
