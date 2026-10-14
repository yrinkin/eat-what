// 브라우저 저장소. 저장소를 쓸 수 없는 환경(차단, 시크릿 제한)에서도 앱이 멈추지 않게 한다.
const TOKEN_KEY = 'lunch-token-v1'
const GROUP_KEY = 'lunch-group-v1'

function read(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key, value) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    // 저장하지 못하면 새로고침 후 다시 로그인·선택해야 한다.
  }
}

export const getToken = () => read(TOKEN_KEY)
export const saveToken = (token) => write(TOKEN_KEY, token)
export const clearToken = () => write(TOKEN_KEY, null)

// 마지막으로 연 그룹 id. 새로고침해도 같은 그룹 화면을 보여 주는 데만 쓴다.
export function getSavedGroupId() {
  const id = Number(read(GROUP_KEY))
  return Number.isInteger(id) && id > 0 ? id : null
}
export const saveGroupId = (id) => write(GROUP_KEY, id === null ? null : String(id))

export { TOKEN_KEY }
