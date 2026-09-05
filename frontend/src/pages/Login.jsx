import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import straiveLogo from '../assets/straive-logo.webp'
import './Auth.css'

export function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [formData, setFormData] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(formData.email, formData.password)
      navigate('/titles')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card login-card">
        <section className="login-brand-panel">
          <img className="straive-logo auth-logo" src={straiveLogo} alt="Straive" />
          <div className="login-brand-copy"><h1>AssessBridge</h1><p>Your assessment workspace</p></div>
          <span className="login-brand-note">Assessment workspace</span>
        </section>

        <section className="login-form-panel">
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="login-heading"><h2>Welcome back</h2><p>Sign in to continue to AssessBridge.</p></div>
            {error && <div className="error-message">{error}</div>}

            <div className="form-group">
              <label htmlFor="email">Email address</label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={e => setFormData({ ...formData, email: e.target.value })}
              required
              disabled={loading}
            />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={formData.password}
              onChange={e => setFormData({ ...formData, password: e.target.value })}
              required
              disabled={loading}
            />
            </div>

            <div className="login-options"><label><input type="checkbox" /> Remember me</label><a href="#">Forgot password?</a></div>

            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="auth-link">Don't have an account? <Link to="/register">Register here</Link></p>
        </section>
      </div>
    </div>
  )
}
