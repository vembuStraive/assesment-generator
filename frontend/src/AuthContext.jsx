/* Auth hook is intentionally colocated with its provider for this app. */
/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from './api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Check if user is already logged in on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      authAPI
        .getCurrentUser()
        .then(res => {
          setUser(res.data)
          setError(null)
        })
        .catch(() => {
          localStorage.removeItem('access_token')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email, password) => {
    setLoading(true)
    setError(null)
    try {
      const res = await authAPI.login(email, password)
      localStorage.setItem('access_token', res.data.access_token)
      // Fetch current user
      const userRes = await authAPI.getCurrentUser()
      setUser(userRes.data)
      return userRes.data
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Login failed'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const register = async (email, username, password) => {
    setLoading(true)
    setError(null)
    try {
      const res = await authAPI.register(email, username, password)
      return res.data
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Registration failed'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    setUser(null)
    setError(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, error, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
