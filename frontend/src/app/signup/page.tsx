'use client'

import { useState } from 'react'
import '../marketing-page.css'
import '../console.css'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function SignupPage() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName || undefined,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => null)
        const detail = data?.detail
        const message =
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((d: any) => d.msg || String(d)).join(', ')
              : 'Could not create your account.'
        setError(message)
        setSubmitting(false)
        return
      }

      // Registration succeeded — log the new user in immediately.
      const loginRes = await fetch(`${API_URL}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const loginData = await loginRes.json().catch(() => null)

      if (loginData?.access_token) {
        localStorage.setItem('token', loginData.access_token)
        window.location.href = '/console'
      } else {
        // Account was created but auto-login failed; send them to sign in manually.
        window.location.href = '/console'
      }
    } catch {
      setError('Could not reach the network. Try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="login-shell">
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;800&display=swap"
        rel="stylesheet"
      />
      <div className="login-card">
        <a href="/" className="login-logo">
          <img src="/brand/utachi-logo-white.png" alt="Utachi Industries" />
          <span className="mlogo-divider" />
          <span className="mlogo-product">Ultorn</span>
        </a>
        <span className="login-chip">[ Sovereign access ]</span>
        <h1 className="login-title">Create your account.</h1>
        <p className="login-sub">Set up client access to the Ultorn console.</p>

        <form className="login-form" onSubmit={submit}>
          <div className="login-field">
            <label className="login-label" htmlFor="signup-name">Full name</label>
            <input
              id="signup-name"
              className="login-input"
              type="text"
              placeholder="Optional"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
              autoFocus
            />
          </div>
          <div className="login-field">
            <label className="login-label" htmlFor="signup-email">Email</label>
            <input
              id="signup-email"
              className="login-input"
              type="email"
              placeholder="you@company.sn"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>
          <div className="login-field">
            <label className="login-label" htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              className="login-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>
          <div className="login-field">
            <label className="login-label" htmlFor="signup-confirm-password">Confirm password</label>
            <input
              id="signup-confirm-password"
              className="login-input"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>
          {error && <div className="login-error" role="alert">{error}</div>}
          <button type="submit" className="login-btn" disabled={submitting} aria-busy={submitting}>
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="login-hint">Use at least 8 characters. A longer passphrase is stronger.</p>
        <a href="/console" className="login-back">Already have an account? Sign in</a>
        <a href="/" className="login-back">← Back to home</a>
      </div>
    </div>
  )
}
