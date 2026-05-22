const TOKEN_KEY = 'auth_token'

export function useAuth() {
  const getToken = () => localStorage.getItem(TOKEN_KEY)

  const hasToken = () => !!getToken()

  const setToken = (token) => localStorage.setItem(TOKEN_KEY, token)

  const removeToken = () => localStorage.removeItem(TOKEN_KEY)

  const login = (token) => setToken(token)

  const logout = () => removeToken()

  return {
    getToken,
    hasToken,
    setToken,
    removeToken,
    login,
    logout
  }
}