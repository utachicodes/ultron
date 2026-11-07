'use client'

import { useState, useEffect, useRef } from 'react'
import '../console.css'
import '../auth.css'
import AuthShell from '../../components/AuthShell'
import { PasswordField, TextField } from '../../components/auth-ui'
import Modal from '../../components/Modal'
import { useTheme } from '../../components/theme'
import { Button, ConfirmDialog, Field, Select, TextInput, Textarea, Toast } from './ui'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const ACCENT = 'var(--c-accent)'
const ACCENT_BRIGHT = 'var(--c-accent-bright)'
const ACCENT_SOFT = 'var(--c-accent-soft)'
const ACCENT_BORDER = 'var(--c-accent-border)'

// Operator-console surface system. Every color is a CSS variable so the
// light/dark switch repaints the workspace (including charts, fields and
// modals) without a second component tree.
const BG = 'var(--c-bg)'
const SURFACE = 'var(--c-surface)'
const SURFACE_RAISED = 'var(--c-surface-raised)'
const SURFACE_SUNKEN = 'var(--c-sunken)'
const BORDER = 'var(--c-border)'
const BORDER_STRONG = 'var(--c-border-strong)'
const TEXT = 'var(--c-text)'
const TEXT_DIM = 'var(--c-text-dim)'
const TEXT_FAINT = 'var(--c-text-faint)'
const MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

// One-click "try it" personas, seeded by `backend/seed_demo.py`. Only
// present on a server an operator chose to seed with demo data -- if none
// of these exist, the buttons below just surface the backend's normal
// "Incorrect email or password" error, same as any other login attempt.
const DEMO_ACCOUNTS = [
  {
    email: 'admin@ultorn.local',
    password: 'admin123',
    role: 'Admin',
    blurb: 'Full platform access: every client, user management, API keys.',
  },
  {
    email: 'analyst-demo@ultorn.local',
    password: 'demo-analyst-123',
    role: 'Analyst',
    blurb: 'Runs scans, reviews findings, cannot manage users.',
  },
  {
    email: 'client-demo@sahelbank.sn',
    password: 'demo-client-123',
    role: 'Client',
    blurb: "Sees only Sahel Bank's own scans and findings.",
  },
  {
    email: 'client-demo@dakarunitedfc.sn',
    password: 'demo-club-123',
    role: 'Club',
    blurb: "Sees only Dakar United FC's scans and findings, with the sports sector pack.",
  },
]

const ICONS: Record<string, React.ReactNode> = {
  dashboard: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" />
    </svg>
  ),
  clients: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="9" cy="8" r="3.2" /><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      <circle cx="17.5" cy="8.5" r="2.4" /><path d="M15.8 14.2c2.6.4 4.7 2.6 4.7 5.8" />
    </svg>
  ),
  scans: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" />
    </svg>
  ),
  findings: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3 2 20h20L12 3Z" /><path d="M12 10v4" /><circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />
    </svg>
  ),
  ai: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
      <circle cx="12" cy="12" r="3.2" />
    </svg>
  ),
  audit: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M6 3h9l4 4v14H6z" /><path d="M15 3v4h4M9 12h6M9 16h6M9 8h2" />
    </svg>
  ),
  admin: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="2.8" />
      <path d="M19.4 13.5a7.6 7.6 0 0 0 0-3l2-1.5-2-3.5-2.3.9a7.6 7.6 0 0 0-2.6-1.5L14 2h-4l-.5 2.4a7.6 7.6 0 0 0-2.6 1.5l-2.3-.9-2 3.5 2 1.5a7.6 7.6 0 0 0 0 3l-2 1.5 2 3.5 2.3-.9c.77.66 1.65 1.17 2.6 1.5L10 22h4l.5-2.4a7.6 7.6 0 0 0 2.6-1.5l2.3.9 2-3.5-2-1.5Z" />
    </svg>
  ),
  collapse: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M15 5l-7 7 7 7" />
    </svg>
  ),
  menu: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 6h18M3 12h18M3 18h18" />
    </svg>
  ),
  close: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  ),
  monitors: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21v-2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2" />
    </svg>
  ),
  alerts: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M10 20v4M14 20v4M12 13V8M12 8l-1-1M12 8l1-1" />
      <circle cx="12" cy="17" r="1" />
    </svg>
  ),
  code: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
    </svg>
  ),
  compliance: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="3" />
    </svg>
  ),
  authz: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3 4 6.5v5.2c0 5 3.4 8.9 8 10.3 4.6-1.4 8-5.3 8-10.3V6.5L12 3Z" />
      <path d="M9.5 12.2l1.8 1.8 3.3-3.6" />
    </svg>
  ),
  reports: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><path d="M16 13h-4M16 17h-4" />
    </svg>
  ),
  schedules: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />
    </svg>
  ),
  sun: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  ),
  moon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.5 14.1A8.5 8.5 0 0 1 9.9 3.5a8.5 8.5 0 1 0 10.6 10.6Z" />
    </svg>
  ),
}

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/

function LoginScreen({ onToken, notice }: { onToken: (token: string) => void; notice?: string }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [emailError, setEmailError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [demoLoading, setDemoLoading] = useState<string | null>(null)
  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)

  const authenticate = async (loginEmail: string, loginPassword: string) => {
    const res = await fetch(`${API_URL}/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: loginEmail, password: loginPassword }),
    })
    return res.json()
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate locally first: /auth/token is rate-limited (10 attempts per
    // minute per IP), so an obviously empty form should never spend one.
    const nextEmailError =
      email.trim() === ''
        ? 'Enter your email address.'
        : EMAIL_PATTERN.test(email.trim())
          ? ''
          : 'Check the email address format.'
    const nextPasswordError = password === '' ? 'Enter your password.' : ''
    setEmailError(nextEmailError)
    setPasswordError(nextPasswordError)
    if (nextEmailError) {
      emailRef.current?.focus()
      return
    }
    if (nextPasswordError) {
      passwordRef.current?.focus()
      return
    }

    setSubmitting(true)
    try {
      const data = await authenticate(email.trim(), password)
      if (data.access_token) {
        localStorage.setItem('token', data.access_token)
        onToken(data.access_token)
      } else {
        setError(data.detail || 'Login failed')
      }
    } catch {
      setError('Could not reach the network. Try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const loginAsDemo = async (account: (typeof DEMO_ACCOUNTS)[number]) => {
    setError('')
    setDemoLoading(account.email)
    try {
      const data = await authenticate(account.email, account.password)
      if (data.access_token) {
        localStorage.setItem('token', data.access_token)
        onToken(data.access_token)
      } else {
        setError(
          `Could not sign in as the demo ${account.role.toLowerCase()} account. ` +
            `Has this server been seeded with demo data (python seed_demo.py)?`
        )
      }
    } catch {
      setError('Could not reach the network. Try again.')
    } finally {
      setDemoLoading(null)
    }
  }

  return (
    <AuthShell>
      <span className="auth-kicker">Sovereign access</span>
      <h1 className="auth-title">Welcome back.</h1>
      <p className="auth-sub">Sign in to the operator console.</p>
      {notice && (
        <div className="auth-notice" role="status">
          {notice}
        </div>
      )}

      <form className="auth-form" onSubmit={submit} noValidate>
        <TextField
          id="login-email"
          label="Email"
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            if (emailError) setEmailError('')
          }}
          autoComplete="email"
          placeholder="you@company.sn"
          inputRef={emailRef}
          error={emailError}
          autoFocus
        />
        <PasswordField
          id="login-password"
          label="Password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value)
            if (passwordError) setPasswordError('')
          }}
          autoComplete="current-password"
          inputRef={passwordRef}
          error={passwordError}
          labelAction={
            <a className="auth-inline-link" href="/forgot-password">
              Forgot password?
            </a>
          }
        />

        {error && (
          <div className="login-error" role="alert">
            {error}
          </div>
        )}

        <button type="submit" className="auth-submit" disabled={submitting} aria-busy={submitting}>
          {submitting && <span className="auth-spinner" aria-hidden="true" />}
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <p className="auth-hint">Access is provisioned by your Ultorn administrator.</p>

      <div className="auth-divider" role="separator">
        <span>or explore first</span>
      </div>

      <div className="auth-demo" role="group" aria-label="Try a demo account">
        {DEMO_ACCOUNTS.map((account) => (
          <button
            key={account.email}
            type="button"
            className="auth-demo-btn"
            onClick={() => loginAsDemo(account)}
            disabled={demoLoading !== null}
            aria-busy={demoLoading === account.email}
          >
            <span className="auth-demo-text">
              <span className="auth-demo-role">
                {demoLoading === account.email ? 'Signing in…' : `Try as ${account.role}`}
              </span>
              <span className="auth-demo-blurb">{account.blurb}</span>
            </span>
            <span className="auth-demo-arrow" aria-hidden="true">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </span>
          </button>
        ))}
      </div>
      <p className="auth-hint">
        Demo accounts drop you straight into the console with sample clients and findings already loaded.
      </p>

      <div className="auth-links">
        <span>New to Ultorn?</span>
        <a className="auth-link-strong" href="/signup">
          Create an account
        </a>
      </div>
    </AuthShell>
  )
}

function ChangePasswordButton({
  api,
  onChanged,
}: {
  api: (path: string, opts?: RequestInit) => Promise<any>
  onChanged: (notice: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const close = () => {
    if (saving) return
    setOpen(false)
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
    setError('')
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (newPassword.length < 8) {
      setError('Use at least 8 characters for the new password.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('The new passwords do not match.')
      return
    }
    if (newPassword === currentPassword) {
      setError('Choose a password different from the current one.')
      return
    }

    setSaving(true)
    try {
      await api('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })
      onChanged('Password changed. Sign in with your new password.')
    } catch (e: any) {
      setError(e.message || 'Could not change the password')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
          background: 'transparent',
          border: '1px solid var(--c-border-strong)',
          color: 'var(--c-text-soft)',
          padding: '0.5rem 0.9rem',
          borderRadius: 0,
          cursor: 'pointer',
          fontSize: '0.8rem',
          fontWeight: 500,
          minHeight: '40px',
          marginBottom: '0.5rem',
        }}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
          <rect x="4" y="10" width="16" height="11" rx="2" />
          <path d="M8 10V7a4 4 0 0 1 8 0v3" />
        </svg>
        Change password
      </button>

      {open && (
        <Modal title="Change password" onClose={close}>
          <form onSubmit={submit}>
            {error && (
              <div role="alert" style={{ color: 'var(--c-danger)', fontSize: '0.82rem', marginBottom: '0.8rem' }}>
                {error}
              </div>
            )}
            <Field label="Current password" htmlFor="account-current-password" tone="dark" required>
              <TextInput
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
                autoFocus
              />
            </Field>
            <Field
              label="New password"
              htmlFor="account-new-password"
              tone="dark"
              required
              hint="At least 8 characters. A longer passphrase is stronger."
            >
              <TextInput
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
              />
            </Field>
            <Field label="Confirm new password" htmlFor="account-confirm-password" tone="dark" required>
              <TextInput
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
              />
            </Field>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <Button type="submit" loading={saving}>Update password</Button>
              <Button variant="secondaryDark" onClick={close} disabled={saving}>Cancel</Button>
            </div>
            <p style={{ color: 'var(--c-text-dim)', fontSize: '0.78rem', margin: '0.9rem 0 0' }}>
              You will be signed out and asked to sign in with the new password.
            </p>
          </form>
        </Modal>
      )}
    </>
  )
}

// ============================================================
// Shared: stat tile, badge, split list/detail panel
// ============================================================
function StatCard({
  label,
  value,
  hint,
  tone = 'neutral',
  emphasis = false,
}: {
  label: string
  value: string | number
  hint?: string
  tone?: 'neutral' | 'danger' | 'warning' | 'success'
  emphasis?: boolean
}) {
  const valueColor =
    tone === 'danger' ? 'var(--c-danger-strong)' : tone === 'warning' ? 'var(--c-warn)' : tone === 'success' ? 'var(--c-success)' : TEXT
  return (
    <div style={{ ...styles.statCard, ...(emphasis ? styles.statCardEmphasis : {}) }}>
      <div style={styles.statLabel}>{label}</div>
      <div style={{ ...styles.statValue, color: valueColor }}>{value}</div>
      {hint && <div style={styles.statHint}>{hint}</div>}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={styles.metricItem}>
      <div style={styles.metricValue}>{value}</div>
      <div style={styles.metricLabel}>{label}</div>
    </div>
  )
}

function Badge({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: string }) {
  const tones: any = {
    neutral: { background: 'var(--c-wash)', color: 'var(--c-text-dim)' },
    success: { background: 'var(--c-success-soft)', color: 'var(--c-success)' },
    warning: { background: 'var(--c-warn-soft)', color: 'var(--c-warn)' },
    danger: { background: 'var(--c-danger-soft)', color: 'var(--c-danger)' },
    accent: { background: ACCENT_SOFT, color: 'var(--c-accent-violet)' },
  }
  return (
    <span style={{ ...styles.badge, ...tones[tone] }}>{children}</span>
  )
}

function SplitPanel({
  title,
  action,
  items,
  selectedId,
  onSelect,
  renderRow,
  renderDetail,
  emptyLabel,
  emptyHint,
  loading = false,
}: {
  title: string
  action?: React.ReactNode
  items: any[]
  selectedId: any
  onSelect: (item: any) => void
  renderRow: (item: any, selected: boolean) => React.ReactNode
  renderDetail: (item: any) => React.ReactNode
  emptyLabel: string
  emptyHint?: string
  loading?: boolean
}) {
  const selected = items.find((i) => i.id === selectedId) || null

  return (
    <div style={styles.panelDark}>
      <div style={styles.panelHeader}>
        <h3 style={styles.panelTitle}>{title}</h3>
        {action}
      </div>
      <div style={styles.panelBody} className="split-panel-body">
        <div style={styles.listPane} className="split-panel-list">
          {loading && items.length === 0 && (
            <div style={styles.emptyState} role="status" aria-live="polite">Loading…</div>
          )}
          {!loading && items.length === 0 && (
            <div style={styles.emptyState}>
              <div>{emptyLabel}</div>
              {emptyHint && <div style={{ marginTop: '0.4rem', fontSize: '0.8rem', opacity: 0.85 }}>{emptyHint}</div>}
            </div>
          )}
          {items.map((item) => {
            const isSelected = item.id === selectedId
            return (
              <button
                key={item.id}
                type="button"
                className="list-row-button"
                onClick={() => onSelect(item)}
                aria-current={isSelected ? 'true' : undefined}
                style={{
                  ...styles.listRow,
                  ...(isSelected ? styles.listRowActive : {}),
                }}
              >
                {renderRow(item, isSelected)}
              </button>
            )
          })}
        </div>
        <div style={styles.detailPane} className="split-panel-detail">
          {selected ? renderDetail(selected) : (
            <div style={styles.emptyState}>Select an item to see details.</div>
          )}
        </div>
      </div>
    </div>
  )
}

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type ToastTone = 'info' | 'error' | 'success'

function Page() {
  const { theme, toggle } = useTheme()
  const [token, setToken] = useState<string | null>(null)
  const [authNotice, setAuthNotice] = useState('')

  useEffect(() => {
    setToken(localStorage.getItem('token'))
  }, [])
  const [user, setUser] = useState<any>(null)
  const [view, setView] = useState('dashboard')
  const [clients, setClients] = useState<any[]>([])
  const [scans, setScans] = useState<any[]>([])
  const [findings, setFindings] = useState<any[]>([])
  const [audit, setAudit] = useState<any[]>([])
  const [monitors, setMonitors] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [codeScans, setCodeScans] = useState<any[]>([])
  const [authzHunts, setAuthzHunts] = useState<any[]>([])
  const [prReviews, setPrReviews] = useState<any[]>([])
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [redteamRuns, setRedteamRuns] = useState<any[]>([])
  const [message, setMessage] = useState<{ text: string; type: ToastTone } | null>(null)
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const messageTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  /**
   * Drop every tenant-scoped value together. Without this, a persona switch
   * could render the next role with the previous user's `canManage` flag for
   * the first frame -- which made a Client's dashboard request /audit, get a
   * 403, and show "Insufficient permissions" until a full reload.
   */
  const clearWorkspace = () => {
    if (messageTimer.current) {
      clearTimeout(messageTimer.current)
      messageTimer.current = null
    }
    setMessage(null)
    setUser(null)
    setClients([])
    setScans([])
    setFindings([])
    setAudit([])
    setMonitors([])
    setAlerts([])
    setCodeScans([])
    setAuthzHunts([])
    setPrReviews([])
    setCampaigns([])
    setRedteamRuns([])
    setView('dashboard')
    setMobileOpen(false)
  }

  const signOut = () => {
    localStorage.removeItem('token')
    setToken(null)
    clearWorkspace()
  }

  useEffect(() => {
    setCollapsed(localStorage.getItem('ultorn_sidebar_collapsed') === 'true')
  }, [])

  // Escape closes the mobile drawer, same as the backdrop or a nav choice.
  useEffect(() => {
    if (!mobileOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [mobileOpen])

  useEffect(() => {
    if (!token) return
    // The token changed: do not keep the previous account's profile around
    // while /auth/me is in flight, and abort that request on sign-out so a
    // late response cannot restore the previous persona.
    const controller = new AbortController()
    setUser(null)
    fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    })
      .then((r) => {
        if (r.status === 401) throw new Error('Session expired')
        if (!r.ok) throw new Error('Could not load your profile')
        return r.json()
      })
      .then((data) => {
        if (!controller.signal.aborted) setUser(data)
      })
      .catch(() => {
        if (controller.signal.aborted) return
        localStorage.removeItem('token')
        setToken(null)
        clearWorkspace()
      })
    return () => controller.abort()
  }, [token])

  useEffect(() => () => {
    if (messageTimer.current) clearTimeout(messageTimer.current)
  }, [])

  /**
   * One API entry point: normalises errors, parses JSON safely, and sends the
   * user back to sign-in when their session is no longer valid.
   */
  const api = async (path: string, opts: RequestInit = {}) => {
    let res: Response
    try {
      res = await fetch(`${API_URL}${path}`, {
        ...opts,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(opts.headers || {}),
        },
      })
    } catch {
      throw new ApiError('Cannot reach the API. Check that the backend is running.', 0)
    }

    if (res.status === 401) {
      localStorage.removeItem('token')
      setToken(null)
      clearWorkspace()
      throw new ApiError('Your session expired. Please sign in again.', 401)
    }

    const raw = await res.text()
    let data: any = null
    if (raw) {
      try {
        data = JSON.parse(raw)
      } catch {
        data = raw
      }
    }

    if (!res.ok) {
      const detail =
        typeof data?.detail === 'string'
          ? data.detail
          : Array.isArray(data?.detail)
            ? data.detail.map((d: any) => d.msg || String(d)).join(', ')
            : `Request failed (${res.status})`
      throw new ApiError(detail, res.status)
    }

    return data
  }

  const notify = (text: string, type: ToastTone = 'info') => {
    if (messageTimer.current) clearTimeout(messageTimer.current)
    setMessage({ text, type })
    messageTimer.current = setTimeout(() => setMessage(null), 5000)
  }

  // ---------- LOGIN ----------
  if (!token) {
    return (
      <LoginScreen
        notice={authNotice}
        onToken={(t: string) => {
          setAuthNotice('')
          clearWorkspace()
          setToken(t)
        }}
      />
    )
  }

  // The profile decides what the console may show. Gate on it so a previous
  // persona's role and permissions can never paint the next session.
  if (!user) {
    return (
      <div style={{ ...styles.shell, alignItems: 'center', justifyContent: 'center' }}>
        <div role="status" aria-live="polite" style={{ textAlign: 'center', color: TEXT_DIM }}>
          <div className="console-workspace-loader" aria-hidden="true" />
          <p style={{ margin: '1rem 0 0', fontSize: '0.85rem' }}>Loading your workspace…</p>
        </div>
      </div>
    )
  }

  // Mirrors the backend's `require_role(admin, analyst)` gate used on every
  // create/update/delete endpoint. A client-role user can read their own
  // data everywhere but never mutate it -- the UI should never offer a
  // control that the API will then reject.
  const canManage = user?.role === 'admin' || user?.role === 'analyst'
  const isAdmin = user?.role === 'admin'

  // The sidebar names the workspace, not just the role: a client landing in
  // the same console shell should see their own organization, not internal
  // operator framing.
  const clientOrg = user?.role === 'client' ? clients[0] : null
  const isClubPortal = user?.role === 'client' && clientOrg?.sector === 'sports'
  const workspaceLabel =
    user?.role === 'admin'
      ? 'Admin workspace'
      : user?.role === 'analyst'
        ? 'Analyst workspace'
        : isClubPortal
          ? 'Club portal'
          : 'Client portal'

  // Grouped so no menu exposes more than four choices at once (Hick's Law),
  // and ordered by the job an analyst is doing rather than by internal module.
  //
  // The client role gets a structurally separate nav list (CLIENT_NAV_GROUPS),
  // not a filtered view of the operator one: a client never configures scans,
  // monitors, schedules, code scans or AI Guard -- those are the tooling that
  // *produces* findings/alerts, not something a client reads or tunes. Keeping
  // the two lists apart means a future change to operator nav can't silently
  // change what a client sees, and vice versa.
  const isClient = user?.role === 'client'

  const OPERATOR_NAV_GROUPS = [
    {
      label: 'Overview',
      items: [{ key: 'dashboard', label: 'Dashboard', icon: 'dashboard' }],
    },
    {
      label: 'Operations',
      items: [
        { key: 'clients', label: 'Clients', icon: 'clients' },
        { key: 'scans', label: 'Scans', icon: 'scans' },
        { key: 'findings', label: 'Findings', icon: 'findings' },
      ],
    },
    {
      label: 'Monitoring',
      items: [
        { key: 'monitors', label: 'Monitors', icon: 'monitors' },
        { key: 'alerts', label: 'Alerts', icon: 'alerts' },
        { key: 'schedules', label: 'Scan Schedules', icon: 'schedules' },
      ],
    },
    {
      label: 'Analysis',
      items: [
        { key: 'code-scans', label: 'Code Scans', icon: 'code' },
        { key: 'authz', label: 'Authorization Hunts', icon: 'authz' },
        { key: 'pr-reviews', label: 'PR Reviews', icon: 'code' },
        { key: 'campaigns', label: 'Campaigns', icon: 'schedules' },
        { key: 'ai-redteam', label: 'AI Red-Team', icon: 'ai' },
        { key: 'compliance', label: 'Compliance', icon: 'compliance' },
        { key: 'reports', label: 'Reports', icon: 'reports' },
        { key: 'ai', label: 'AI Guard', icon: 'ai' },
      ],
    },
    // Audit (admin/analyst only on the backend) and Admin (admin only) are
    // left out of this group entirely for roles that can't open them --
    // a nav link to a page that only throws a 403 is a dead end, not a
    // feature, and hiding it beats showing an error after the fact.
    {
      label: 'Governance',
      items: [
        ...(canManage ? [{ key: 'audit', label: 'Audit', icon: 'audit' }] : []),
        ...(user?.role === 'admin' ? [{ key: 'admin', label: 'Admin', icon: 'admin' }] : []),
      ],
    },
  ].filter((group) => group.items.length > 0)

  // A client reads results, not operator tooling: Dashboard, Organization,
  // Findings, Alerts, Compliance, Reports. No Scans, Monitors, Schedules,
  // Code Scans or AI Guard.
  const CLIENT_NAV_GROUPS = [
    {
      label: 'Overview',
      items: [{ key: 'dashboard', label: 'Dashboard', icon: 'dashboard' }],
    },
    {
      label: 'Operations',
      items: [
        { key: 'clients', label: 'Organization', icon: 'clients' },
        { key: 'findings', label: 'Findings', icon: 'findings' },
        { key: 'alerts', label: 'Alerts', icon: 'alerts' },
      ],
    },
    {
      label: 'Analysis',
      items: [
        { key: 'compliance', label: 'Compliance', icon: 'compliance' },
        { key: 'reports', label: 'Reports', icon: 'reports' },
      ],
    },
  ]

  const NAV_GROUPS = isClient ? CLIENT_NAV_GROUPS : OPERATOR_NAV_GROUPS

  const currentLabel = NAV_GROUPS.flatMap((g) => g.items).find((i) => i.key === view)?.label || 'Ultorn'

  const ctx = {
    token, api, notify, user, canManage, isAdmin,
    clients, setClients,
    scans, setScans,
    findings, setFindings,
    audit, setAudit,
    monitors, setMonitors,
    alerts, setAlerts,
    codeScans, setCodeScans,
    authzHunts, setAuthzHunts,
    prReviews, setPrReviews,
    campaigns, setCampaigns,
    redteamRuns, setRedteamRuns,
    setView,
  }

  // ---------- MAIN LAYOUT ----------
  return (
    <div className="console-shell" style={styles.shell}>
      <div
        className={`console-backdrop${mobileOpen ? ' open' : ''}`}
        onClick={() => setMobileOpen(false)}
      />

      <aside id="console-sidebar" className={`console-sidebar${collapsed ? ' collapsed' : ''}${mobileOpen ? ' mobile-open' : ''}`} style={styles.sidebar}>
        <div className="sidebar-brand" style={styles.sidebarBrand}>
          <img
            src={theme === 'light' ? '/brand/utachi-logo.png' : '/brand/utachi-logo-white.png'}
            alt="Utachi Industries"
            className="sidebar-logo-img"
            style={styles.navBrandLogo}
          />
          <span className="sidebar-brand-text-wrap">
            <span style={styles.navBrandDivider} />
            <span className="sidebar-brand-text" style={styles.sidebarBrandText}>Ultorn</span>
          </span>
          <button
            className="sidebar-collapse-btn"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={() => setCollapsed((v) => { localStorage.setItem('ultorn_sidebar_collapsed', (!v).toString()); return !v })}
          >
            {ICONS.collapse}
          </button>
          <button
            type="button"
            className="sidebar-close-btn"
            aria-label="Close menu"
            onClick={() => setMobileOpen(false)}
          >
            {ICONS.close}
          </button>
        </div>

        <div className="sidebar-role">
          <span className="sidebar-role-dot" aria-hidden="true" />
          <span className="sidebar-label">
            {workspaceLabel}
            {clientOrg && <span className="sidebar-role-org"> · {clientOrg.name}</span>}
          </span>
        </div>

        <a
          href="/"
          className="sidebar-link sidebar-home"
          aria-label="Back to landing page"
          title="Back to landing page"
          style={{
            ...styles.sidebarLink,
            color: 'var(--c-sidebar-label)',
            fontSize: '0.8rem',
            margin: '0 0.5rem 0.25rem',
            padding: '0.55rem 0.9rem',
            textDecoration: 'none',
          }}
        >
          <span style={styles.sidebarIcon} aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5" /><path d="M11 18l-6-6 6-6" />
            </svg>
          </span>
          <span className="sidebar-label">Back to landing page</span>
        </a>

        <div style={styles.sidebarNavScroll} className="console-scroll">
          {NAV_GROUPS.map((group) => (
            <nav key={group.label} aria-label={`${group.label} navigation`} style={styles.sidebarNav}>
              <div className="sidebar-group-label" style={styles.sidebarGroupLabel} aria-hidden="true">{group.label}</div>
              {group.items.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => { setView(item.key); setMobileOpen(false) }}
                  aria-current={view === item.key ? 'page' : undefined}
                  style={view === item.key ? { ...styles.sidebarLink, ...styles.sidebarLinkActive } : styles.sidebarLink}
                  className="sidebar-link"
                >
                  <span style={styles.sidebarIcon} aria-hidden="true">{ICONS[item.icon]}</span>
                  <span className="sidebar-label">{item.label}</span>
                </button>
              ))}
            </nav>
          ))}
        </div>

        <div style={styles.sidebarFooter}>
          <div className="sidebar-user" style={styles.sidebarUser}>
            <div style={styles.sidebarAvatar}>{(user?.email || '?')[0].toUpperCase()}</div>
            <div className="sidebar-user-info" style={{ minWidth: 0 }}>
              <div style={styles.sidebarUserEmail}>{user?.email || '…'}</div>
              <div style={styles.sidebarUserRole}>
                {user?.role || ''}
                {clientOrg ? ` · ${clientOrg.name}` : ''}
              </div>
            </div>
          </div>
          <button
            type="button"
            className="sidebar-theme-btn"
            onClick={toggle}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            <span style={styles.sidebarIcon} aria-hidden="true">
              {theme === 'dark' ? ICONS.sun : ICONS.moon}
            </span>
            <span className="sidebar-label">{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
          </button>
          <ChangePasswordButton
            api={api}
            onChanged={(notice) => {
              setAuthNotice(notice)
              signOut()
            }}
          />
          <button onClick={signOut} style={styles.sidebarSignOut}>
            Sign out
          </button>
        </div>
      </aside>

      <div className="console-main" style={{ flex: 1, minWidth: 0 }}>
        <div className="console-mobile-bar">
          <button
            className="sidebar-burger"
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileOpen}
            aria-controls="console-sidebar"
            onClick={() => setMobileOpen((v) => !v)}
          >
            {ICONS.menu}
          </button>
          <img
            src={theme === 'light' ? '/brand/utachi-logo.png' : '/brand/utachi-logo-white.png'}
            alt="Utachi Industries"
            style={{ height: '20px' }}
          />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{currentLabel}</span>
          <button
            type="button"
            className="mobile-theme-btn"
            onClick={toggle}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? ICONS.sun : ICONS.moon}
          </button>
        </div>

        <main style={styles.main}>
          {message && (
            <div className="console-toast-wrap">
              <Toast message={message.text} tone={message.type} onDismiss={() => setMessage(null)} />
            </div>
          )}

          {view === 'dashboard' && (
            isClient
              ? <ClientDashboard key={user?.email} ctx={ctx} />
              : <Dashboard key={user?.email} ctx={ctx} />
          )}
          {view === 'clients' && <ClientsSection ctx={ctx} />}
          {view === 'scans' && <ScansSection ctx={ctx} />}
          {view === 'findings' && <FindingsSection ctx={ctx} />}
          {view === 'ai' && <AISection ctx={ctx} />}
          {view === 'audit' && <AuditSection ctx={ctx} />}
          {view === 'admin' && user?.role === 'admin' && <AdminSection ctx={ctx} />}
          {view === 'monitors' && <MonitorsSection ctx={ctx} />}
          {view === 'alerts' && <AlertsSection ctx={ctx} />}
          {view === 'schedules' && <SchedulesSection ctx={ctx} />}
          {view === 'code-scans' && <CodeScansSection ctx={ctx} />}
          {view === 'authz' && <AuthzSection ctx={ctx} />}
          {view === 'pr-reviews' && <PRReviewsSection ctx={ctx} />}
          {view === 'campaigns' && <CampaignsSection ctx={ctx} />}
          {view === 'ai-redteam' && <AIRedTeamSection ctx={ctx} />}
          {view === 'compliance' && <ComplianceSection ctx={ctx} />}
          {view === 'reports' && <ReportsSection ctx={ctx} />}
        </main>
      </div>
    </div>
  )
}

// ============================================================
// Sections — module-level components (never redefined on re-render)
// ============================================================
function severityTone(s: string) {
  switch (s) {
    case 'critical': return 'danger'
    case 'high': return 'warning'
    case 'medium': return 'accent'
    default: return 'neutral'
  }
}

const SECTOR_LABELS: Record<string, string> = {
  banking: 'Banking / Mobile Money',
  telecom: 'Telecom',
  government: 'Government',
  sports: 'Sports (club / federation / academy)',
  other: 'Other',
}
function sectorLabel(sector: string) {
  return SECTOR_LABELS[sector] || sector
}

function Dashboard({ ctx }: { ctx: any }) {
  const { api, token, clients, setClients, scans, setScans, audit, setAudit, setView, canManage, user } = ctx
    const [stats, setStats] = useState<any>({})
    const [alerts, setAlerts] = useState<any[]>([])
    const [monitors, setMonitors] = useState<any[]>([])
    const [codeIssues, setCodeIssues] = useState(0)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    const load = async () => {
      setLoading(true)
      setError('')
      try {
        // /audit is admin/analyst only on the backend (403 for a client
        // role). Bundling it into the same Promise.all as everything else
        // used to fail the *entire* dashboard for a client user over one
        // endpoint they were never going to be allowed to call -- skip it
        // up front instead of asking and handling the rejection.
        const [scansData, clientsData, auditData, alertsData, monitorsData, codeData] = await Promise.all([
          api('/scans'),
          api('/clients'),
          canManage ? api('/audit?limit=8') : Promise.resolve([]),
          api('/alerts'),
          api('/monitors'),
          api('/code-scans'),
        ])
        const allScans = Array.isArray(scansData) ? scansData : []
        setScans(allScans)
        setClients(Array.isArray(clientsData) ? clientsData : [])
        setAudit(Array.isArray(auditData) ? auditData : [])
        setAlerts(Array.isArray(alertsData) ? alertsData : [])
        setMonitors(Array.isArray(monitorsData) ? monitorsData : [])
        setStats({
          totalScans: allScans.length,
          critical: allScans.reduce((acc: number, s: any) => acc + (s.summary?.critical || 0), 0),
          high: allScans.reduce((acc: number, s: any) => acc + (s.summary?.high || 0), 0),
        })
        setCodeIssues(
          (Array.isArray(codeData) ? codeData : []).reduce((acc: number, s: any) => acc + (s.issues_found || 0), 0)
        )
      } catch (e: any) {
        setError(e.message || 'Could not load the dashboard')
      } finally {
        setLoading(false)
      }
    }

    // Re-run if the loaded profile changes (e.g. a persona switch), not just
    // when the token string changes: a client must never inherit an analyst's
    // /audit request from the previous session.
    useEffect(() => { load() }, [token, user?.role])

    const openAlerts = alerts.filter((a: any) => a.status === 'open')
    const activeMonitors = monitors.filter((m: any) => m.is_active)

    // The dashboard is deliberately role-shaped. A client sees their own
    // posture (and is told so); an analyst gets the review queue; an admin
    // gets platform governance. Same data plane, different job.
    const role = user?.role
    const isAdmin = role === 'admin'
    const isAnalyst = role === 'analyst'
    const isClient = role === 'client'
    const org = isClient ? clients[0] : null
    const isClub = isClient && org?.sector === 'sports'
    const workspaceLabel = isAdmin
      ? 'Admin workspace'
      : isAnalyst
        ? 'Analyst workspace'
        : isClub
          ? 'Club portal'
          : 'Client portal'
    const scopeLabel = isAdmin ? 'Entire platform' : isAnalyst ? 'All clients' : org?.name || 'Your organization'
    const dashboardTitle = isAdmin
      ? 'Platform overview'
      : isAnalyst
        ? 'Operations overview'
        : isClub
          ? 'Club security posture'
          : 'Your security posture'
    const subtitle = isAdmin
      ? 'Platform-wide posture across every client, scan, monitor and code review.'
      : isAnalyst
        ? 'Operations queue across all clients: findings to review, scans, and live alerts.'
        : `Your security posture across scans, monitoring and code review${org ? ` for ${org.name}` : ''}. You only see your own data.`
    const reviewCount = scans.reduce((acc: number, s: any) => acc + (s.summary?.requires_human_review || 0), 0)
    const reviewScans = scans.filter((s: any) => (s.summary?.requires_human_review || 0) > 0)

    const header = (
      <div style={styles.dashHead}>
        <div style={{ minWidth: 0 }}>
          <div style={styles.roleEyebrow}>
            <span style={styles.roleDot} aria-hidden="true" />
            {workspaceLabel}
          </div>
          <h1 style={styles.dashTitle}>{dashboardTitle}</h1>
          <p style={styles.dashSub}>{subtitle}</p>
        </div>
        <div style={styles.scopeChip} title="Data visible to this account">
          <span style={styles.scopeChipLabel}>Scope</span>
          <span style={styles.scopeChipValue}>{scopeLabel}</span>
        </div>
      </div>
    )

    // Four primary risk indicators first; activity counts are secondary.
    const primary = (
      <div style={styles.statGrid}>
        <StatCard
          emphasis
          label="Critical findings"
          value={stats.critical || 0}
          tone={(stats.critical || 0) > 0 ? 'danger' : 'success'}
          hint={(stats.critical || 0) > 0 ? 'Requires human review' : 'None outstanding'}
        />
        <StatCard
          emphasis
          label="Open alerts"
          value={openAlerts.length}
          tone={openAlerts.length > 0 ? 'warning' : 'success'}
          hint={openAlerts.length > 0 ? 'Needs triage' : 'All clear'}
        />
        {isAdmin ? (
          <StatCard
            emphasis
            label="Clients protected"
            value={clients.length}
            tone="neutral"
            hint="Across the platform"
          />
        ) : isAnalyst ? (
          <StatCard
            emphasis
            label="Awaiting review"
            value={reviewCount}
            tone={reviewCount > 0 ? 'warning' : 'success'}
            hint={reviewScans.length > 0 ? `Across ${reviewScans.length} scans` : 'Queue clear'}
          />
        ) : (
          <StatCard
            emphasis
            label="Code issues"
            value={codeIssues}
            tone={codeIssues > 0 ? 'warning' : 'success'}
            hint="Across code scans"
          />
        )}
        <StatCard
          emphasis
          label="Active monitors"
          value={activeMonitors.length}
          tone="neutral"
          hint={`${monitors.length} configured`}
        />
      </div>
    )

    const rolePanel = (
      <div style={styles.rolePanel}>
        <div style={{ minWidth: 0 }}>
          <div style={styles.rolePanelKicker}>
            {isAdmin ? 'Workspace governance' : isAnalyst ? 'Review queue' : 'Your organization'}
          </div>
          <div style={styles.rolePanelText}>
            {isAdmin &&
              `${clients.length} ${clients.length === 1 ? 'client' : 'clients'} · ${stats.totalScans || 0} scans · ${monitors.length} monitors under management.`}
            {isAnalyst &&
              (reviewCount > 0
                ? `${reviewCount} finding${reviewCount === 1 ? '' : 's'} awaiting a human decision across ${reviewScans.length} scan${reviewScans.length === 1 ? '' : 's'}.`
                : 'The review queue is clear — no findings are waiting for a human decision.')}
            {isClient &&
              `${org?.name || 'Your organization'} · ${sectorLabel(org?.sector || 'other')}. This workspace is scoped to your own scans, findings and alerts.`}
          </div>
        </div>
        <button
          type="button"
          onClick={() => setView(isAdmin ? 'admin' : isAnalyst ? 'findings' : 'clients')}
          style={styles.darkActionBtn}
        >
          {isAdmin ? 'Open admin' : isAnalyst ? 'Review findings' : 'View organization'}
        </button>
      </div>
    )

    if (loading) {
      return (
        <div style={styles.section}>
          {header}
          <div style={styles.statGrid} role="status" aria-live="polite">
            <div style={styles.skeleton} />
            <div style={styles.skeleton} />
            <div style={styles.skeleton} />
            <div style={styles.skeleton} />
            <span className="sr-only">Loading dashboard</span>
          </div>
        </div>
      )
    }

    if (error) {
      return (
        <div style={styles.section}>
          {header}
          <div style={styles.lightCard}>
            <h3 style={styles.h3}>Could not load the dashboard</h3>
            <p style={{ ...styles.hint, marginBottom: '1rem' }}>{error}</p>
            <button type="button" onClick={load} style={styles.button}>Try again</button>
          </div>
        </div>
      )
    }

    return (
      <div style={styles.section}>
        {header}
        {primary}

        <div style={styles.metricStrip} className="metric-strip">
          <Metric label="Total scans" value={stats.totalScans || 0} />
          <Metric label="High findings" value={stats.high || 0} />
          {isAdmin && <Metric label="Clients" value={clients.length} />}
          {isAnalyst && <Metric label="Awaiting review" value={reviewCount} />}
          {isClient && <Metric label="Code issues" value={codeIssues} />}
          <Metric label="Monitors" value={monitors.length} />
        </div>

        {rolePanel}

        <div style={styles.split}>
          <div style={styles.panelDark}>
            <div style={styles.panelHeader}>
              <h3 style={styles.panelTitle}>Recent Scans</h3>
              {canManage && (
                <button type="button" onClick={() => setView('scans')} style={styles.darkActionBtn}>Start a scan</button>
              )}
            </div>
            <div style={{ padding: '0 1.25rem 1.25rem' }}>
              {scans.slice(0, 6).map((s: any) => (
                <div key={s.id} style={styles.auditRow}>
                  <div>
                    <strong style={{ color: 'var(--c-text)' }}>{s.client?.name || '-'}</strong>
                    <span style={styles.listRowSub}> · {s.scan_type}</span>
                  </div>
                  <Badge tone={s.status === 'completed' ? 'success' : 'warning'}>{s.status}</Badge>
                </div>
              ))}
              {scans.length === 0 && (
                <div style={styles.emptyState}>
                  No scans yet — a scan maps your attack surface and files findings for review.
                  {canManage && (
                    <div style={{ marginTop: '0.75rem' }}>
                      <button type="button" onClick={() => setView('scans')} style={styles.darkActionBtn}>Start the first scan</button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div style={styles.panelDark}>
            <div style={styles.panelHeader}>
              <h3 style={styles.panelTitle}>Open Alerts</h3>
              <button type="button" onClick={() => setView('alerts')} style={styles.darkActionBtn}>Review all</button>
            </div>
            <div style={{ padding: '0 1.25rem 1.25rem' }}>
              {openAlerts.slice(0, 6).map((a: any) => (
                <div key={a.id} style={styles.auditRow}>
                  <div>
                    <strong style={{ color: 'var(--c-text)' }}>{a.title}</strong>
                    <span style={styles.listRowSub}> · {a.severity}</span>
                  </div>
                  <Badge tone={severityTone(a.severity)}>{a.status}</Badge>
                </div>
              ))}
              {openAlerts.length === 0 && (
                <div style={styles.emptyState}>No open alerts. Monitoring is running in the background.</div>
              )}
            </div>
          </div>
        </div>

        {canManage && (
          <div style={{ ...styles.panelDark, marginTop: '1rem' }}>
            <div style={styles.panelHeader}>
              <h3 style={styles.panelTitle}>Recent Audit Activity</h3>
              <button type="button" onClick={() => setView('audit')} style={styles.darkActionBtn}>View log</button>
            </div>
            <div style={{ padding: '0 1.25rem 1.25rem' }}>
              {audit.map((a: any) => (
                <div key={a.id} style={styles.auditRow}>
                  <div>
                    <strong style={{ color: 'var(--c-text)' }}>{a.action}</strong>
                    <span style={styles.listRowSub}> · {a.resource_type} #{a.resource_id}</span>
                  </div>
                  <span style={styles.listRowSub}>{new Date(a.created_at).toLocaleString()}</span>
                </div>
              ))}
              {audit.length === 0 && <div style={styles.emptyState}>No activity recorded yet.</div>}
            </div>
          </div>
        )}
      </div>
    )
  }

// ============================================================
// CLIENT DASHBOARD — a genuinely distinct portal, not the operator
// dashboard with buttons hidden. A client reads results (findings, alerts,
// compliance posture); it never sees the operator stat grid, "Recent
// Scans"/"Review findings"/"Open admin" affordances, since those are
// tooling a client never configures. Same already-scoped API calls as the
// operator Dashboard, reshaped presentation only.
// ============================================================
function ClientDashboard({ ctx }: { ctx: any }) {
  const { api, token, clients, setClients, scans, setScans, alerts, setAlerts, setView, user } = ctx
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [compliance, setCompliance] = useState<any>(null)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [scansData, clientsData, alertsData] = await Promise.all([
        api('/scans'),
        api('/clients'),
        api('/alerts'),
      ])
      setScans(Array.isArray(scansData) ? scansData : [])
      setClients(Array.isArray(clientsData) ? clientsData : [])
      setAlerts(Array.isArray(alertsData) ? alertsData : [])
    } catch (e: any) {
      setError(e.message || 'Could not load your dashboard')
    } finally {
      setLoading(false)
    }
  }

  // Re-run on a persona switch, not just a token change -- same reasoning
  // as the operator Dashboard.
  useEffect(() => { load() }, [token, user?.role])

  const org = clients[0]
  const isClub = org?.sector === 'sports'
  const workspaceLabel = isClub ? 'Club portal' : 'Client portal'
  const dashboardTitle = isClub ? 'Club security posture' : 'Your security posture'

  const findings = scans.flatMap((s: any) => s.findings || [])
  const openFindings = findings.filter((f: any) => f.status !== 'fixed' && f.status !== 'false_positive')
  const severityCounts = {
    critical: openFindings.filter((f: any) => f.severity === 'critical').length,
    high: openFindings.filter((f: any) => f.severity === 'high').length,
    medium: openFindings.filter((f: any) => f.severity === 'medium').length,
    low: openFindings.filter((f: any) => f.severity === 'low').length,
  }
  const openAlerts = alerts.filter((a: any) => a.status === 'open')
  const hasCritical = severityCounts.critical > 0
  const lastChecked = scans.length
    ? new Date(
        Math.max(...scans.map((s: any) => new Date(s.completed_at || s.created_at || s.started_at || 0).getTime()))
      ).toLocaleDateString()
    : null

  // A lightweight read of the same compliance/summary endpoint the operator
  // Compliance page uses, scoped to this org's own findings and sector --
  // just enough to show the sector pack name and whether reporting is
  // required, without sending the client into the operator's mapping tool.
  useEffect(() => {
    if (!org || loading) return
    const params = new URLSearchParams({
      total_findings: String(openFindings.length),
      critical: String(severityCounts.critical),
      high: String(severityCounts.high),
      medium: String(severityCounts.medium),
      client_sector: org.sector || 'other',
    })
    api(`/compliance/summary?${params.toString()}`).then(setCompliance).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [org?.id, loading, openFindings.length, severityCounts.critical, severityCounts.high, severityCounts.medium])

  const header = (
    <div style={styles.dashHead}>
      <div style={{ minWidth: 0 }}>
        <div style={styles.roleEyebrow}>
          <span style={styles.roleDot} aria-hidden="true" />
          {workspaceLabel}
        </div>
        <h1 style={styles.dashTitle}>{dashboardTitle}</h1>
      </div>
    </div>
  )

  if (loading) {
    return (
      <div style={styles.section}>
        {header}
        <div style={styles.skeleton} role="status" aria-live="polite">
          <span className="sr-only">Loading your dashboard</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.section}>
        {header}
        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Could not load your dashboard</h3>
          <p style={{ ...styles.hint, marginBottom: '1rem' }}>{error}</p>
          <button type="button" onClick={load} style={styles.button}>Try again</button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.section}>
      {header}

      {/* The headline of the page: one plain-language posture statement,
          not a stat grid. */}
      <div style={{ ...styles.postureBanner, ...(hasCritical ? styles.postureBannerWarning : styles.postureBannerSuccess) }}>
        <div style={styles.postureHeadline}>
          {hasCritical
            ? `${severityCounts.critical} critical finding${severityCounts.critical === 1 ? '' : 's'} need${severityCounts.critical === 1 ? 's' : ''} your attention`
            : `No critical issues${lastChecked ? ` — last checked ${lastChecked}` : ''}`}
        </div>
        <p style={styles.postureSub}>
          {org?.name || 'Your organization'} · {sectorLabel(org?.sector || 'other')}. This workspace only ever shows
          your own scans, findings and alerts.
        </p>
      </div>

      <div style={styles.narrativeGrid}>
        <div style={styles.narrativeCard}>
          <h3 style={styles.panelTitle}>Findings</h3>
          <div style={styles.narrativeValue}>{openFindings.length}</div>
          <div style={styles.hint}>open finding{openFindings.length === 1 ? '' : 's'}</div>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', margin: '0.85rem 0' }}>
            {severityCounts.critical > 0 && <Badge tone="danger">{severityCounts.critical} critical</Badge>}
            {severityCounts.high > 0 && <Badge tone="warning">{severityCounts.high} high</Badge>}
            {severityCounts.medium > 0 && <Badge tone="accent">{severityCounts.medium} medium</Badge>}
            {severityCounts.low > 0 && <Badge tone="neutral">{severityCounts.low} low</Badge>}
            {openFindings.length === 0 && <Badge tone="success">All clear</Badge>}
          </div>
          <button type="button" onClick={() => setView('findings')} style={styles.darkActionBtn}>View findings</button>
        </div>

        <div style={styles.narrativeCard}>
          <h3 style={styles.panelTitle}>Alerts</h3>
          <div style={styles.narrativeValue}>{openAlerts.length}</div>
          <div style={styles.hint}>open alert{openAlerts.length === 1 ? '' : 's'}</div>
          <div style={{ margin: '0.85rem 0' }}>
            <Badge tone={openAlerts.length > 0 ? 'warning' : 'success'}>
              {openAlerts.length > 0 ? 'Needs triage' : 'All clear'}
            </Badge>
          </div>
          <button type="button" onClick={() => setView('alerts')} style={styles.darkActionBtn}>View alerts</button>
        </div>

        <div style={styles.narrativeCard}>
          <h3 style={styles.panelTitle}>Compliance</h3>
          <div style={styles.narrativeValue}>{compliance?.sector_pack?.label || sectorLabel(org?.sector || 'other')}</div>
          <div style={styles.hint}>
            {compliance
              ? compliance.reporting_required
                ? 'Incident reporting required for your sector'
                : 'No mandatory incident reporting flagged'
              : 'Loading your obligations…'}
          </div>
          <div style={{ marginTop: '0.85rem' }}>
            <button type="button" onClick={() => setView('compliance')} style={styles.darkActionBtn}>View compliance</button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================
// CLIENTS
// ============================================================
function ClientsSection({ ctx }: { ctx: any }) {
  const { api, token, notify, clients, setClients, canManage, isAdmin } = ctx
    const emptyClientForm = { name: '', legal_name: '', contact_email: '', contact_phone: '', sector: '' }
    const [newClient, setNewClient] = useState(emptyClientForm)
    const [showAdd, setShowAdd] = useState(false)
    const [editClient, setEditClient] = useState<any>(null)
    const [editForm, setEditForm] = useState(emptyClientForm)
    const [pendingDeleteClient, setPendingDeleteClient] = useState<any>(null)
    const [selectedId, setSelectedId] = useState<any>(null)
    const [scopes, setScopes] = useState<any[]>([])
    const [newScope, setNewScope] = useState({ target: '', target_type: 'domain' })
    const [pendingDeleteScope, setPendingDeleteScope] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [savingEdit, setSavingEdit] = useState(false)

    const loadClients = async () => {
      try {
        const data = await api('/clients')
        setClients(Array.isArray(data) ? data : [])
      } catch (e: any) {
        notify(e.message || 'Could not load clients', 'error')
      }
    }

    useEffect(() => {
      loadClients().finally(() => setLoading(false))
    }, [token])

    // A client portal only ever has one organization, and an operator should
    // not stare at an empty detail pane on first load. Select the first row
    // once the list arrives (the scopes request below then fills the detail).
    useEffect(() => {
      if (selectedId == null && clients.length > 0) setSelectedId(clients[0].id)
    }, [clients, selectedId])

    const loadScopes = async (clientId: any) => {
      try {
        const data = await api(`/clients/${clientId}/scopes`)
        setScopes(Array.isArray(data) ? data : [])
      } catch (e: any) {
        notify(e.message || 'Could not load scopes', 'error')
      }
    }

    useEffect(() => {
      if (selectedId) loadScopes(selectedId)
    }, [selectedId])

    const createClient = async (e: any) => {
      e.preventDefault()
      setSubmitting(true)
      try {
        await api('/clients', { method: 'POST', body: JSON.stringify(newClient) })
        setNewClient(emptyClientForm)
        setShowAdd(false)
        await loadClients()
        notify('Client created', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not create the client', 'error')
      } finally {
        setSubmitting(false)
      }
    }

    const openEdit = (c: any) => {
      setEditForm({
        name: c.name || '',
        legal_name: c.legal_name || '',
        contact_email: c.contact_email || '',
        contact_phone: c.contact_phone || '',
        sector: c.sector || '',
      })
      setEditClient(c)
    }

    const saveEdit = async (e: any) => {
      e.preventDefault()
      if (!editClient) return
      setSavingEdit(true)
      try {
        await api(`/clients/${editClient.id}`, { method: 'PATCH', body: JSON.stringify(editForm) })
        setEditClient(null)
        await loadClients()
        notify('Client updated', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not update the client', 'error')
      } finally {
        setSavingEdit(false)
      }
    }

    const toggleClientActive = async (c: any) => {
      try {
        await api(`/clients/${c.id}`, { method: 'PATCH', body: JSON.stringify({ is_active: !c.is_active }) })
        await loadClients()
        notify(c.is_active ? 'Client deactivated' : 'Client reactivated', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not update the client', 'error')
      }
    }

    const confirmDeleteClient = async () => {
      const c = pendingDeleteClient
      setPendingDeleteClient(null)
      if (!c) return
      try {
        await api(`/clients/${c.id}`, { method: 'DELETE' })
        if (selectedId === c.id) setSelectedId(null)
        await loadClients()
        notify('Client and all of its scans, findings, and monitors were deleted', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not delete the client', 'error')
      }
    }

    const addScope = async (e: any) => {
      e.preventDefault()
      try {
        await api(`/clients/${selectedId}/scopes`, { method: 'POST', body: JSON.stringify(newScope) })
        setNewScope({ target: '', target_type: 'domain' })
        await loadScopes(selectedId)
        notify('Scope added', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not add the scope', 'error')
      }
    }

    const toggleScopeExcluded = async (s: any) => {
      try {
        await api(`/clients/${selectedId}/scopes/${s.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ is_excluded: !s.is_excluded }),
        })
        await loadScopes(selectedId)
        notify(s.is_excluded ? 'Scope included in future scans' : 'Scope excluded from future scans', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not update the scope', 'error')
      }
    }

    const confirmDeleteScope = async () => {
      const s = pendingDeleteScope
      setPendingDeleteScope(null)
      if (!s) return
      try {
        await api(`/clients/${selectedId}/scopes/${s.id}`, { method: 'DELETE' })
        await loadScopes(selectedId)
        notify('Scope removed', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not remove the scope', 'error')
      }
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>{canManage ? 'Clients' : 'Organization'}</h1>
        <p style={styles.hint}>
          {canManage
            ? 'Onboard clients, then register the domains, IPs, and URLs they have authorised you to assess.'
            : 'Your organization profile and the domains, IPs, and URLs authorized for assessment.'}
        </p>

        {showAdd && (
          <Modal title="Add client" onClose={() => setShowAdd(false)}>
            <form onSubmit={createClient}>
              <Field label="Client name" htmlFor="client-name" tone="dark" required>
                <TextInput
                  value={newClient.name}
                  onChange={(e) => setNewClient({ ...newClient, name: e.target.value })}
                  autoFocus
                  required
                  placeholder="e.g. Sahel Bank"
                />
              </Field>
              <Field label="Legal name" htmlFor="client-legal-name" tone="dark" hint="Used on contracts and reports">
                <TextInput
                  value={newClient.legal_name}
                  onChange={(e) => setNewClient({ ...newClient, legal_name: e.target.value })}
                />
              </Field>
              <Field label="Contact email" htmlFor="client-email" tone="dark">
                <TextInput
                  type="email"
                  value={newClient.contact_email}
                  onChange={(e) => setNewClient({ ...newClient, contact_email: e.target.value })}
                />
              </Field>
              <Field label="Contact phone" htmlFor="client-phone" tone="dark">
                <TextInput
                  type="tel"
                  value={newClient.contact_phone}
                  onChange={(e) => setNewClient({ ...newClient, contact_phone: e.target.value })}
                />
              </Field>
              <Field label="Sector" htmlFor="client-sector" tone="dark" hint="Drives which compliance obligations apply to this client">
                <Select value={newClient.sector} onChange={(e) => setNewClient({ ...newClient, sector: e.target.value })} tone="dark">
                  <option value="">Unspecified</option>
                  <option value="banking">Banking / Mobile Money</option>
                  <option value="telecom">Telecom</option>
                  <option value="government">Government</option>
                  <option value="sports">Sports (club / federation / academy)</option>
                  <option value="other">Other</option>
                </Select>
              </Field>
              <Button type="submit" loading={submitting} disabled={!newClient.name.trim()}>
                Add client
              </Button>
            </form>
          </Modal>
        )}

        {editClient && (
          <Modal title={`Edit ${editClient.name}`} onClose={() => setEditClient(null)}>
            <form onSubmit={saveEdit}>
              <Field label="Client name" htmlFor="edit-client-name" tone="dark" required>
                <TextInput
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  autoFocus
                  required
                />
              </Field>
              <Field label="Legal name" htmlFor="edit-client-legal-name" tone="dark">
                <TextInput
                  value={editForm.legal_name}
                  onChange={(e) => setEditForm({ ...editForm, legal_name: e.target.value })}
                />
              </Field>
              <Field label="Contact email" htmlFor="edit-client-email" tone="dark">
                <TextInput
                  type="email"
                  value={editForm.contact_email}
                  onChange={(e) => setEditForm({ ...editForm, contact_email: e.target.value })}
                />
              </Field>
              <Field label="Contact phone" htmlFor="edit-client-phone" tone="dark">
                <TextInput
                  type="tel"
                  value={editForm.contact_phone}
                  onChange={(e) => setEditForm({ ...editForm, contact_phone: e.target.value })}
                />
              </Field>
              <Field label="Sector" htmlFor="edit-client-sector" tone="dark" hint="Drives which compliance obligations apply to this client">
                <Select value={editForm.sector} onChange={(e) => setEditForm({ ...editForm, sector: e.target.value })} tone="dark">
                  <option value="">Unspecified</option>
                  <option value="banking">Banking / Mobile Money</option>
                  <option value="telecom">Telecom</option>
                  <option value="government">Government</option>
                  <option value="sports">Sports (club / federation / academy)</option>
                  <option value="other">Other</option>
                </Select>
              </Field>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <Button type="submit" loading={savingEdit} disabled={!editForm.name.trim()}>Save changes</Button>
                <Button type="button" variant="secondaryDark" onClick={() => setEditClient(null)} disabled={savingEdit}>Cancel</Button>
              </div>
            </form>
          </Modal>
        )}

        <SplitPanel
          title={canManage ? 'All Clients' : 'Your organization'}
          loading={loading}
          action={canManage ? (
            <button type="button" onClick={() => setShowAdd(true)} style={styles.darkActionBtn}>+ Add client</button>
          ) : undefined}
          items={clients}
          selectedId={selectedId}
          onSelect={(c) => setSelectedId(c.id)}
          emptyLabel={canManage ? 'No clients yet.' : 'No organization found.'}
          emptyHint={canManage ? 'Add a client to start registering scan scopes.' : 'Contact your Ultorn administrator if this looks wrong.'}
          renderRow={(c) => (
            <>
              <div style={styles.listRowMain}>
                <div className="list-row-title" style={styles.listRowTitle}>{c.name}</div>
                <div style={styles.listRowSub}>{c.contact_email || 'No contact email'}</div>
              </div>
              <Badge tone={c.is_active ? 'success' : 'neutral'}>{c.is_active ? 'Active' : 'Inactive'}</Badge>
            </>
          )}
          renderDetail={(c) => (
            <>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem' }}>
                <div>
                  <div style={styles.detailHeading}>{c.name}</div>
                  {c.legal_name && <div style={styles.listRowSub}>{c.legal_name}</div>}
                </div>
                <Badge tone={c.is_active ? 'success' : 'neutral'}>{c.is_active ? 'Active' : 'Inactive'}</Badge>
              </div>
              <div style={styles.detailSub}>
                {c.contact_email || 'No contact email'} · {c.contact_phone || 'No contact phone'}
                {c.sector && <Badge tone="accent">{sectorLabel(c.sector)}</Badge>}
              </div>

              {canManage && (
                <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button type="button" onClick={() => openEdit(c)} style={styles.darkActionBtn}>Edit</button>
                  <button type="button" onClick={() => toggleClientActive(c)} style={styles.darkActionBtn}>
                    {c.is_active ? 'Deactivate' : 'Reactivate'}
                  </button>
                  {isAdmin && (
                    <button type="button" onClick={() => setPendingDeleteClient(c)} style={{ ...styles.darkActionBtn, background: 'var(--c-danger-soft)', color: 'var(--c-danger)' }}>
                      Delete
                    </button>
                  )}
                </div>
              )}

              <div style={{ marginTop: '1.25rem' }}>
                <div style={styles.detailLabel}>Scan scopes</div>
                {scopes.length === 0 && <div style={styles.listRowSub}>No scopes added.</div>}
                {scopes.map((s: any) => (
                  <div key={s.id} style={{ ...styles.scopeRow, alignItems: 'center' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {s.target}
                      <Badge tone="neutral">{s.target_type}</Badge>
                      {s.is_excluded && <Badge tone="warning">Excluded</Badge>}
                      <Badge tone={s.verified ? 'success' : 'neutral'}>{s.verified ? 'Verified' : 'Unverified'}</Badge>
                    </span>
                    {canManage && (
                      <span style={{ display: 'flex', gap: '0.4rem', flexShrink: 0 }}>
                        <button type="button" onClick={() => toggleScopeExcluded(s)} style={styles.buttonSmall}>
                          {s.is_excluded ? 'Include' : 'Exclude'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setPendingDeleteScope(s)}
                          style={{ ...styles.buttonSmall, background: 'var(--c-danger-soft)', color: 'var(--c-danger)', borderColor: 'var(--c-danger-border)' }}
                        >
                          Remove
                        </button>
                      </span>
                    )}
                  </div>
                ))}
                {canManage && (
                  <form onSubmit={addScope} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                    <input
                      aria-label="Scope target (domain, IP, or URL)"
                      placeholder="domain, IP, or URL"
                      value={newScope.target}
                      onChange={(e) => setNewScope({ ...newScope, target: e.target.value })}
                      style={{ ...styles.input, flex: '1 1 200px', background: 'var(--c-field-strong)', color: 'var(--c-text)', border: '1px solid var(--c-border-strong)' }}
                    />
                    <select
                      aria-label="Scope type"
                      value={newScope.target_type}
                      onChange={(e) => setNewScope({ ...newScope, target_type: e.target.value })}
                      style={{ ...styles.inputSmall, background: 'var(--c-field-strong)', color: 'var(--c-text)', border: '1px solid var(--c-border-strong)' }}
                    >
                      <option value="domain">Domain</option>
                      <option value="ip">IP</option>
                      <option value="url">URL</option>
                    </select>
                    <button type="submit" disabled={!newScope.target.trim()} style={{ ...styles.darkActionBtn, opacity: newScope.target.trim() ? 1 : 0.5 }}>Add</button>
                  </form>
                )}
              </div>
            </>
          )}
        />

        <ConfirmDialog
          open={Boolean(pendingDeleteClient)}
          title="Delete this client?"
          description={
            pendingDeleteClient
              ? `${pendingDeleteClient.name} and every scan, finding, monitor, alert, schedule, and code scan tied to it will be permanently deleted. This cannot be undone.`
              : ''
          }
          confirmLabel="Delete client"
          onConfirm={confirmDeleteClient}
          onCancel={() => setPendingDeleteClient(null)}
        />

        <ConfirmDialog
          open={Boolean(pendingDeleteScope)}
          title="Remove this scope?"
          description={
            pendingDeleteScope
              ? `${pendingDeleteScope.target} will no longer be in scope for future scans. Past findings against it are kept.`
              : ''
          }
          confirmLabel="Remove scope"
          onConfirm={confirmDeleteScope}
          onCancel={() => setPendingDeleteScope(null)}
        />
      </div>
    )
  }

// ============================================================
// SCANS
// ============================================================
function ScansSection({ ctx }: { ctx: any }) {
  const { api, token, notify, clients, setClients, scans, setScans, canManage } = ctx
    const [newScan, setNewScan] = useState({ client_id: '', scan_type: 'vulnerability' })
    const [showStart, setShowStart] = useState(false)
    const [selectedId, setSelectedId] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)

    useEffect(() => {
      Promise.all([api('/scans'), api('/clients')])
        .then(([scansData, clientsData]) => {
          setScans(Array.isArray(scansData) ? scansData : [])
          setClients(Array.isArray(clientsData) ? clientsData : [])
        })
        .catch((e: any) => notify(e.message || 'Could not load scans', 'error'))
        .finally(() => setLoading(false))
    }, [token])

    useEffect(() => {
      if (selectedId != null || scans.length === 0) return
      const first = scans.find((s: any) => s.status === 'completed') || scans[0]
      setSelectedId(first.id)
    }, [scans, selectedId])

    const startScan = async (e: any) => {
      e.preventDefault()
      setSubmitting(true)
      try {
        await api('/scans', { method: 'POST', body: JSON.stringify({ client_id: parseInt(newScan.client_id), scan_type: newScan.scan_type }) })
        setShowStart(false)
        setNewScan({ client_id: '', scan_type: 'vulnerability' })
        const data = await api('/scans')
        setScans(Array.isArray(data) ? data : [])
        notify('Scan started. It runs on all scopes with no verification gate.', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not start the scan', 'error')
      } finally {
        setSubmitting(false)
      }
    }

    const runScan = async (id: number) => {
      try {
        const res = await api(`/scans/${id}/run`, { method: 'POST' })
        notify(res.status || 'Scan completed', 'success')
        const data = await api('/scans')
        setScans(Array.isArray(data) ? data : [])
      } catch (e: any) {
        notify(e.message || 'Could not run the scan', 'error')
      }
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Security Assessments</h1>
        <p style={styles.hint}>
          {canManage
            ? 'No verification gate. Scans run on all in-scope targets immediately. Full data extraction: banners, headers, page content, body.'
            : 'Assessments run against the domains, IPs, and URLs your organization has authorized. Findings are filed for analyst review.'}
        </p>

        {showStart && (
          <Modal title="Start scan" onClose={() => setShowStart(false)}>
            <form onSubmit={startScan}>
              <Field label="Client" htmlFor="scan-client" tone="dark" required>
                <Select value={newScan.client_id} onChange={(e) => setNewScan({ ...newScan, client_id: e.target.value })}>
                  <option value="">Select a client</option>
                  {clients.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </Select>
              </Field>
              <Field label="Assessment type" htmlFor="scan-type" tone="dark">
                <Select value={newScan.scan_type} onChange={(e) => setNewScan({ ...newScan, scan_type: e.target.value })}>
                  <option value="vulnerability">Vulnerability assessment</option>
                  <option value="web">Web application</option>
                  <option value="full">Full assessment</option>
                </Select>
              </Field>
              <Button type="submit" loading={submitting} disabled={!newScan.client_id}>Start scan</Button>
            </form>
          </Modal>
        )}

        <SplitPanel
          title="Scans"
          loading={loading}
          action={canManage ? (
            <button type="button" onClick={() => setShowStart(true)} style={styles.darkActionBtn}>+ Start scan</button>
          ) : undefined}
          items={scans}
          selectedId={selectedId}
          onSelect={(s) => setSelectedId(s.id)}
          emptyLabel="No scans yet."
          emptyHint="Start a scan to map the client's attack surface."
          renderRow={(s) => (
            <>
              <div style={styles.listRowMain}>
                <div className="list-row-title" style={styles.listRowTitle}>{s.client?.name || '-'}</div>
                <div style={styles.listRowSub}>{s.scan_type}</div>
              </div>
              <Badge tone={s.status === 'completed' ? 'success' : 'warning'}>{s.status}</Badge>
            </>
          )}
          renderDetail={(s) => (
            <>
              <div style={styles.detailHeading}>{s.client?.name || '-'}</div>
              <div style={styles.detailSub}>{s.scan_type} · <Badge tone={s.status === 'completed' ? 'success' : 'warning'}>{s.status}</Badge></div>
              <div style={styles.subCardGrid}>
                <div style={styles.subCard}><div style={styles.subCardLabel}>Findings</div><div style={styles.subCardValue}>{s.summary?.total_findings || 0}</div></div>
                <div style={styles.subCard}><div style={styles.subCardLabel}>Critical</div><div style={styles.subCardValue}>{s.summary?.critical || 0}</div></div>
                <div style={styles.subCard}><div style={styles.subCardLabel}>High</div><div style={styles.subCardValue}>{s.summary?.high || 0}</div></div>
              </div>
              {canManage && s.status !== 'running' && (
                <button type="button" onClick={() => runScan(s.id)} style={{ ...styles.darkActionBtn, marginTop: '1.25rem' }}>Run scan</button>
              )}
            </>
          )}
        />
      </div>
    )
  }

// ============================================================
// FINDINGS
// ============================================================
function FindingsSection({ ctx }: { ctx: any }) {
  const { api, token, notify, findings, setFindings, canManage } = ctx
    const [selectedId, setSelectedId] = useState<any>(null)
    const [reviewStatus, setReviewStatus] = useState('fixed')

    useEffect(() => {
      api('/scans').then((data: any) => {
        setFindings(data.flatMap((s: any) => s.findings || []))
      })
    }, [token])

    useEffect(() => {
      if (selectedId == null && findings.length > 0) setSelectedId(findings[0].id)
    }, [findings, selectedId])

    const reviewFinding = async (id: number) => {
      try {
        await api(`/findings/${id}/review`, { method: 'POST', body: JSON.stringify({ status: reviewStatus }) })
        notify('Finding reviewed: human analyst attested', 'success')
        const data = await api('/scans')
        setFindings(data.flatMap((s: any) => s.findings || []))
      } catch (e: any) {
        notify(e.message || 'Could not save the review', 'error')
      }
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Findings & Remediation</h1>
        <p style={styles.hint}>
          Critical and high findings require named human analyst review before remediation. No autonomous exploitation.
        </p>

        <SplitPanel
          title="Findings"
          items={findings}
          selectedId={selectedId}
          onSelect={(f) => { setSelectedId(f.id); setReviewStatus('fixed') }}
          emptyLabel="No findings yet."
          renderRow={(f) => (
            <>
              <div style={styles.listRowMain}>
                <div className="list-row-title" style={styles.listRowTitle}>{f.title}</div>
                <div style={styles.listRowSub}>{f.target}</div>
              </div>
              <Badge tone={severityTone(f.severity)}>{f.severity}</Badge>
            </>
          )}
          renderDetail={(f) => {
            let evidence: any = {}
            try {
              evidence = f.evidence ? JSON.parse(f.evidence) : {}
            } catch {
              evidence = { raw: f.evidence }
            }
            const needsReview = f.severity === 'critical' || f.severity === 'high'
            return (
              <>
                <div style={styles.detailHeading}>{f.title}</div>
                <div style={styles.detailSub}>
                  <Badge tone={severityTone(f.severity)}>{f.severity}</Badge> · {f.target} · status {f.status}
                </div>
                <div style={styles.detailLabel}>Evidence</div>
                <div style={styles.codeBlock}>{JSON.stringify(evidence, null, 2).slice(0, 600)}</div>
                <div style={styles.detailLabel}>Reviewed by</div>
                <div style={styles.listRowSub}>{f.reviewed_by_user?.email || 'Not yet reviewed'}</div>

                {needsReview && canManage && (
                  <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.5rem' }}>
                    <select
                      aria-label="New status for this finding"
                      value={reviewStatus}
                      onChange={(e) => setReviewStatus(e.target.value)}
                      style={{ ...styles.input, background: 'var(--c-field-strong)', color: 'var(--c-text)', border: '1px solid var(--c-border-strong)' }}
                    >
                      <option value="open">Open</option>
                      <option value="fixed">Fixed</option>
                      <option value="false_positive">False Positive</option>
                      <option value="acknowledged">Acknowledged</option>
                    </select>
                    <button onClick={() => reviewFinding(f.id)} style={styles.darkActionBtn}>Attest Review</button>
                  </div>
                )}
              </>
            )
          }}
        />
      </div>
    )
  }

// ============================================================
// AI / SOVEREIGNTY
// ============================================================
function AISection({ ctx }: { ctx: any }) {
  const { api, token, notify, clients } = ctx
    const [prompt, setPrompt] = useState('')
    const [clientName, setClientName] = useState('')
    const [response, setResponse] = useState('')
    const [aiMeta, setAiMeta] = useState<any>(null)
    const [sanitized, setSanitized] = useState('')
    const [forceLocal, setForceLocal] = useState(false)
    const [busy, setBusy] = useState(false)

    // If the prompt names a client in this workspace, use that name for
    // redaction automatically. The field stays editable for ad-hoc prompts.
    useEffect(() => {
      if (clientName.trim() || !prompt.trim()) return
      const match = (clients || []).find(
        (c: any) => c.name && prompt.toLowerCase().includes(c.name.toLowerCase())
      )
      if (match) setClientName(match.name)
    }, [prompt, clients, clientName])

    const queryAI = async () => {
      if (!prompt.trim()) return
      setBusy(true)
      try {
        const res = await api('/ai/query', {
          method: 'POST',
          body: JSON.stringify({ prompt, client_name: clientName || undefined, force_local: forceLocal }),
        })
        setResponse(res.response || 'No response')
        setAiMeta({ provider: res.provider, model: res.model, sanitized: res.prompt_sanitized, id: res.query_id })
      } catch (e: any) {
        notify(e.message || 'The AI query failed', 'error')
      } finally {
        setBusy(false)
      }
    }

    const doSanitize = async () => {
      if (!prompt.trim()) return
      try {
        const data = await api('/sanitize', {
          method: 'POST',
          body: JSON.stringify({ text: prompt, client_name: clientName || undefined }),
        })
        setSanitized(data.sanitized || '')
      } catch (e: any) {
        notify(e.message || 'Could not preview the sanitization', 'error')
      }
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>AI Guard: Sovereignty Layer</h1>
        <p style={styles.hint}>
          Prompts are sanitized before reaching any external model: IPs, credentials, and PII are stripped,
          and known client names are redacted automatically. Sensitive data stays local. Every query is immutably logged.
        </p>

        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Send to AI</h3>
          <Field
            label="Prompt"
            htmlFor="ai-prompt"
            hint="Client names, IPs, credentials, and PII are stripped before any model sees it."
          >
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. 'Review Acme Corp at 10.0.0.5 with API key sk-live-9f8a7b6c'"
              rows={4}
              style={{ minHeight: 'unset' }}
            />
          </Field>
          <div style={styles.formRow}>
            <div style={{ flex: '1 1 260px' }}>
              <Field label="Client name (optional)" htmlFor="ai-client" hint="Redacted from the prompt before it leaves the platform.">
                <TextInput value={clientName} onChange={(e) => setClientName(e.target.value)} />
              </Field>
            </div>
            <label style={styles.checkboxLabel}>
              <input type="checkbox" checked={forceLocal} onChange={(e) => setForceLocal(e.target.checked)} />
              Force local processing (no external model)
            </label>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem', flexWrap: 'wrap' }}>
            <Button onClick={queryAI} loading={busy} disabled={!prompt.trim()}>Query AI</Button>
            <Button variant="secondary" onClick={doSanitize} disabled={!prompt.trim()}>Preview sanitization</Button>
          </div>
        </div>

        {response && (
          <div style={styles.lightCard}>
            <h3 style={styles.h3}>AI Response</h3>
            {aiMeta && (
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
                <Badge tone={aiMeta.provider === 'local' ? 'success' : 'warning'}>
                  {aiMeta.provider === 'local' ? 'Stayed on-premises' : `Sent to ${aiMeta.provider}`}
                </Badge>
                <Badge tone="neutral">{aiMeta.model}</Badge>
                <Badge tone={aiMeta.sanitized ? 'success' : 'neutral'}>
                  {aiMeta.sanitized ? 'Prompt sanitized' : 'No sensitive data'}
                </Badge>
                <Badge tone="neutral">Query #{aiMeta.id}</Badge>
              </div>
            )}
            <div style={styles.codeBlock}>{response}</div>
          </div>
        )}

        {sanitized && (
          <div style={styles.lightCard}>
            <h3 style={styles.h3}>Sanitized Prompt (what the model sees)</h3>
            <div style={styles.codeBlock}>{sanitized}</div>
          </div>
        )}
      </div>
    )
  }

// ============================================================
// AUDIT LOG
// ============================================================
function AuditSection({ ctx }: { ctx: any }) {
  const { api, token, audit, setAudit } = ctx
    const [selectedId, setSelectedId] = useState<any>(null)

    useEffect(() => {
      api('/audit').then((data: any) => setAudit(data))
    }, [token])

    useEffect(() => {
      if (selectedId == null && audit.length > 0) setSelectedId(audit[0].id)
    }, [audit, selectedId])

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Immutable Audit Log</h1>
        <p style={styles.hint}>
          Every action, scan, AI query, and review is logged. This log is the authoritative record for regulatory and client accountability.
        </p>

        <SplitPanel
          title="Audit Trail"
          items={audit}
          selectedId={selectedId}
          onSelect={(a) => setSelectedId(a.id)}
          emptyLabel="No audit entries yet."
          renderRow={(a) => (
            <>
              <div style={styles.listRowMain}>
                <div className="list-row-title" style={styles.listRowTitle}>{a.action}</div>
                <div style={styles.listRowSub}>{a.user_email || 'system'}</div>
              </div>
              <span style={styles.listRowSub}>{new Date(a.created_at).toLocaleDateString()}</span>
            </>
          )}
          renderDetail={(a) => (
            <>
              <div style={styles.detailHeading}>{a.action}</div>
              <div style={styles.detailSub}>
                {a.user_email || 'system'} · {a.resource_type || '-'} #{a.resource_id || '-'} · {new Date(a.created_at).toLocaleString()}
              </div>
              <div style={styles.detailLabel}>Details</div>
              <div style={styles.codeBlock}>{a.details || '-'}</div>
            </>
          )}
        />
      </div>
    )
  }

// ============================================================
// ADMIN: users & API keys
// ============================================================
function AdminSection({ ctx }: { ctx: any }) {
  const { api, token, notify } = ctx
    const [users, setUsers] = useState<any[]>([])
    const [apiKeys, setApiKeys] = useState<any[]>([])
    const [newKeyName, setNewKeyName] = useState('')
    const [mintedKey, setMintedKey] = useState<string | null>(null)
    const [showCreate, setShowCreate] = useState(false)
    const [selectedUserId, setSelectedUserId] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [creatingKey, setCreatingKey] = useState(false)
    const [pendingRevoke, setPendingRevoke] = useState<any>(null)
    const [resetUser, setResetUser] = useState<any>(null)
    const [temporaryPassword, setTemporaryPassword] = useState<string | null>(null)
    const [resettingPassword, setResettingPassword] = useState(false)
    const [resetError, setResetError] = useState('')
    const [showCreateUser, setShowCreateUser] = useState(false)
    const [newUser, setNewUser] = useState({ email: '', password: '', full_name: '', role: 'analyst' })
    const [creatingUser, setCreatingUser] = useState(false)
    const [createUserError, setCreateUserError] = useState('')

    const loadUsers = async () => {
      const data = await api('/admin/users')
      setUsers(Array.isArray(data) ? data : [])
    }
    const loadKeys = async () => {
      const data = await api('/admin/api-keys')
      setApiKeys(Array.isArray(data) ? data : [])
    }

    useEffect(() => {
      Promise.all([loadUsers(), loadKeys()])
        .catch((e: any) => notify(e.message || 'Could not load admin data', 'error'))
        .finally(() => setLoading(false))
    }, [token])

    useEffect(() => {
      if (selectedUserId == null && users.length > 0) setSelectedUserId(users[0].id)
    }, [users, selectedUserId])

    const changeRole = async (userId: number, role: string) => {
      try {
        await api(`/admin/users/${userId}`, { method: 'PATCH', body: JSON.stringify({ role }) })
        await loadUsers()
        notify('User role updated', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not update the role', 'error')
      }
    }

    const toggleActive = async (u: any) => {
      try {
        await api(`/admin/users/${u.id}`, { method: 'PATCH', body: JSON.stringify({ is_active: !u.is_active }) })
        await loadUsers()
        notify(u.is_active ? 'User deactivated' : 'User reactivated', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not update the user', 'error')
      }
    }

    const createUser = async (e: any) => {
      e.preventDefault()
      setCreatingUser(true)
      setCreateUserError('')
      try {
        await api('/admin/users', { method: 'POST', body: JSON.stringify(newUser) })
        setShowCreateUser(false)
        setNewUser({ email: '', password: '', full_name: '', role: 'analyst' })
        await loadUsers()
        notify('User created', 'success')
      } catch (e: any) {
        setCreateUserError(e.message || 'Could not create the user')
      } finally {
        setCreatingUser(false)
      }
    }

    const createKey = async (e: any) => {
      e.preventDefault()
      if (!newKeyName.trim()) return
      setCreatingKey(true)
      try {
        const created = await api('/admin/api-keys', { method: 'POST', body: JSON.stringify({ name: newKeyName }) })
        setMintedKey(created.api_key || null)
        setNewKeyName('')
        await loadKeys()
        notify('API key created. Copy it now, it will not be shown again.', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not create the API key', 'error')
      } finally {
        setCreatingKey(false)
      }
    }

    const confirmRevoke = async () => {
      const key = pendingRevoke
      setPendingRevoke(null)
      if (!key) return
      try {
        await api(`/admin/api-keys/${key.id}`, { method: 'DELETE' })
        await loadKeys()
        notify('API key revoked', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not revoke the API key', 'error')
      }
    }

    const closeReset = () => {
      if (resettingPassword) return
      setResetUser(null)
      setTemporaryPassword(null)
      setResetError('')
    }

    const resetPassword = async () => {
      if (!resetUser) return
      setResettingPassword(true)
      setResetError('')
      try {
        const result = await api(`/admin/users/${resetUser.id}/reset-password`, { method: 'POST' })
        setTemporaryPassword(result.temporary_password)
        notify('Temporary password generated. Share it securely.', 'success')
      } catch (e: any) {
        setResetError(e.message || 'Could not reset the password')
      } finally {
        setResettingPassword(false)
      }
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Admin</h1>
        <p style={styles.hint}>Manage platform users and programmatic API keys. Admin-only.</p>

        <SplitPanel
          title="Users"
          loading={loading}
          action={<button type="button" onClick={() => { setShowCreateUser(true); setCreateUserError('') }} style={styles.darkActionBtn}>+ Create user</button>}
          items={users}
          selectedId={selectedUserId}
          onSelect={(u) => setSelectedUserId(u.id)}
          emptyLabel="No users yet."
          renderRow={(u) => (
            <>
              <div style={styles.listRowMain}>
                <div className="list-row-title" style={styles.listRowTitle}>{u.email}</div>
                <div style={styles.listRowSub}>{u.full_name || '-'}</div>
              </div>
              <Badge tone={u.is_active ? 'success' : 'danger'}>{u.is_active ? 'Active' : 'Disabled'}</Badge>
            </>
          )}
          renderDetail={(u) => (
            <>
              <div style={styles.detailHeading}>{u.email}</div>
              <div style={styles.detailSub}>{u.full_name || '-'}</div>
              <div style={styles.detailLabel}>Role</div>
              <select
                aria-label={`Role for ${u.email}`}
                value={u.role}
                onChange={(e) => changeRole(u.id, e.target.value)}
                style={{ ...styles.input, background: 'var(--c-field-strong)', color: 'var(--c-text)', border: '1px solid var(--c-border-strong)' }}
              >
                <option value="admin">Admin</option>
                <option value="analyst">Analyst</option>
                <option value="client">Client</option>
              </select>
              <div style={styles.detailLabel}>Account access</div>
              <button type="button" onClick={() => toggleActive(u)} style={styles.darkActionBtn}>
                {u.is_active ? 'Disable account' : 'Enable account'}
              </button>
              <p style={{ ...styles.listRowSub, marginTop: '0.6rem' }}>
                {u.is_active
                  ? 'Disabling immediately blocks sign-in and API access for this user.'
                  : 'This account cannot sign in until it is enabled again.'}
              </p>
              <div style={styles.detailLabel}>Credentials</div>
              <button
                type="button"
                onClick={() => { setResetUser(u); setTemporaryPassword(null); setResetError('') }}
                style={styles.darkActionBtn}
              >
                Reset password
              </button>
              <p style={{ ...styles.listRowSub, marginTop: '0.6rem' }}>
                Generates a one-time password for a locked-out user. It is shown once and never stored in the audit log.
              </p>
            </>
          )}
        />

        <div style={{ ...styles.panelDark, marginTop: '1rem' }}>
          <div style={styles.panelHeader}>
            <h3 style={styles.panelTitle}>API Keys</h3>
            <button type="button" onClick={() => { setMintedKey(null); setShowCreate(true) }} style={styles.darkActionBtn}>+ Create key</button>
          </div>
          <p style={{ ...styles.hint, padding: '0 1.25rem', color: 'var(--c-text-dim)' }}>
            Keys authenticate programmatic access via the <code>X-API-Key</code> header, scoped to the admin account that minted them.
          </p>

          {showCreate && (
            <Modal title="Create API key" onClose={() => setShowCreate(false)}>
              {mintedKey ? (
                <>
                  <div style={styles.codeBlock}>
                    {mintedKey}
                    <div style={{ color: 'var(--c-warn)', marginTop: '0.5rem', fontFamily: 'inherit' }}>Copy this now. It will not be shown again.</div>
                  </div>
                  <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <Button
                      onClick={() => { navigator.clipboard?.writeText(mintedKey); notify('API key copied to clipboard', 'success') }}
                    >
                      Copy key
                    </Button>
                    <Button variant="secondaryDark" onClick={() => setShowCreate(false)}>Done</Button>
                  </div>
                </>
              ) : (
                <form onSubmit={createKey}>
                  <Field label="Key name" htmlFor="key-name" tone="dark" required hint="Something recognisable, like ci-pipeline">
                    <TextInput value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} autoFocus />
                  </Field>
                  <Button type="submit" loading={creatingKey} disabled={!newKeyName.trim()}>Create key</Button>
                </form>
              )}
            </Modal>
          )}

          <div style={{ padding: '0 1.25rem 1.25rem' }}>
            {apiKeys.length === 0 && <div style={styles.listRowSub}>No API keys yet.</div>}
            {apiKeys.map((k: any) => (
              <div key={k.id} style={styles.auditRow}>
                <div>
                  <strong style={{ color: 'var(--c-text)' }}>{k.name}</strong>
                  <span style={styles.listRowSub}> · {k.key_prefix}… · owner #{k.owner_id}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Badge tone={k.is_active ? 'success' : 'neutral'}>{k.is_active ? 'Active' : 'Revoked'}</Badge>
                  {k.is_active && (
                    <button type="button" onClick={() => setPendingRevoke(k)} style={styles.buttonSmall}>Revoke</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {showCreateUser && (
          <Modal title="Create user" onClose={() => { if (!creatingUser) setShowCreateUser(false) }}>
            <form onSubmit={createUser}>
              {createUserError && (
                <div role="alert" style={{ color: 'var(--c-danger)', fontSize: '0.82rem', marginBottom: '0.8rem' }}>
                  {createUserError}
                </div>
              )}
              <Field label="Email" htmlFor="new-user-email" tone="dark" required>
                <TextInput
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  autoFocus
                  required
                />
              </Field>
              <Field label="Full name" htmlFor="new-user-name" tone="dark">
                <TextInput
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                />
              </Field>
              <Field label="Temporary password" htmlFor="new-user-password" tone="dark" required hint="At least 8 characters. Share it securely; they can change it after signing in.">
                <TextInput
                  type="text"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  required
                />
              </Field>
              <Field label="Role" htmlFor="new-user-role" tone="dark" required>
                <Select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  tone="dark"
                >
                  <option value="admin">Admin</option>
                  <option value="analyst">Analyst</option>
                  <option value="client">Client</option>
                </Select>
              </Field>
              <Button type="submit" loading={creatingUser} disabled={!newUser.email.trim() || newUser.password.length < 8}>
                Create user
              </Button>
            </form>
          </Modal>
        )}

        {resetUser && (
          <Modal title={`Reset password for ${resetUser.email}`} onClose={closeReset}>
            {temporaryPassword ? (
              <>
                <p style={{ color: 'var(--c-text-soft)', fontSize: '0.85rem', marginTop: 0 }}>
                  Share this temporary password securely. The user should change it after signing in.
                </p>
                <div style={styles.codeBlock}>
                  {temporaryPassword}
                  <div style={{ color: 'var(--c-warn)', marginTop: '0.5rem', fontFamily: 'inherit' }}>
                    This will not be shown again.
                  </div>
                </div>
                <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <Button
                    onClick={() => {
                      navigator.clipboard?.writeText(temporaryPassword)
                      notify('Temporary password copied to clipboard', 'success')
                    }}
                  >
                    Copy password
                  </Button>
                  <Button variant="secondaryDark" onClick={closeReset}>Done</Button>
                </div>
              </>
            ) : (
              <>
                <p style={{ color: 'var(--c-text-soft)', fontSize: '0.85rem', marginTop: 0 }}>
                  This replaces the user&apos;s current password immediately. Their existing session may stay active until it expires.
                </p>
                {resetError && (
                  <div role="alert" style={{ color: 'var(--c-danger)', fontSize: '0.82rem', marginBottom: '0.8rem' }}>
                    {resetError}
                  </div>
                )}
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <Button onClick={resetPassword} loading={resettingPassword}>Generate temporary password</Button>
                  <Button variant="secondaryDark" onClick={closeReset} disabled={resettingPassword}>Cancel</Button>
                </div>
              </>
            )}
          </Modal>
        )}

        <ConfirmDialog
          open={Boolean(pendingRevoke)}
          title="Revoke this API key?"
          description={
            pendingRevoke
              ? `"${pendingRevoke.name}" will stop working immediately. Any integration using it will fail until a new key is issued.`
              : ''
          }
          confirmLabel="Revoke key"
          onConfirm={confirmRevoke}
          onCancel={() => setPendingRevoke(null)}
        />
      </div>
    )
  }
// ============================================================
// MONITORS (Continuous Monitoring)
// ============================================================
function MonitorsSection({ ctx }: { ctx: any }) {
  const { api, token, notify, monitors, setMonitors, canManage } = ctx
    const [newMonitor, setNewMonitor] = useState({ target: '', monitor_type: 'access_anomaly', client_id: '' })
    const [clientsForMonitor, setClientsForMonitor] = useState<any[]>([])
    const [selectedId, setSelectedId] = useState<any>(null)
    const [monitorAlerts, setMonitorAlerts] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [pendingDelete, setPendingDelete] = useState<any>(null)
    const [editingId, setEditingId] = useState<any>(null)
    const [editForm, setEditForm] = useState({ target: '', monitor_type: '' })
    const [savingEdit, setSavingEdit] = useState(false)

    useEffect(() => {
      Promise.all([api('/monitors'), api('/clients')])
        .then(([monitorsData, clientsData]) => {
          setMonitors(Array.isArray(monitorsData) ? monitorsData : [])
          setClientsForMonitor(Array.isArray(clientsData) ? clientsData : [])
        })
        .catch((e: any) => notify(e.message || 'Could not load monitors', 'error'))
        .finally(() => setLoading(false))
    }, [token])

    useEffect(() => {
      if (selectedId != null || monitors.length === 0) return
      const first = monitors[0]
      setSelectedId(first.id)
      setMonitorAlerts([])
      api(`/monitors/${first.id}/alerts`)
        .then((d: any) => setMonitorAlerts(Array.isArray(d) ? d : []))
        .catch((e: any) => notify(e.message || 'Could not load monitor alerts', 'error'))
    }, [monitors, selectedId])

    const refreshMonitors = async () => {
      try {
        const data = await api('/monitors')
        setMonitors(Array.isArray(data) ? data : [])
      } catch (e: any) {
        notify(e.message || 'Could not refresh monitors', 'error')
      }
    }

    const createMonitor = async (e: any) => {
      e.preventDefault()
      setSubmitting(true)
      try {
        await api('/monitors', {
          method: 'POST',
          body: JSON.stringify({ ...newMonitor, client_id: parseInt(newMonitor.client_id) }),
        })
        setNewMonitor({ target: '', monitor_type: 'access_anomaly', client_id: '' })
        notify('Monitor created', 'success')
        refreshMonitors()
      } catch (e: any) {
        notify(e.message || 'Could not create the monitor', 'error')
      } finally {
        setSubmitting(false)
      }
    }

    const runCheck = async (id: number) => {
      try {
        const res = await api(`/monitors/${id}/check`, { method: 'POST' })
        notify(`Monitor check complete: ${res.alerts_created || 0} alert(s) created`, 'success')
        const alertsData = await api(`/monitors/${id}/alerts`)
        setMonitorAlerts(Array.isArray(alertsData) ? alertsData : [])
        refreshMonitors()
      } catch (e: any) {
        notify(e.message || 'The monitor check failed', 'error')
      }
    }

    const toggleActive = async (m: any) => {
      try {
        await api(`/monitors/${m.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ is_active: !m.is_active }),
        })
        notify(m.is_active ? 'Monitor paused' : 'Monitor resumed', 'success')
        refreshMonitors()
      } catch (e: any) {
        notify(e.message || 'Could not update the monitor', 'error')
      }
    }

    const confirmDelete = async () => {
      const m = pendingDelete
      setPendingDelete(null)
      if (!m) return
      try {
        await api(`/monitors/${m.id}`, { method: 'DELETE' })
        setSelectedId(null)
        setMonitorAlerts([])
        notify('Monitor deleted', 'success')
        refreshMonitors()
      } catch (e: any) {
        notify(e.message || 'Could not delete the monitor', 'error')
      }
    }

    const startEdit = (m: any) => {
      setEditForm({ target: m.target, monitor_type: m.monitor_type })
      setEditingId(m.id)
    }

    const saveEdit = async (e: any) => {
      e.preventDefault()
      setSavingEdit(true)
      try {
        await api(`/monitors/${editingId}`, { method: 'PATCH', body: JSON.stringify(editForm) })
        setEditingId(null)
        await refreshMonitors()
        notify('Monitor updated', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not update the monitor', 'error')
      } finally {
        setSavingEdit(false)
      }
    }

    const canSubmit = Boolean(newMonitor.client_id && newMonitor.target.trim())

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Continuous Monitoring</h1>
        <p style={styles.hint}>
          AI agents continuously watch for anomalous access, config drift, leaked credentials,
          and policy violations before they go live.
        </p>

        {canManage && (
        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Create Monitor</h3>
          <form onSubmit={createMonitor}>
            <Field label="Client" htmlFor="monitor-client" required>
              <Select
                value={newMonitor.client_id}
                onChange={(e) => setNewMonitor({ ...newMonitor, client_id: e.target.value })}
              >
                <option value="">Select a client</option>
                {clientsForMonitor.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Field>
            <Field label="What to watch" htmlFor="monitor-type">
              <Select
                value={newMonitor.monitor_type}
                onChange={(e) => setNewMonitor({ ...newMonitor, monitor_type: e.target.value })}
              >
                <option value="access_anomaly">Access anomaly detection</option>
                <option value="config_drift">Configuration drift</option>
                <option value="leaked_cred">Leaked credentials</option>
                <option value="policy_violation">Policy violation</option>
              </Select>
            </Field>
            <Field label="Target" htmlFor="monitor-target" required hint="Domain or URL, for example bank.sn">
              <TextInput
                value={newMonitor.target}
                onChange={(e) => setNewMonitor({ ...newMonitor, target: e.target.value })}
              />
            </Field>
            <Button type="submit" loading={submitting} disabled={!canSubmit}>Create monitor</Button>
          </form>
        </div>
        )}

        <SplitPanel
          title="Monitors"
          loading={loading}
          items={monitors}
          selectedId={selectedId}
          onSelect={async (m) => {
            setSelectedId(m.id)
            setMonitorAlerts([])
            try {
              const d = await api(`/monitors/${m.id}/alerts`)
              setMonitorAlerts(Array.isArray(d) ? d : [])
            } catch (e: any) {
              notify(e.message || 'Could not load monitor alerts', 'error')
            }
          }}
          emptyLabel="No monitors yet."
          emptyHint="Create a monitor to watch for drift, leaks, and anomalous access."
          renderRow={(m) => (
            <>
              <div style={styles.listRowMain}>
                <div className="list-row-title" style={styles.listRowTitle}>{m.target}</div>
                <div style={styles.listRowSub}>{m.monitor_type}</div>
              </div>
              <Badge tone={m.is_active ? 'success' : 'neutral'}>{m.is_active ? 'Active' : 'Inactive'}</Badge>
            </>
          )}
          renderDetail={(m) => (
            <>
              {editingId === m.id ? (
                <form onSubmit={saveEdit}>
                  <Field label="Target" htmlFor="monitor-edit-target" tone="dark" required>
                    <TextInput
                      value={editForm.target}
                      onChange={(e) => setEditForm({ ...editForm, target: e.target.value })}
                      autoFocus
                      required
                    />
                  </Field>
                  <Field label="What to watch" htmlFor="monitor-edit-type" tone="dark">
                    <Select value={editForm.monitor_type} onChange={(e) => setEditForm({ ...editForm, monitor_type: e.target.value })} tone="dark">
                      <option value="access_anomaly">Access anomaly detection</option>
                      <option value="config_drift">Configuration drift</option>
                      <option value="leaked_cred">Leaked credentials</option>
                      <option value="policy_violation">Policy violation</option>
                    </Select>
                  </Field>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <Button type="submit" loading={savingEdit} disabled={!editForm.target.trim()}>Save changes</Button>
                    <Button type="button" variant="secondaryDark" onClick={() => setEditingId(null)} disabled={savingEdit}>Cancel</Button>
                  </div>
                </form>
              ) : (
                <>
                  <div style={styles.detailHeading}>{m.target}</div>
                  <div style={styles.detailSub}>{m.monitor_type} · last check {m.last_check ? new Date(m.last_check).toLocaleString() : 'never'}</div>
                  {canManage && (
                    <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <button type="button" onClick={() => runCheck(m.id)} style={styles.darkActionBtn}>Run check now</button>
                      <button type="button" onClick={() => startEdit(m)} style={styles.darkActionBtn}>Edit</button>
                      <button type="button" onClick={() => toggleActive(m)} style={styles.darkActionBtn}>
                        {m.is_active ? 'Pause' : 'Resume'}
                      </button>
                      <button type="button" onClick={() => setPendingDelete(m)} style={styles.darkActionBtn}>Delete</button>
                    </div>
                  )}
                </>
              )}
              {monitorAlerts.length > 0 && (
                <>
                  <div style={styles.detailLabel}>Alerts</div>
                  {monitorAlerts.map((a: any) => (
                    <div key={a.id} style={styles.auditRow}>
                      <div>{a.title}</div>
                      <Badge tone={severityTone(a.severity)}>{a.severity}</Badge>
                    </div>
                  ))}
                </>
              )}
            </>
          )}
        />

        <ConfirmDialog
          open={Boolean(pendingDelete)}
          title="Delete this monitor?"
          description={
            pendingDelete
              ? `The monitor for ${pendingDelete.target} and its alerts will be permanently removed. This cannot be undone.`
              : ''
          }
          confirmLabel="Delete monitor"
          onConfirm={confirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      </div>
    )
}

// ============================================================
// ALERTS
// ============================================================
function AlertsSection({ ctx }: { ctx: any }) {
  const { api, token, notify, canManage } = ctx
    const [alerts, setAlerts] = useState<any[]>([])
    const [statusFilter, setStatusFilter] = useState('')
    const [severityFilter, setSeverityFilter] = useState('')
    const [loading, setLoading] = useState(true)
    const [busyId, setBusyId] = useState<any>(null)

    const load = async () => {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter) params.set('status', statusFilter)
      if (severityFilter) params.set('severity', severityFilter)
      const qs = params.toString()
      try {
        const data = await api(`/alerts${qs ? `?${qs}` : ''}`)
        setAlerts(Array.isArray(data) ? data : [])
      } catch (e: any) {
        notify(e.message || 'Could not load alerts', 'error')
      } finally {
        setLoading(false)
      }
    }

    useEffect(() => { load() }, [token, statusFilter, severityFilter])

    const setStatus = async (alert: any, status: string) => {
      setBusyId(alert.id)
      try {
        await api(`/alerts/${alert.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ status }),
        })
        notify(`Alert marked ${status.replace('_', ' ')}`, 'success')
        await load()
      } catch (e: any) {
        notify(e.message || 'Could not update the alert', 'error')
      } finally {
        setBusyId(null)
      }
    }

    const openCount = alerts.filter((a: any) => a.status === 'open').length

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Monitoring Alerts</h1>
        <p style={styles.hint}>
          {canManage
            ? openCount > 0
              ? `${openCount} open alert${openCount === 1 ? '' : 's'} need review. Acknowledge to claim one, resolve when fixed.`
              : 'No open alerts right now. Acknowledge and resolve each alert as it arrives.'
            : openCount > 0
              ? `${openCount} open alert${openCount === 1 ? '' : 's'} on your account. Your Ultorn analyst will review ${openCount === 1 ? 'it' : 'them'}.`
              : 'No open alerts on your account right now.'}
        </p>

        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <select
            className="alerts-filter"
            aria-label="Filter alerts by status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ ...styles.input, maxWidth: 200 }}
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
            <option value="false_positive">False positive</option>
          </select>
          <select
            className="alerts-filter"
            aria-label="Filter alerts by severity"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{ ...styles.input, maxWidth: 200 }}
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div style={styles.lightCard}>
          <div style={styles.tableWrap}>
            <table className="responsive-table" style={{ width: '100%', borderCollapse: 'collapse', minWidth: 620 }}>
              <caption className="sr-only">Monitoring alerts with severity, status, and time detected</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--c-border)' }}>
                <th scope="col" style={styles.th}>Alert</th>
                <th scope="col" style={styles.th}>Severity</th>
                <th scope="col" style={styles.th}>Status</th>
                <th scope="col" style={styles.th}>Detected</th>
                <th scope="col" style={styles.th}><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={5} style={styles.tdEmpty} role="status">Loading alerts…</td></tr>
              )}
              {!loading && alerts.length === 0 && (
                <tr>
                  <td colSpan={5} style={styles.tdEmpty}>
                    {statusFilter || severityFilter ? 'No alerts match these filters.' : 'No alerts yet. Monitoring agents will file them here.'}
                  </td>
                </tr>
              )}
              {alerts.map((a: any) => (
                <tr key={a.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                  <td className="responsive-primary" style={styles.td}>
                    <div>{a.title}</div>
                    {a.description && <div style={{ fontSize: '0.78rem', color: TEXT_DIM }}>{a.description}</div>}
                  </td>
                  <td data-label="Severity" style={styles.td}><Badge tone={severityTone(a.severity)}>{a.severity}</Badge></td>
                  <td data-label="Status" style={styles.td}>{a.status.replace('_', ' ')}</td>
                  <td data-label="Detected" style={{ ...styles.td, fontSize: '0.8rem', color: TEXT_FAINT }}>{new Date(a.created_at).toLocaleString()}</td>
                  <td className="responsive-actions" style={{ ...styles.td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {canManage && a.status === 'open' && (
                      <button
                        type="button"
                        onClick={() => setStatus(a, 'acknowledged')}
                        disabled={busyId === a.id}
                        style={styles.buttonGhostLight}
                      >
                        Acknowledge
                      </button>
                    )}
                    {canManage && a.status !== 'resolved' && (
                      <button
                        type="button"
                        onClick={() => setStatus(a, 'resolved')}
                        disabled={busyId === a.id}
                        style={{ ...styles.buttonGhostLight, marginLeft: '0.4rem' }}
                      >
                        Resolve
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      </div>
    )
}

// ============================================================
// SCAN SCHEDULES
// ============================================================
function SchedulesSection({ ctx }: { ctx: any }) {
  const { api, token, notify, canManage } = ctx
    const [schedules, setSchedules] = useState<any[]>([])
    const [clientsForSchedule, setClientsForSchedule] = useState<any[]>([])
    const [newSchedule, setNewSchedule] = useState({ client_id: '', scan_type: 'vulnerability', interval_minutes: '1440' })
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [pendingDelete, setPendingDelete] = useState<any>(null)
    const [editingId, setEditingId] = useState<any>(null)
    const [editForm, setEditForm] = useState({ scan_type: 'vulnerability', interval_minutes: '1440' })
    const [savingEdit, setSavingEdit] = useState(false)

    const load = async () => {
      try {
        const data = await api('/scan-schedules')
        setSchedules(Array.isArray(data) ? data : [])
      } catch (e: any) {
        notify(e.message || 'Could not load schedules', 'error')
      } finally {
        setLoading(false)
      }
    }

    useEffect(() => {
      load()
      api('/clients')
        .then((data: any) => setClientsForSchedule(Array.isArray(data) ? data : []))
        .catch((e: any) => notify(e.message || 'Could not load clients', 'error'))
    }, [token])

    const createSchedule = async (e: any) => {
      e.preventDefault()
      setSubmitting(true)
      try {
        await api('/scan-schedules', {
          method: 'POST',
          body: JSON.stringify({
            client_id: parseInt(newSchedule.client_id),
            scan_type: newSchedule.scan_type,
            interval_minutes: parseInt(newSchedule.interval_minutes),
          }),
        })
        setNewSchedule({ client_id: '', scan_type: 'vulnerability', interval_minutes: '1440' })
        notify('Scan schedule created', 'success')
        load()
      } catch (e: any) {
        notify(e.message || 'Could not create the schedule', 'error')
      } finally {
        setSubmitting(false)
      }
    }

    const toggle = async (s: any) => {
      try {
        await api(`/scan-schedules/${s.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ is_active: !s.is_active }),
        })
        notify(s.is_active ? 'Schedule paused' : 'Schedule resumed', 'success')
        load()
      } catch (e: any) {
        notify(e.message || 'Could not update the schedule', 'error')
      }
    }

    const runNow = async (s: any) => {
      try {
        const res = await api(`/scan-schedules/${s.id}/run`, { method: 'POST' })
        notify(`Scan #${res.scan_id} started and completed`, 'success')
        load()
      } catch (e: any) {
        notify(e.message || 'Could not run the schedule', 'error')
      }
    }

    const confirmDelete = async () => {
      const s = pendingDelete
      setPendingDelete(null)
      if (!s) return
      try {
        await api(`/scan-schedules/${s.id}`, { method: 'DELETE' })
        notify('Schedule deleted', 'success')
        load()
      } catch (e: any) {
        notify(e.message || 'Could not delete the schedule', 'error')
      }
    }

    const startEdit = (s: any) => {
      setEditForm({ scan_type: s.scan_type, interval_minutes: String(s.interval_minutes) })
      setEditingId(s.id)
    }

    const saveEdit = async (e: any) => {
      e.preventDefault()
      setSavingEdit(true)
      try {
        await api(`/scan-schedules/${editingId}`, {
          method: 'PATCH',
          body: JSON.stringify({ scan_type: editForm.scan_type, interval_minutes: parseInt(editForm.interval_minutes) }),
        })
        setEditingId(null)
        notify('Schedule updated', 'success')
        load()
      } catch (e: any) {
        notify(e.message || 'Could not update the schedule', 'error')
      } finally {
        setSavingEdit(false)
      }
    }

    const humanInterval = (minutes: number) => {
      if (minutes === 60) return 'Every hour'
      if (minutes === 360) return 'Every 6 hours'
      if (minutes === 1440) return 'Daily'
      if (minutes === 10080) return 'Weekly'
      if (minutes === 43200) return 'Monthly'
      if (minutes % 1440 === 0) return `Every ${minutes / 1440} days`
      if (minutes % 60 === 0) return `Every ${minutes / 60} hours`
      return `Every ${minutes} minutes`
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Recurring Scans</h1>
        <p style={styles.hint}>
          {canManage
            ? "Schedule vulnerability assessments to run automatically. Each run uses the client's current non-excluded scopes and files findings for human review."
            : 'See the recurring assessments configured for your organization. Each run uses your current non-excluded scopes and files findings for review.'}
        </p>

        {canManage && (
        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Create Schedule</h3>
          <form onSubmit={createSchedule}>
            <Field label="Client" htmlFor="schedule-client" required>
              <Select
                value={newSchedule.client_id}
                onChange={(e) => setNewSchedule({ ...newSchedule, client_id: e.target.value })}
              >
                <option value="">Select a client</option>
                {clientsForSchedule.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Field>
            <Field label="Assessment type" htmlFor="schedule-type">
              <Select
                value={newSchedule.scan_type}
                onChange={(e) => setNewSchedule({ ...newSchedule, scan_type: e.target.value })}
              >
                <option value="vulnerability">Vulnerability</option>
                <option value="full">Full assessment</option>
                <option value="web">Web application</option>
              </Select>
            </Field>
            <Field label="Frequency" htmlFor="schedule-interval">
              <Select
                value={newSchedule.interval_minutes}
                onChange={(e) => setNewSchedule({ ...newSchedule, interval_minutes: e.target.value })}
              >
                <option value="60">Every hour</option>
                <option value="360">Every 6 hours</option>
                <option value="1440">Daily</option>
                <option value="10080">Weekly</option>
                <option value="43200">Monthly</option>
              </Select>
            </Field>
            <Button type="submit" loading={submitting} disabled={!newSchedule.client_id}>Create schedule</Button>
          </form>
        </div>
        )}

        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Schedules</h3>
          <div style={styles.tableWrap}>
            <table className="responsive-table" style={{ width: '100%', borderCollapse: 'collapse', minWidth: 680 }}>
              <caption className="sr-only">Recurring scan schedules with their next run time</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--c-border)' }}>
                <th scope="col" style={styles.th}>Client</th>
                <th scope="col" style={styles.th}>Type</th>
                <th scope="col" style={styles.th}>Every</th>
                <th scope="col" style={styles.th}>Next run</th>
                <th scope="col" style={styles.th}>Status</th>
                <th scope="col" style={styles.th}><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={6} style={styles.tdEmpty} role="status">Loading schedules…</td></tr>
              )}
              {!loading && schedules.length === 0 && (
                <tr><td colSpan={6} style={styles.tdEmpty}>No schedules yet. Create one above to run scans automatically.</td></tr>
              )}
              {schedules.map((s: any) => (
                editingId === s.id ? (
                  <tr key={s.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                    <td className="responsive-primary" style={styles.td}>{s.client?.name || s.client_id}</td>
                    <td className="responsive-form" data-label="Schedule" style={styles.td} colSpan={2}>
                      <form onSubmit={saveEdit} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                        <select
                          aria-label="Assessment type"
                          value={editForm.scan_type}
                          onChange={(e) => setEditForm({ ...editForm, scan_type: e.target.value })}
                          style={{ ...styles.inputSmall, background: 'var(--c-field-strong)', color: TEXT, border: `1px solid ${BORDER_STRONG}` }}
                        >
                          <option value="vulnerability">Vulnerability</option>
                          <option value="full">Full assessment</option>
                          <option value="web">Web application</option>
                        </select>
                        <select
                          aria-label="Frequency"
                          value={editForm.interval_minutes}
                          onChange={(e) => setEditForm({ ...editForm, interval_minutes: e.target.value })}
                          style={{ ...styles.inputSmall, background: 'var(--c-field-strong)', color: TEXT, border: `1px solid ${BORDER_STRONG}` }}
                        >
                          <option value="60">Every hour</option>
                          <option value="360">Every 6 hours</option>
                          <option value="1440">Daily</option>
                          <option value="10080">Weekly</option>
                          <option value="43200">Monthly</option>
                        </select>
                        <button type="submit" disabled={savingEdit} style={styles.buttonSmall}>Save</button>
                        <button type="button" onClick={() => setEditingId(null)} disabled={savingEdit} style={styles.buttonGhostLight}>Cancel</button>
                      </form>
                    </td>
                    <td data-label="Next run" style={{ ...styles.td, fontSize: '0.8rem', color: TEXT_FAINT }}>
                      {s.next_run ? new Date(s.next_run).toLocaleString() : '—'}
                    </td>
                    <td data-label="Status" style={styles.td}>
                      <Badge tone={s.is_active ? 'success' : 'neutral'}>{s.is_active ? 'Active' : 'Paused'}</Badge>
                    </td>
                    <td className="responsive-actions" style={{ ...styles.td, textAlign: 'right' }} />
                  </tr>
                ) : (
                  <tr key={s.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                    <td className="responsive-primary" style={styles.td}>{s.client?.name || s.client_id}</td>
                    <td data-label="Type" style={styles.td}>{s.scan_type}</td>
                    <td data-label="Every" style={styles.td}>{humanInterval(s.interval_minutes)}</td>
                    <td data-label="Next run" style={{ ...styles.td, fontSize: '0.8rem', color: TEXT_FAINT }}>
                      {s.next_run ? new Date(s.next_run).toLocaleString() : '—'}
                    </td>
                    <td data-label="Status" style={styles.td}>
                      <Badge tone={s.is_active ? 'success' : 'neutral'}>{s.is_active ? 'Active' : 'Paused'}</Badge>
                    </td>
                    <td className="responsive-actions" style={{ ...styles.td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                      {canManage && (
                        <>
                          <button type="button" onClick={() => runNow(s)} style={{ ...styles.buttonGhostLight, marginLeft: '0.4rem' }}>Run now</button>
                          <button type="button" onClick={() => startEdit(s)} style={{ ...styles.buttonGhostLight, marginLeft: '0.4rem' }}>Edit</button>
                          <button type="button" onClick={() => toggle(s)} style={{ ...styles.buttonGhostLight, marginLeft: '0.4rem' }}>{s.is_active ? 'Pause' : 'Resume'}</button>
                          <button type="button" onClick={() => setPendingDelete(s)} style={{ ...styles.buttonGhostLight, marginLeft: '0.4rem' }}>Delete</button>
                        </>
                      )}
                    </td>
                  </tr>
                )
              ))}
            </tbody>
          </table>
          </div>
        </div>

        <ConfirmDialog
          open={Boolean(pendingDelete)}
          title="Delete this schedule?"
          description={
            pendingDelete
              ? `Scans for ${pendingDelete.client?.name || `client #${pendingDelete.client_id}`} will stop running automatically. Existing findings are kept.`
              : ''
          }
          confirmLabel="Delete schedule"
          onConfirm={confirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      </div>
    )
}

// ============================================================
// CODE SCANS
// ============================================================
function CodeScansSection({ ctx }: { ctx: any }) {
  const { api, token, notify, codeScans, setCodeScans, canManage } = ctx
    const [newCodeScan, setNewCodeScan] = useState({ client_id: '', repository_url: '', branch: 'main' })
    const [clientsForCode, setClientsForCode] = useState<any[]>([])
    const [selectedId, setSelectedId] = useState<any>(null)
    const [issues, setIssues] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [issuesLoading, setIssuesLoading] = useState(false)
    const [submitting, setSubmitting] = useState(false)

    const load = async () => {
      try {
        const [scansData, clientsData] = await Promise.all([api('/code-scans'), api('/clients')])
        setCodeScans(Array.isArray(scansData) ? scansData : [])
        setClientsForCode(Array.isArray(clientsData) ? clientsData : [])
      } catch (e: any) {
        notify(e.message || 'Could not load code scans', 'error')
      } finally {
        setLoading(false)
      }
    }

    useEffect(() => { load() }, [token])

    const openIssues = async (scan: any) => {
      setSelectedId(scan.id)
      setIssues([])
      setIssuesLoading(true)
      try {
        const data = await api(`/code-scans/${scan.id}/issues`)
        setIssues(Array.isArray(data) ? data : [])
      } catch (e: any) {
        notify(e.message || 'Could not load issues', 'error')
      } finally {
        setIssuesLoading(false)
      }
    }

    const createCodeScan = async (e: any) => {
      e.preventDefault()
      setSubmitting(true)
      try {
        await api('/code-scans', {
          method: 'POST',
          body: JSON.stringify({ ...newCodeScan, client_id: parseInt(newCodeScan.client_id) }),
        })
        setNewCodeScan({ client_id: '', repository_url: '', branch: 'main' })
        notify('Code scan started', 'success')
        load()
      } catch (e: any) {
        notify(e.message || 'Could not start the code scan', 'error')
      } finally {
        setSubmitting(false)
      }
    }

    const canSubmit = Boolean(newCodeScan.client_id && newCodeScan.repository_url.trim())

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>AI Code Scanning</h1>
        <p style={styles.hint}>
          Detect hardcoded secrets, insecure defaults, vulnerable dependencies,
          and logic flaws in AI-generated code before it ships.
        </p>

        {canManage && (
        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Scan Code</h3>
          <form onSubmit={createCodeScan}>
            <Field label="Client" htmlFor="code-client" required>
              <Select
                value={newCodeScan.client_id}
                onChange={(e) => setNewCodeScan({ ...newCodeScan, client_id: e.target.value })}
              >
                <option value="">Select a client</option>
                {clientsForCode.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Field>
            <Field label="Repository URL or directory" htmlFor="code-repo" required hint="For example github.com/sahel-bank/mobile-api">
              <TextInput
                value={newCodeScan.repository_url}
                onChange={(e) => setNewCodeScan({ ...newCodeScan, repository_url: e.target.value })}
              />
            </Field>
            <Field label="Branch" htmlFor="code-branch">
              <TextInput
                value={newCodeScan.branch}
                onChange={(e) => setNewCodeScan({ ...newCodeScan, branch: e.target.value })}
              />
            </Field>
            <Button type="submit" loading={submitting} disabled={!canSubmit}>Scan code</Button>
          </form>
        </div>
        )}

        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Code Scans</h3>
          <div style={styles.tableWrap}>
            <table className="responsive-table" style={{ width: '100%', borderCollapse: 'collapse', minWidth: 620 }}>
              <caption className="sr-only">Code scans and the issues found in each</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--c-border)' }}>
                <th scope="col" style={styles.th}>Repository</th>
                <th scope="col" style={styles.th}>Branch</th>
                <th scope="col" style={styles.th}>Status</th>
                <th scope="col" style={styles.th}>Issues</th>
                <th scope="col" style={styles.th}><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={5} style={styles.tdEmpty}>Loading code scans…</td></tr>
              )}
              {!loading && codeScans.length === 0 && (
                <tr><td colSpan={5} style={styles.tdEmpty}>No code scans yet. Scan a repository above to get started.</td></tr>
              )}
              {codeScans.map((s: any) => (
                <tr key={s.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                  <td className="responsive-primary" style={{ ...styles.td, overflowWrap: 'anywhere' }}>{s.repository_url || '-'}</td>
                  <td data-label="Branch" style={styles.td}>{s.branch}</td>
                  <td data-label="Status" style={styles.td}><Badge tone={s.status === 'completed' ? 'success' : 'warning'}>{s.status}</Badge></td>
                  <td data-label="Issues" style={styles.td}>{s.issues_found}</td>
                  <td className="responsive-actions" style={{ ...styles.td, textAlign: 'right' }}>
                    <button type="button" onClick={() => openIssues(s)} style={styles.buttonGhostLight}>
                      View issues
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>

        {selectedId && (
          <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
            <h3 style={styles.h3}>Issues</h3>
            {issuesLoading && <p style={styles.mutedText} role="status">Loading issues…</p>}
            {!issuesLoading && issues.length === 0 && <p style={styles.mutedText}>No issues found in this scan.</p>}
            {issues.map((i: any) => (
              <div key={i.id} style={styles.auditRowLight}>
                <div style={{ flex: 1 }}>
                  <strong>{i.file_path}</strong>:{i.line_number}
                  <br />
                  <span style={styles.mutedText}>{i.issue_type}</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <Badge tone={severityTone(i.severity || 'medium')}>{i.severity}</Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
}

// ============================================================
// AUTHORIZATION HUNTS (autonomous IDOR/BOLA proof-of-exploit)
// ============================================================
function verdictTone(v: string) {
  switch (v) {
    case 'confirmed_leak': return 'danger'
    case 'inconclusive': return 'warning'
    case 'no_leak': return 'success'
    default: return 'neutral'
  }
}

function verdictLabel(v: string) {
  switch (v) {
    case 'confirmed_leak': return 'Confirmed leak'
    case 'no_leak': return 'No leak'
    case 'inconclusive': return 'Inconclusive'
    case 'probe_error': return 'Probe error'
    default: return v
  }
}

const HEADER_NAME_OPTIONS = ['Authorization', 'Cookie', 'X-API-Key', 'X-Auth-Token']

function emptyRole() {
  return { name: '', header_name: 'Authorization', header_value: '' }
}

function emptyProbe() {
  return { method: 'GET', path: '', id_param: 'id', owner_role: '', owner_value: '', description: '' }
}

function emptyCrawlRole() {
  return {
    role_name: '',
    start_url: '',
    login_url: '',
    username_selector: '#username',
    username: '',
    password_selector: '#password',
    password: '',
    submit_selector: 'button[type=submit]',
  }
}

function AuthzSection({ ctx }: { ctx: any }) {
  const { api, token, notify, authzHunts, setAuthzHunts, canManage } = ctx
  const [clientsForAuthz, setClientsForAuthz] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [suggesting, setSuggesting] = useState(false)
  const [specUrl, setSpecUrl] = useState('')
  const [showCrawl, setShowCrawl] = useState(false)
  const [crawling, setCrawling] = useState(false)
  const [crawlRoles, setCrawlRoles] = useState([emptyCrawlRole(), emptyCrawlRole()])
  const [newHunt, setNewHunt] = useState({ client_id: '' as any, base_url: '' })
  const [roles, setRoles] = useState([emptyRole(), emptyRole()])
  const [probes, setProbes] = useState([emptyProbe()])
  const [selectedHuntId, setSelectedHuntId] = useState<any>(null)
  const [huntFindings, setHuntFindings] = useState<any[]>([])
  const [findingsLoading, setFindingsLoading] = useState(false)
  const [expandedEvidence, setExpandedEvidence] = useState<Record<number, boolean>>({})

  const load = async () => {
    try {
      const [huntsData, clientsData] = await Promise.all([api('/authz-hunts'), api('/clients')])
      setAuthzHunts(Array.isArray(huntsData) ? huntsData : [])
      setClientsForAuthz(Array.isArray(clientsData) ? clientsData : [])
    } catch (e: any) {
      notify(e.message || 'Could not load authorization hunts', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [token])

  const openFindings = async (hunt: any) => {
    setSelectedHuntId(hunt.id)
    setHuntFindings([])
    setExpandedEvidence({})
    setFindingsLoading(true)
    try {
      const data = await api(`/authz-hunts/${hunt.id}/findings`)
      setHuntFindings(Array.isArray(data) ? data : [])
    } catch (e: any) {
      notify(e.message || 'Could not load findings', 'error')
    } finally {
      setFindingsLoading(false)
    }
  }

  const reviewFinding = async (findingId: number) => {
    try {
      await api(`/authz-findings/${findingId}/review`, { method: 'POST', body: JSON.stringify({}) })
      notify('Finding marked reviewed', 'success')
      setHuntFindings((prev: any[]) =>
        prev.map((f) => (f.id === findingId ? { ...f, reviewed_at: new Date().toISOString() } : f))
      )
    } catch (e: any) {
      notify(e.message || 'Could not record the review', 'error')
    }
  }

  const suggestProbes = async () => {
    if (!specUrl.trim()) return
    setSuggesting(true)
    try {
      const res = await api('/authz-hunts/suggest-probes', {
        method: 'POST',
        body: JSON.stringify({ spec_url: specUrl.trim() }),
      })
      const suggestions = Array.isArray(res?.suggestions) ? res.suggestions : []
      if (suggestions.length === 0) {
        notify('No id-shaped GET endpoints found in that spec', 'info')
        return
      }
      setProbes((prev) => {
        // Drop a single still-empty starter probe before appending suggestions.
        const base = prev.length === 1 && !prev[0].path ? [] : prev
        return [
          ...base,
          ...suggestions.map((s: any) => ({
            method: s.method,
            path: s.path,
            id_param: s.id_param,
            owner_role: '',
            owner_value: '',
            description: s.description || '',
          })),
        ]
      })
      notify(`Added ${suggestions.length} suggested probe(s) -- fill in owner_role and owner_value for each`, 'success')
    } catch (e: any) {
      notify(e.message || 'Could not fetch or parse that spec', 'error')
    } finally {
      setSuggesting(false)
    }
  }

  const updateCrawlRole = (i: number, patch: any) =>
    setCrawlRoles((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)))

  const runCrawl = async () => {
    if (!newHunt.base_url.trim()) {
      notify('Enter a base URL above first', 'error')
      return
    }
    setCrawling(true)
    try {
      const res = await api('/authz-hunts/crawl-and-suggest', {
        method: 'POST',
        body: JSON.stringify({
          base_url: newHunt.base_url.trim(),
          max_pages: 15,
          roles: crawlRoles
            .filter((r) => r.role_name.trim() && r.start_url.trim())
            .map((r) => ({
              role_name: r.role_name.trim(),
              start_url: r.start_url.trim(),
              login: r.login_url.trim()
                ? {
                    url: r.login_url.trim(),
                    username_selector: r.username_selector,
                    username: r.username,
                    password_selector: r.password_selector,
                    password: r.password,
                    submit_selector: r.submit_selector,
                  }
                : undefined,
            })),
        }),
      })
      setRoles(
        res.roles.map((r: any) => {
          const [header_name, header_value] = Object.entries(r.headers || {})[0] || ['Cookie', '']
          return { name: r.name, header_name, header_value: String(header_value || '') }
        })
      )
      setProbes(
        res.probes.length > 0
          ? res.probes.map((p: any) => ({ ...p, description: '' }))
          : [emptyProbe()]
      )
      notify(`Crawl found ${res.probes.length} candidate probe(s) across ${res.roles.length} role(s)`, 'success')
    } catch (e: any) {
      notify(e.message || 'Could not crawl that target', 'error')
    } finally {
      setCrawling(false)
    }
  }

  const updateRole = (i: number, patch: Partial<ReturnType<typeof emptyRole>>) =>
    setRoles((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)))
  const updateProbe = (i: number, patch: Partial<ReturnType<typeof emptyProbe>>) =>
    setProbes((prev) => prev.map((p, idx) => (idx === i ? { ...p, ...patch } : p)))

  const createHunt = async (e: any) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const payload = {
        client_id: parseInt(newHunt.client_id),
        base_url: newHunt.base_url.trim(),
        roles: roles
          .filter((r) => r.name.trim())
          .map((r) => ({
            name: r.name.trim(),
            headers: r.header_value.trim() ? { [r.header_name]: r.header_value.trim() } : {},
          })),
        probes: probes
          .filter((p) => p.path.trim() && p.owner_role.trim() && p.owner_value.trim())
          .map((p) => ({
            method: p.method,
            path: p.path.trim(),
            id_param: p.id_param.trim() || 'id',
            owner_role: p.owner_role.trim(),
            owner_value: p.owner_value.trim(),
            description: p.description?.trim() || undefined,
          })),
      }
      if (payload.roles.length < 2) {
        notify('Add at least 2 named roles with their auth headers', 'error')
        setSubmitting(false)
        return
      }
      if (payload.probes.length === 0) {
        notify('Add at least 1 probe with a path, owner role, and owner value', 'error')
        setSubmitting(false)
        return
      }
      await api('/authz-hunts', { method: 'POST', body: JSON.stringify(payload) })
      setNewHunt({ client_id: '', base_url: '' })
      setRoles([emptyRole(), emptyRole()])
      setProbes([emptyProbe()])
      setSpecUrl('')
      notify('Authorization hunt completed', 'success')
      load()
    } catch (e: any) {
      notify(e.message || 'Could not run the authorization hunt', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const canSubmit = Boolean(newHunt.client_id && newHunt.base_url.trim())

  return (
    <div style={styles.section}>
      <h1 style={styles.pageTitle}>Authorization Hunts</h1>
      <p style={styles.hint}>
        Prove broken object-level authorization (IDOR/BOLA) instead of just flagging it: log in
        as two or more roles, replay the same request with another role&apos;s object id, and
        see whether the response leaks their data -- the &quot;change <code>/invoices/1024</code>{' '}
        to <code>/invoices/1025</code>&quot; exploit, automated and evidenced. Confirmed leaks
        still need a named analyst review before they go to a client.
      </p>

      {canManage && (
        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Run a Hunt</h3>
          <form onSubmit={createHunt}>
            <Field label="Client" htmlFor="authz-client" required>
              <Select
                value={newHunt.client_id}
                onChange={(e) => setNewHunt({ ...newHunt, client_id: e.target.value })}
              >
                <option value="">Select a client</option>
                {clientsForAuthz.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Field>
            <Field label="Base URL" htmlFor="authz-base-url" required hint="e.g. https://api.testbank.sn">
              <TextInput
                value={newHunt.base_url}
                onChange={(e) => setNewHunt({ ...newHunt, base_url: e.target.value })}
                placeholder="https://api.example.sn"
              />
            </Field>

            <h4 style={styles.h4}>Roles</h4>
            <p style={styles.mutedText}>At least 2 named, authenticated identities to replay requests as.</p>
            {roles.map((r, i) => (
              <div key={i} style={styles.formRow}>
                <TextInput
                  value={r.name}
                  onChange={(e) => updateRole(i, { name: e.target.value })}
                  placeholder={`Role name (e.g. customer-a)`}
                  aria-label={`Role ${i + 1} name`}
                />
                <Select
                  value={r.header_name}
                  onChange={(e) => updateRole(i, { header_name: e.target.value })}
                  aria-label={`Role ${i + 1} header name`}
                >
                  {HEADER_NAME_OPTIONS.map((h) => <option key={h} value={h}>{h}</option>)}
                </Select>
                <TextInput
                  value={r.header_value}
                  onChange={(e) => updateRole(i, { header_value: e.target.value })}
                  placeholder="Header value (e.g. Bearer eyJ...)"
                  aria-label={`Role ${i + 1} header value`}
                />
                <button
                  type="button"
                  onClick={() => setRoles((prev) => prev.filter((_, idx) => idx !== i))}
                  style={styles.buttonGhostLight}
                  disabled={roles.length <= 2}
                >
                  Remove
                </button>
              </div>
            ))}
            <button type="button" onClick={() => setRoles((prev) => [...prev, emptyRole()])} style={styles.buttonGhostLight}>
              + Add role
            </button>

            <h4 style={{ ...styles.h4, marginTop: '1.25rem' }}>Probes</h4>
            <p style={styles.mutedText}>
              Each probe is one request shape to replay across roles. <code>path</code> must
              contain a <code>{'{'}id_param{'}'}</code> placeholder, and <code>owner_value</code>{' '}
              must be a real object id known to belong to <code>owner_role</code>.
            </p>

            <div style={styles.formRow}>
              <TextInput
                value={specUrl}
                onChange={(e) => setSpecUrl(e.target.value)}
                placeholder="OpenAPI spec URL (optional) -- e.g. https://api.example.sn/openapi.json"
                aria-label="OpenAPI spec URL"
              />
              <Button type="button" variant="secondary" loading={suggesting} onClick={suggestProbes} disabled={!specUrl.trim()}>
                Suggest probes from spec
              </Button>
            </div>

            <button type="button" onClick={() => setShowCrawl((v) => !v)} style={styles.buttonGhostLight}>
              {showCrawl ? 'Hide' : 'No spec? Discover via browser crawl'}
            </button>

            {showCrawl && (
              <div style={{ border: `1px solid ${BORDER}`, padding: '0.9rem', margin: '0.75rem 0' }}>
                <p style={styles.mutedText}>
                  Logs in as each role through its real login form (not a token), crawls same-origin
                  pages, and auto-fills roles (with the resulting session cookie) and probes from
                  what each role was actually able to reach. Requires the backend to have Playwright
                  and a Chromium binary installed.
                </p>
                {crawlRoles.map((r, i) => (
                  <div key={i} style={{ marginBottom: '0.75rem' }}>
                    <div style={styles.formRow}>
                      <TextInput value={r.role_name} onChange={(e) => updateCrawlRole(i, { role_name: e.target.value })} placeholder={`Role name (e.g. customer-${i === 0 ? 'a' : 'b'})`} aria-label={`Crawl role ${i + 1} name`} />
                      <TextInput value={r.start_url} onChange={(e) => updateCrawlRole(i, { start_url: e.target.value })} placeholder="Start URL after login, e.g. https://app.example.sn/dashboard" aria-label={`Crawl role ${i + 1} start URL`} />
                    </div>
                    <div style={{ ...styles.formRow, flexWrap: 'wrap' }}>
                      <TextInput value={r.login_url} onChange={(e) => updateCrawlRole(i, { login_url: e.target.value })} placeholder="Login page URL (leave blank if already public)" aria-label={`Crawl role ${i + 1} login URL`} style={{ minWidth: 220 }} />
                      <TextInput value={r.username} onChange={(e) => updateCrawlRole(i, { username: e.target.value })} placeholder="Username" aria-label={`Crawl role ${i + 1} username`} style={{ maxWidth: 140 }} />
                      <TextInput type="password" value={r.password} onChange={(e) => updateCrawlRole(i, { password: e.target.value })} placeholder="Password" aria-label={`Crawl role ${i + 1} password`} style={{ maxWidth: 140 }} />
                    </div>
                    <div style={{ ...styles.formRow, flexWrap: 'wrap' }}>
                      <TextInput value={r.username_selector} onChange={(e) => updateCrawlRole(i, { username_selector: e.target.value })} placeholder="Username field CSS selector" aria-label={`Crawl role ${i + 1} username selector`} style={{ maxWidth: 180 }} />
                      <TextInput value={r.password_selector} onChange={(e) => updateCrawlRole(i, { password_selector: e.target.value })} placeholder="Password field CSS selector" aria-label={`Crawl role ${i + 1} password selector`} style={{ maxWidth: 180 }} />
                      <TextInput value={r.submit_selector} onChange={(e) => updateCrawlRole(i, { submit_selector: e.target.value })} placeholder="Submit button CSS selector" aria-label={`Crawl role ${i + 1} submit selector`} style={{ maxWidth: 180 }} />
                    </div>
                  </div>
                ))}
                <Button type="button" variant="secondary" loading={crawling} onClick={runCrawl}>
                  Crawl and fill roles/probes
                </Button>
              </div>
            )}

            {probes.map((p, i) => (
              <div key={i} style={{ ...styles.formRow, flexWrap: 'wrap' }}>
                <TextInput
                  value={p.path}
                  onChange={(e) => updateProbe(i, { path: e.target.value })}
                  placeholder="/api/invoices/{id}"
                  aria-label={`Probe ${i + 1} path`}
                  style={{ minWidth: 200 }}
                />
                <TextInput
                  value={p.id_param}
                  onChange={(e) => updateProbe(i, { id_param: e.target.value })}
                  placeholder="id"
                  aria-label={`Probe ${i + 1} id param`}
                  style={{ maxWidth: 100 }}
                />
                <Select
                  value={p.owner_role}
                  onChange={(e) => updateProbe(i, { owner_role: e.target.value })}
                  aria-label={`Probe ${i + 1} owner role`}
                >
                  <option value="">Owner role</option>
                  {roles.filter((r) => r.name.trim()).map((r) => (
                    <option key={r.name} value={r.name}>{r.name}</option>
                  ))}
                </Select>
                <TextInput
                  value={p.owner_value}
                  onChange={(e) => updateProbe(i, { owner_value: e.target.value })}
                  placeholder="owner's object id, e.g. 1024"
                  aria-label={`Probe ${i + 1} owner value`}
                  style={{ maxWidth: 180 }}
                />
                <button
                  type="button"
                  onClick={() => setProbes((prev) => prev.filter((_, idx) => idx !== i))}
                  style={styles.buttonGhostLight}
                >
                  Remove
                </button>
              </div>
            ))}
            <button type="button" onClick={() => setProbes((prev) => [...prev, emptyProbe()])} style={styles.buttonGhostLight}>
              + Add probe
            </button>

            <div style={{ marginTop: '1.25rem' }}>
              <Button type="submit" loading={submitting} disabled={!canSubmit}>Run hunt</Button>
            </div>
          </form>
        </div>
      )}

      <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
        <h3 style={styles.h3}>Hunts</h3>
        <div style={styles.tableWrap}>
          <table className="responsive-table" style={{ width: '100%', borderCollapse: 'collapse', minWidth: 620 }}>
            <caption className="sr-only">Authorization hunts and their confirmed leak counts</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--c-border)' }}>
                <th scope="col" style={styles.th}>Base URL</th>
                <th scope="col" style={styles.th}>Status</th>
                <th scope="col" style={styles.th}>Probes run</th>
                <th scope="col" style={styles.th}>Confirmed leaks</th>
                <th scope="col" style={styles.th}><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={5} style={styles.tdEmpty}>Loading authorization hunts…</td></tr>}
              {!loading && authzHunts.length === 0 && (
                <tr><td colSpan={5} style={styles.tdEmpty}>No hunts yet. Run one above to prove or rule out IDOR/BOLA.</td></tr>
              )}
              {authzHunts.map((h: any) => (
                <tr key={h.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                  <td className="responsive-primary" style={{ ...styles.td, overflowWrap: 'anywhere' }}>{h.base_url}</td>
                  <td data-label="Status" style={styles.td}><Badge tone={h.status === 'completed' ? 'success' : 'warning'}>{h.status}</Badge></td>
                  <td data-label="Probes run" style={styles.td}>{h.probes_run}</td>
                  <td data-label="Confirmed leaks" style={styles.td}>
                    {h.confirmed_leaks > 0 ? <Badge tone="danger">{h.confirmed_leaks}</Badge> : <Badge tone="success">0</Badge>}
                  </td>
                  <td className="responsive-actions" style={{ ...styles.td, textAlign: 'right' }}>
                    <button type="button" onClick={() => openFindings(h)} style={styles.buttonGhostLight}>
                      View findings
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedHuntId && (
        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Findings</h3>
          {findingsLoading && <p style={styles.mutedText} role="status">Loading findings…</p>}
          {!findingsLoading && huntFindings.length === 0 && <p style={styles.mutedText}>No findings on this hunt.</p>}
          {huntFindings.map((f: any) => (
            <div key={f.id} style={{ ...styles.auditRowLight, flexDirection: 'column', alignItems: 'stretch' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                <div>
                  <strong>{f.method} {f.path}</strong>
                  <br />
                  <span style={styles.mutedText}>
                    {f.owner_role} → {f.tested_role} · confidence {Math.round((f.confidence || 0) * 100)}%
                  </span>
                </div>
                <Badge tone={verdictTone(f.verdict)}>{verdictLabel(f.verdict)}</Badge>
              </div>
              {f.reason && <p style={{ ...styles.mutedText, marginTop: '0.4rem' }}>{f.reason}</p>}
              {f.narrative && (
                <p style={{ marginTop: '0.4rem', fontSize: '0.85rem' }}>
                  <strong>Exploit narrative: </strong>{f.narrative}
                </p>
              )}
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => setExpandedEvidence((prev) => ({ ...prev, [f.id]: !prev[f.id] }))}
                  style={styles.buttonGhostLight}
                >
                  {expandedEvidence[f.id] ? 'Hide evidence' : 'View evidence'}
                </button>
                {canManage && f.verdict === 'confirmed_leak' && (
                  f.reviewed_at
                    ? <Badge tone="success">Reviewed</Badge>
                    : <button type="button" onClick={() => reviewFinding(f.id)} style={styles.buttonGhostLight}>
                        Mark reviewed
                      </button>
                )}
              </div>
              {expandedEvidence[f.id] && f.evidence && (
                <pre style={styles.codeBlock}>{JSON.stringify(f.evidence, null, 2)}</pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================================
// PR REVIEWS (whitebox: risk-ranked GitHub pull-request review)
// ============================================================
function PRReviewsSection({ ctx }: { ctx: any }) {
  const { api, token, notify, prReviews, setPrReviews, canManage } = ctx
  const [clientsForPr, setClientsForPr] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ client_id: '' as any, repo: '', pr_number: '', github_token: '', post_comment: false, provider: 'github', host: '' })
  const [selectedReviewId, setSelectedReviewId] = useState<any>(null)
  const [reviewFindings, setReviewFindings] = useState<any[]>([])
  const [findingsLoading, setFindingsLoading] = useState(false)

  const load = async () => {
    try {
      const [reviewsData, clientsData] = await Promise.all([api('/pr-reviews'), api('/clients')])
      setPrReviews(Array.isArray(reviewsData) ? reviewsData : [])
      setClientsForPr(Array.isArray(clientsData) ? clientsData : [])
    } catch (e: any) {
      notify(e.message || 'Could not load PR reviews', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [token])

  const openFindings = async (review: any) => {
    setSelectedReviewId(review.id)
    setReviewFindings([])
    setFindingsLoading(true)
    try {
      const data = await api(`/pr-reviews/${review.id}/findings`)
      setReviewFindings(Array.isArray(data) ? data : [])
    } catch (e: any) {
      notify(e.message || 'Could not load findings', 'error')
    } finally {
      setFindingsLoading(false)
    }
  }

  const createReview = async (e: any) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api('/pr-reviews', {
        method: 'POST',
        body: JSON.stringify({
          client_id: parseInt(form.client_id),
          repo: form.repo.trim(),
          pr_number: parseInt(form.pr_number),
          github_token: form.github_token.trim(),
          post_comment: form.post_comment,
          provider: form.provider,
          host: form.provider === 'forgejo' ? form.host.trim() : undefined,
        }),
      })
      setForm({ client_id: form.client_id, repo: '', pr_number: '', github_token: '', post_comment: false, provider: form.provider, host: '' })
      notify('PR review completed', 'success')
      load()
    } catch (e: any) {
      notify(e.message || 'Could not review that pull request', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const canSubmit = Boolean(
    form.client_id &&
    form.repo.trim() &&
    form.pr_number &&
    form.github_token.trim() &&
    (form.provider !== 'forgejo' || form.host.trim())
  )

  return (
    <div style={styles.section}>
      <h1 style={styles.pageTitle}>PR Reviews</h1>
      <p style={styles.hint}>
        Whitebox review for a single pull request: fetches its diff, flags risky patterns
        introduced by the added lines (hardcoded secrets, insecure defaults, dangerous calls),
        ranks them by severity, and can post a findings comment on the PR itself. The access
        token you provide is used once, in memory, to make the GitHub API calls -- it is never
        stored.
      </p>

      {canManage && (
        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Review a Pull Request</h3>
          <form onSubmit={createReview}>
            <Field label="Client" htmlFor="pr-client" required>
              <Select value={form.client_id} onChange={(e) => setForm({ ...form, client_id: e.target.value })}>
                <option value="">Select a client</option>
                {clientsForPr.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Field>
            <Field label="Provider" htmlFor="pr-provider" required>
              <Select value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}>
                <option value="github">GitHub</option>
                <option value="bitbucket">Bitbucket Cloud</option>
                <option value="forgejo">Forgejo / Gitea (self-hosted)</option>
              </Select>
            </Field>
            {form.provider === 'forgejo' && (
              <Field label="Forgejo host" htmlFor="pr-host" required hint="e.g. https://forgejo.example.sn">
                <TextInput
                  value={form.host}
                  onChange={(e) => setForm({ ...form, host: e.target.value })}
                  placeholder="https://forgejo.example.sn"
                />
              </Field>
            )}
            <Field label="Repository" htmlFor="pr-repo" required hint="owner/name (workspace/repo_slug for Bitbucket), e.g. utachicodes/ultron">
              <TextInput
                value={form.repo}
                onChange={(e) => setForm({ ...form, repo: e.target.value })}
                placeholder="owner/name"
              />
            </Field>
            <Field label="Pull request number" htmlFor="pr-number" required>
              <TextInput
                type="number"
                min={1}
                value={form.pr_number}
                onChange={(e) => setForm({ ...form, pr_number: e.target.value })}
              />
            </Field>
            <Field label="Access token" htmlFor="pr-token" required hint="A token with read access to this repo (and comment access if posting). Used once, never stored.">
              <TextInput
                type="password"
                value={form.github_token}
                onChange={(e) => setForm({ ...form, github_token: e.target.value })}
                placeholder="ghp_... / Bitbucket app password / Forgejo token"
              />
            </Field>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={form.post_comment}
                onChange={(e) => setForm({ ...form, post_comment: e.target.checked })}
              />
              Post the findings as a comment on the PR
            </label>
            <div style={{ marginTop: '1rem' }}>
              <Button type="submit" loading={submitting} disabled={!canSubmit}>Run review</Button>
            </div>
          </form>
        </div>
      )}

      <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
        <h3 style={styles.h3}>Reviews</h3>
        <div style={styles.tableWrap}>
          <table className="responsive-table" style={{ width: '100%', borderCollapse: 'collapse', minWidth: 620 }}>
            <caption className="sr-only">PR reviews and their findings</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--c-border)' }}>
                <th scope="col" style={styles.th}>Repo / PR</th>
                <th scope="col" style={styles.th}>Status</th>
                <th scope="col" style={styles.th}>Findings</th>
                <th scope="col" style={styles.th}>Comment</th>
                <th scope="col" style={styles.th}><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={5} style={styles.tdEmpty}>Loading PR reviews…</td></tr>}
              {!loading && prReviews.length === 0 && (
                <tr><td colSpan={5} style={styles.tdEmpty}>No PR reviews yet. Review one above.</td></tr>
              )}
              {prReviews.map((r: any) => (
                <tr key={r.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                  <td className="responsive-primary" style={{ ...styles.td, overflowWrap: 'anywhere' }}>
                    <Badge tone="neutral">{r.provider}</Badge> {r.repo}#{r.pr_number}
                    {r.pr_title && <><br /><span style={styles.mutedText}>{r.pr_title}</span></>}
                  </td>
                  <td data-label="Status" style={styles.td}>
                    <Badge tone={r.status === 'completed' ? 'success' : r.status === 'failed' ? 'danger' : 'warning'}>{r.status}</Badge>
                  </td>
                  <td data-label="Findings" style={styles.td}>
                    {r.findings_count > 0 ? <Badge tone="warning">{r.findings_count}</Badge> : <Badge tone="success">0</Badge>}
                  </td>
                  <td data-label="Comment" style={styles.td}>
                    <Badge tone={r.comment_posted ? 'success' : 'neutral'}>{r.comment_posted ? 'Posted' : 'Not posted'}</Badge>
                  </td>
                  <td className="responsive-actions" style={{ ...styles.td, textAlign: 'right' }}>
                    <button type="button" onClick={() => openFindings(r)} style={styles.buttonGhostLight}>
                      View findings
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedReviewId && (
        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Findings</h3>
          {findingsLoading && <p style={styles.mutedText} role="status">Loading findings…</p>}
          {!findingsLoading && reviewFindings.length === 0 && <p style={styles.mutedText}>No risky patterns found in the added lines of this PR.</p>}
          {reviewFindings.map((f: any) => (
            <div key={f.id} style={styles.auditRowLight}>
              <div style={{ flex: 1 }}>
                <strong>{f.file_path}</strong>:{f.line_number}
                <br />
                <span style={styles.mutedText}>{f.summary}</span>
                {f.suggested_fix && (
                  <>
                    <br />
                    <span style={styles.mutedText}>Fix: {f.suggested_fix}</span>
                  </>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <Badge tone={severityTone(f.severity || 'medium')}>{f.severity}</Badge>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================================
// CAMPAIGNS (commander-orchestrated multi-task runs)
// ============================================================
function emptyCampaignAuthzTask() {
  return {
    base_url: '',
    roles: [emptyRole(), emptyRole()],
    probes: [emptyProbe()],
  }
}

function emptyCampaignPrTask() {
  return { repo: '', pr_number: '', github_token: '', post_comment: false }
}

function CampaignsSection({ ctx }: { ctx: any }) {
  const { api, token, notify, campaigns, setCampaigns, canManage } = ctx
  const [clientsForCampaign, setClientsForCampaign] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [goal, setGoal] = useState('')
  const [clientId, setClientId] = useState('')
  const [authzTasks, setAuthzTasks] = useState<any[]>([])
  const [prTasks, setPrTasks] = useState<any[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState<any>(null)
  const [campaignFacts, setCampaignFacts] = useState<any[]>([])
  const [factsLoading, setFactsLoading] = useState(false)

  const load = async () => {
    try {
      const [campaignsData, clientsData] = await Promise.all([api('/campaigns'), api('/clients')])
      setCampaigns(Array.isArray(campaignsData) ? campaignsData : [])
      setClientsForCampaign(Array.isArray(clientsData) ? clientsData : [])
    } catch (e: any) {
      notify(e.message || 'Could not load campaigns', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [token])

  const openFacts = async (campaign: any) => {
    setSelectedCampaignId(campaign.id)
    setCampaignFacts([])
    setFactsLoading(true)
    try {
      const data = await api(`/campaigns/${campaign.id}/facts`)
      setCampaignFacts(Array.isArray(data) ? data : [])
    } catch (e: any) {
      notify(e.message || 'Could not load the fact log', 'error')
    } finally {
      setFactsLoading(false)
    }
  }

  const updateAuthzTask = (i: number, patch: any) =>
    setAuthzTasks((prev) => prev.map((t, idx) => (idx === i ? { ...t, ...patch } : t)))
  const updateAuthzTaskRole = (taskIdx: number, roleIdx: number, patch: any) =>
    setAuthzTasks((prev) =>
      prev.map((t, idx) =>
        idx === taskIdx
          ? { ...t, roles: t.roles.map((r: any, ri: number) => (ri === roleIdx ? { ...r, ...patch } : r)) }
          : t
      )
    )
  const updateAuthzTaskProbe = (taskIdx: number, probeIdx: number, patch: any) =>
    setAuthzTasks((prev) =>
      prev.map((t, idx) =>
        idx === taskIdx
          ? { ...t, probes: t.probes.map((p: any, pi: number) => (pi === probeIdx ? { ...p, ...patch } : p)) }
          : t
      )
    )
  const updatePrTask = (i: number, patch: any) =>
    setPrTasks((prev) => prev.map((t, idx) => (idx === i ? { ...t, ...patch } : t)))

  const createCampaign = async (e: any) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const payload = {
        client_id: parseInt(clientId),
        goal: goal.trim(),
        authz_hunts: authzTasks.map((t) => ({
          base_url: t.base_url.trim(),
          roles: t.roles
            .filter((r: any) => r.name.trim())
            .map((r: any) => ({
              name: r.name.trim(),
              headers: r.header_value.trim() ? { [r.header_name]: r.header_value.trim() } : {},
            })),
          probes: t.probes
            .filter((p: any) => p.path.trim() && p.owner_role.trim() && p.owner_value.trim())
            .map((p: any) => ({
              method: p.method,
              path: p.path.trim(),
              id_param: p.id_param.trim() || 'id',
              owner_role: p.owner_role.trim(),
              owner_value: p.owner_value.trim(),
            })),
        })),
        pr_reviews: prTasks
          .filter((t) => t.repo.trim() && t.pr_number && t.github_token.trim())
          .map((t) => ({
            repo: t.repo.trim(),
            pr_number: parseInt(t.pr_number),
            github_token: t.github_token.trim(),
            post_comment: t.post_comment,
          })),
      }
      if (payload.authz_hunts.length === 0 && payload.pr_reviews.length === 0) {
        notify('Add at least one authorization-hunt or PR-review task', 'error')
        setSubmitting(false)
        return
      }
      await api('/campaigns', { method: 'POST', body: JSON.stringify(payload) })
      setGoal('')
      setAuthzTasks([])
      setPrTasks([])
      notify('Campaign completed', 'success')
      load()
    } catch (e: any) {
      notify(e.message || 'Could not run the campaign', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const canSubmit = Boolean(clientId && goal.trim() && (authzTasks.length > 0 || prTasks.length > 0))

  return (
    <div style={styles.section}>
      <h1 style={styles.pageTitle}>Campaigns</h1>
      <p style={styles.hint}>
        Commander-orchestrated runs: give it a goal and a set of authorization-hunt and/or
        PR-review tasks, and it dispatches them (in parallel), consolidating confirmed findings
        into a layered fact log. Architecturally inspired by sapper-v2's commander/worker role
        division — every task still only ever calls Ultron's own proof engines, with the same
        scope limits and human-review gates.
      </p>

      {canManage && (
        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Run a Campaign</h3>
          <form onSubmit={createCampaign}>
            <Field label="Client" htmlFor="campaign-client" required>
              <Select value={clientId} onChange={(e) => setClientId(e.target.value)}>
                <option value="">Select a client</option>
                {clientsForCampaign.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Field>
            <Field label="Goal" htmlFor="campaign-goal" required hint="What this campaign is assessing, in plain language">
              <TextInput value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Assess the new customer portal before launch" />
            </Field>

            <h4 style={styles.h4}>Authorization-Hunt Tasks</h4>
            {authzTasks.map((t, ti) => (
              <div key={ti} style={{ border: `1px solid ${BORDER}`, padding: '0.9rem', marginBottom: '0.75rem' }}>
                <div style={styles.formRow}>
                  <TextInput
                    value={t.base_url}
                    onChange={(e) => updateAuthzTask(ti, { base_url: e.target.value })}
                    placeholder="Base URL, e.g. https://api.example.sn"
                    aria-label={`Task ${ti + 1} base URL`}
                    style={{ flex: 1 }}
                  />
                  <button type="button" onClick={() => setAuthzTasks((prev) => prev.filter((_, idx) => idx !== ti))} style={styles.buttonGhostLight}>
                    Remove task
                  </button>
                </div>
                {t.roles.map((r: any, ri: number) => (
                  <div key={ri} style={styles.formRow}>
                    <TextInput value={r.name} onChange={(e) => updateAuthzTaskRole(ti, ri, { name: e.target.value })} placeholder="Role name" aria-label={`Task ${ti + 1} role ${ri + 1} name`} />
                    <Select value={r.header_name} onChange={(e) => updateAuthzTaskRole(ti, ri, { header_name: e.target.value })} aria-label={`Task ${ti + 1} role ${ri + 1} header name`}>
                      {HEADER_NAME_OPTIONS.map((h) => <option key={h} value={h}>{h}</option>)}
                    </Select>
                    <TextInput value={r.header_value} onChange={(e) => updateAuthzTaskRole(ti, ri, { header_value: e.target.value })} placeholder="Header value" aria-label={`Task ${ti + 1} role ${ri + 1} header value`} />
                  </div>
                ))}
                {t.probes.map((p: any, pi: number) => (
                  <div key={pi} style={{ ...styles.formRow, flexWrap: 'wrap' }}>
                    <TextInput value={p.path} onChange={(e) => updateAuthzTaskProbe(ti, pi, { path: e.target.value })} placeholder="/api/invoices/{id}" aria-label={`Task ${ti + 1} probe ${pi + 1} path`} style={{ minWidth: 180 }} />
                    <TextInput value={p.id_param} onChange={(e) => updateAuthzTaskProbe(ti, pi, { id_param: e.target.value })} placeholder="id" aria-label={`Task ${ti + 1} probe ${pi + 1} id param`} style={{ maxWidth: 90 }} />
                    <Select value={p.owner_role} onChange={(e) => updateAuthzTaskProbe(ti, pi, { owner_role: e.target.value })} aria-label={`Task ${ti + 1} probe ${pi + 1} owner role`}>
                      <option value="">Owner role</option>
                      {t.roles.filter((r: any) => r.name.trim()).map((r: any) => <option key={r.name} value={r.name}>{r.name}</option>)}
                    </Select>
                    <TextInput value={p.owner_value} onChange={(e) => updateAuthzTaskProbe(ti, pi, { owner_value: e.target.value })} placeholder="owner's object id" aria-label={`Task ${ti + 1} probe ${pi + 1} owner value`} style={{ maxWidth: 160 }} />
                  </div>
                ))}
              </div>
            ))}
            <button type="button" onClick={() => setAuthzTasks((prev) => [...prev, emptyCampaignAuthzTask()])} style={styles.buttonGhostLight}>
              + Add authorization-hunt task
            </button>

            <h4 style={{ ...styles.h4, marginTop: '1.25rem' }}>PR-Review Tasks</h4>
            {prTasks.map((t, ti) => (
              <div key={ti} style={{ ...styles.formRow, flexWrap: 'wrap' }}>
                <TextInput value={t.repo} onChange={(e) => updatePrTask(ti, { repo: e.target.value })} placeholder="owner/name" aria-label={`PR task ${ti + 1} repo`} />
                <TextInput type="number" min={1} value={t.pr_number} onChange={(e) => updatePrTask(ti, { pr_number: e.target.value })} placeholder="PR #" aria-label={`PR task ${ti + 1} number`} style={{ maxWidth: 100 }} />
                <TextInput type="password" value={t.github_token} onChange={(e) => updatePrTask(ti, { github_token: e.target.value })} placeholder="GitHub token" aria-label={`PR task ${ti + 1} token`} />
                <button type="button" onClick={() => setPrTasks((prev) => prev.filter((_, idx) => idx !== ti))} style={styles.buttonGhostLight}>
                  Remove
                </button>
              </div>
            ))}
            <button type="button" onClick={() => setPrTasks((prev) => [...prev, emptyCampaignPrTask()])} style={styles.buttonGhostLight}>
              + Add PR-review task
            </button>

            <div style={{ marginTop: '1.25rem' }}>
              <Button type="submit" loading={submitting} disabled={!canSubmit}>Run campaign</Button>
            </div>
          </form>
        </div>
      )}

      <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
        <h3 style={styles.h3}>Campaigns</h3>
        <div style={styles.tableWrap}>
          <table className="responsive-table" style={{ width: '100%', borderCollapse: 'collapse', minWidth: 620 }}>
            <caption className="sr-only">Campaigns and their task progress</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--c-border)' }}>
                <th scope="col" style={styles.th}>Goal</th>
                <th scope="col" style={styles.th}>Status</th>
                <th scope="col" style={styles.th}>Tasks</th>
                <th scope="col" style={styles.th}><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={4} style={styles.tdEmpty}>Loading campaigns…</td></tr>}
              {!loading && campaigns.length === 0 && (
                <tr><td colSpan={4} style={styles.tdEmpty}>No campaigns yet. Run one above.</td></tr>
              )}
              {campaigns.map((c: any) => (
                <tr key={c.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                  <td className="responsive-primary" style={{ ...styles.td, overflowWrap: 'anywhere' }}>{c.goal}</td>
                  <td data-label="Status" style={styles.td}><Badge tone={c.status === 'completed' ? 'success' : 'warning'}>{c.status}</Badge></td>
                  <td data-label="Tasks" style={styles.td}>{c.tasks_completed}/{c.tasks_total}</td>
                  <td className="responsive-actions" style={{ ...styles.td, textAlign: 'right' }}>
                    <button type="button" onClick={() => openFacts(c)} style={styles.buttonGhostLight}>View facts</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedCampaignId && (
        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Fact Log</h3>
          {(() => {
            const campaign = campaigns.find((c: any) => c.id === selectedCampaignId)
            return campaign?.summary ? <p style={{ ...styles.mutedText, marginBottom: '1rem' }}>{campaign.summary}</p> : null
          })()}
          {factsLoading && <p style={styles.mutedText} role="status">Loading facts…</p>}
          {!factsLoading && campaignFacts.length === 0 && <p style={styles.mutedText}>No significant findings in this campaign.</p>}
          {campaignFacts.map((f: any) => (
            <div key={f.id} style={styles.auditRowLight}>
              <div style={{ flex: 1 }}>
                <strong>{f.title}</strong>
                <br />
                <span style={styles.mutedText}>{f.summary}</span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <Badge tone={severityTone(f.severity)}>{f.severity}</Badge>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================================
// AI RED-TEAM (attack + defend AI Guard)
// ============================================================
function AIRedTeamSection({ ctx }: { ctx: any }) {
  const { api, token, notify, redteamRuns, setRedteamRuns, canManage } = ctx
  const [clientsForRedteam, setClientsForRedteam] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [clientId, setClientId] = useState('')
  const [mode, setMode] = useState('internal')
  const [externalUrl, setExternalUrl] = useState('')
  const [headerName, setHeaderName] = useState('Authorization')
  const [headerValue, setHeaderValue] = useState('')
  const [promptField, setPromptField] = useState('prompt')
  const [responseField, setResponseField] = useState('response')
  const [selectedRunId, setSelectedRunId] = useState<any>(null)
  const [runResults, setRunResults] = useState<any[]>([])
  const [resultsLoading, setResultsLoading] = useState(false)
  const [patterns, setPatterns] = useState<any[]>([])

  const load = async () => {
    try {
      const [runsData, clientsData] = await Promise.all([api('/ai-redteam/runs'), api('/clients')])
      setRedteamRuns(Array.isArray(runsData) ? runsData : [])
      setClientsForRedteam(Array.isArray(clientsData) ? clientsData : [])
    } catch (e: any) {
      notify(e.message || 'Could not load red-team runs', 'error')
    } finally {
      setLoading(false)
    }
  }

  const loadPatterns = async () => {
    try {
      const data = await api('/jailbreak-patterns')
      setPatterns(Array.isArray(data) ? data : [])
    } catch (e: any) {
      notify(e.message || 'Could not load jailbreak patterns', 'error')
    }
  }

  useEffect(() => { load(); loadPatterns() }, [token])

  const openResults = async (run: any) => {
    setSelectedRunId(run.id)
    setRunResults([])
    setResultsLoading(true)
    try {
      const data = await api(`/ai-redteam/runs/${run.id}/results`)
      setRunResults(Array.isArray(data) ? data : [])
    } catch (e: any) {
      notify(e.message || 'Could not load results', 'error')
    } finally {
      setResultsLoading(false)
    }
  }

  const runAttack = async (e: any) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const payload: any = { client_id: parseInt(clientId), mode }
      if (mode === 'external') {
        payload.external = {
          url: externalUrl.trim(),
          headers: headerValue.trim() ? { [headerName]: headerValue.trim() } : {},
          prompt_field: promptField.trim() || 'prompt',
          response_field: responseField.trim() || 'response',
        }
      }
      await api('/ai-redteam/runs', { method: 'POST', body: JSON.stringify(payload) })
      notify('Red-team run completed', 'success')
      load()
      loadPatterns()
    } catch (e: any) {
      notify(e.message || 'Could not run the attack', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const canSubmit = Boolean(clientId && (mode === 'internal' || externalUrl.trim()))

  return (
    <div style={styles.section}>
      <h1 style={styles.pageTitle}>AI Red-Team</h1>
      <p style={styles.hint}>
        Fires known prompt-injection/jailbreak patterns at a declared AI target — Ultron's own AI
        Guard, or a client's own AI-powered feature — using canary tokens for deterministic
        grading. Every confirmed bypass is turned into a defense pattern checked on every future
        AI Guard query, closing the loop without touching source code.
      </p>

      {canManage && (
        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Run an Attack</h3>
          <form onSubmit={runAttack}>
            <Field label="Client" htmlFor="redteam-client" required>
              <Select value={clientId} onChange={(e) => setClientId(e.target.value)}>
                <option value="">Select a client</option>
                {clientsForRedteam.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Field>
            <Field label="Target" htmlFor="redteam-mode" required>
              <Select value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="internal">Ultron's own AI Guard</option>
                <option value="external">A client's AI-powered feature (HTTP)</option>
              </Select>
            </Field>
            {mode === 'external' && (
              <>
                <Field label="Endpoint URL" htmlFor="redteam-url" required>
                  <TextInput value={externalUrl} onChange={(e) => setExternalUrl(e.target.value)} placeholder="https://client-app.example.sn/ai/chat" />
                </Field>
                <div style={styles.formRow}>
                  <Select value={headerName} onChange={(e) => setHeaderName(e.target.value)}>
                    {HEADER_NAME_OPTIONS.map((h) => <option key={h} value={h}>{h}</option>)}
                  </Select>
                  <TextInput value={headerValue} onChange={(e) => setHeaderValue(e.target.value)} placeholder="Header value (optional)" />
                </div>
                <div style={styles.formRow}>
                  <TextInput value={promptField} onChange={(e) => setPromptField(e.target.value)} placeholder="Request JSON field for the prompt" />
                  <TextInput value={responseField} onChange={(e) => setResponseField(e.target.value)} placeholder="Response JSON field to read back" />
                </div>
              </>
            )}
            <div style={{ marginTop: '1rem' }}>
              <Button type="submit" loading={submitting} disabled={!canSubmit}>Run attack</Button>
            </div>
          </form>
        </div>
      )}

      <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
        <h3 style={styles.h3}>Runs</h3>
        <div style={styles.tableWrap}>
          <table className="responsive-table" style={{ width: '100%', borderCollapse: 'collapse', minWidth: 620 }}>
            <caption className="sr-only">AI red-team runs and their bypass counts</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--c-border)' }}>
                <th scope="col" style={styles.th}>Target</th>
                <th scope="col" style={styles.th}>Status</th>
                <th scope="col" style={styles.th}>Bypassed</th>
                <th scope="col" style={styles.th}>Patterns Learned</th>
                <th scope="col" style={styles.th}><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={5} style={styles.tdEmpty}>Loading runs…</td></tr>}
              {!loading && redteamRuns.length === 0 && (
                <tr><td colSpan={5} style={styles.tdEmpty}>No runs yet. Run an attack above.</td></tr>
              )}
              {redteamRuns.map((r: any) => (
                <tr key={r.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                  <td className="responsive-primary" style={{ ...styles.td, overflowWrap: 'anywhere' }}>{r.target_summary}</td>
                  <td data-label="Status" style={styles.td}><Badge tone={r.status === 'completed' ? 'success' : 'warning'}>{r.status}</Badge></td>
                  <td data-label="Bypassed" style={styles.td}>
                    {r.bypassed_count > 0 ? <Badge tone="danger">{r.bypassed_count}/{r.payloads_run}</Badge> : <Badge tone="success">0/{r.payloads_run}</Badge>}
                  </td>
                  <td data-label="Patterns Learned" style={styles.td}>{r.patterns_learned}</td>
                  <td className="responsive-actions" style={{ ...styles.td, textAlign: 'right' }}>
                    <button type="button" onClick={() => openResults(r)} style={styles.buttonGhostLight}>View results</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedRunId && (
        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Results</h3>
          {resultsLoading && <p style={styles.mutedText} role="status">Loading results…</p>}
          {runResults.map((r: any) => (
            <div key={r.id} style={styles.auditRowLight}>
              <div style={{ flex: 1 }}>
                <strong>{r.category}</strong>
                {r.pattern_learned && <span style={styles.mutedText}> — new defense pattern learned</span>}
              </div>
              <div style={{ textAlign: 'right' }}>
                <Badge tone={r.verdict === 'bypassed' ? 'danger' : r.verdict === 'error' ? 'warning' : 'success'}>{r.verdict}</Badge>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
        <h3 style={styles.h3}>Active Defense Patterns</h3>
        {patterns.length === 0 && <p style={styles.mutedText}>No learned patterns yet — the 5 well-known categories are pre-armed by default.</p>}
        {patterns.map((p: any) => (
          <div key={p.id} style={styles.auditRowLight}>
            <div style={{ flex: 1 }}>
              <strong>{p.category}</strong>
              <br />
              <span style={styles.mutedText}>{p.pattern}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================================
// COMPLIANCE
// ============================================================
function ComplianceSection({ ctx }: { ctx: any }) {
  const { api, token, notify, clients, setClients, canManage } = ctx
    const [loading, setLoading] = useState(true)
    const [selectedClientId, setSelectedClientId] = useState('')
    const [clientFindings, setClientFindings] = useState<any[]>([])
    const [sectorOverride, setSectorOverride] = useState('')
    const [summary, setSummary] = useState<any>(null)
    const [mappings, setMappings] = useState<any[]>([])
    const [working, setWorking] = useState(false)
    const [soc2Readiness, setSoc2Readiness] = useState<any>(null)
    const [soc2ReportType, setSoc2ReportType] = useState('type2')
    const [soc2Working, setSoc2Working] = useState(false)
    const [isoReadiness, setIsoReadiness] = useState<any>(null)
    const [isoWorking, setIsoWorking] = useState(false)

    useEffect(() => {
      api('/clients')
        .then((data: any) => setClients(Array.isArray(data) ? data : []))
        .catch((e: any) => notify(e.message || 'Could not load clients', 'error'))
        .finally(() => setLoading(false))
    }, [token])

    // Start on the first available client: a client portal has exactly one,
    // and an operator should land on real obligations rather than an empty
    // "Select a client" state. The sector and findings then follow.
    useEffect(() => {
      if (!selectedClientId && clients.length > 0) {
        setSelectedClientId(String(clients[0].id))
      }
    }, [clients, selectedClientId])

    const selectedClient = clients.find((c: any) => String(c.id) === selectedClientId)
    const effectiveSector = sectorOverride || selectedClient?.sector || 'other'

    useEffect(() => {
      setSummary(null)
      setMappings([])
      setSoc2Readiness(null)
      setIsoReadiness(null)
      setSectorOverride('')
      if (!selectedClientId) {
        setClientFindings([])
        return
      }
      api(`/scans?limit=500`)
        .then((scans: any) => {
          const findings = (Array.isArray(scans) ? scans : [])
            .filter((s: any) => String(s.client_id) === selectedClientId)
            .flatMap((s: any) => s.findings || [])
          setClientFindings(findings)
        })
        .catch((e: any) => notify(e.message || 'Could not load findings for this client', 'error'))
    }, [selectedClientId])

    const counts = {
      total: clientFindings.length,
      critical: clientFindings.filter((f: any) => f.severity === 'critical').length,
      high: clientFindings.filter((f: any) => f.severity === 'high').length,
      medium: clientFindings.filter((f: any) => f.severity === 'medium').length,
      low: clientFindings.filter((f: any) => f.severity === 'low').length,
    }

    const runSummary = async () => {
      setWorking(true)
      try {
        const params = new URLSearchParams({
          total_findings: String(counts.total),
          critical: String(counts.critical),
          high: String(counts.high),
          medium: String(counts.medium),
          client_sector: effectiveSector,
        })
        const res = await api(`/compliance/summary?${params.toString()}`)
        setSummary(res)
      } catch (e: any) {
        notify(e.message || 'Could not build the summary', 'error')
      } finally {
        setWorking(false)
      }
    }

    const runMap = async () => {
      setWorking(true)
      try {
        const findings = clientFindings.map((f: any) => ({ title: f.title, severity: f.severity, id: f.id }))
        const res = await api('/compliance/map', {
          method: 'POST',
          body: JSON.stringify({ findings, client_sector: effectiveSector }),
        })
        setMappings(res.mappings || [])
        notify('Compliance mapping generated', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not generate the mapping', 'error')
      } finally {
        setWorking(false)
      }
    }

    const runSoc2 = async () => {
      setSoc2Working(true)
      try {
        const findings = clientFindings.map((f: any) => ({ id: f.id, title: f.title, severity: f.severity }))
        const res = await api('/compliance/soc2', {
          method: 'POST',
          body: JSON.stringify({ findings, report_type: soc2ReportType }),
        })
        setSoc2Readiness(res)
      } catch (e: any) {
        notify(e.message || 'Could not build the SOC 2 readiness summary', 'error')
      } finally {
        setSoc2Working(false)
      }
    }

    const runIso27001 = async () => {
      setIsoWorking(true)
      try {
        const findings = clientFindings.map((f: any) => ({ id: f.id, title: f.title, severity: f.severity }))
        const res = await api('/compliance/iso27001', {
          method: 'POST',
          body: JSON.stringify({ findings }),
        })
        setIsoReadiness(res)
      } catch (e: any) {
        notify(e.message || 'Could not build the ISO 27001 readiness summary', 'error')
      } finally {
        setIsoWorking(false)
      }
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Compliance — Bill No. 25/2026</h1>
        <p style={styles.hint}>
          {canManage
            ? "Map a client's actual findings to the obligations set out in Bill No. 25/2026, passed by the National Assembly on 21 August 2026: National CERT, incident notification, vulnerability disclosure, local hosting, and AI governance. Draft mapping; not legal advice."
            : "Map your actual findings to the obligations set out in Bill No. 25/2026, passed by the National Assembly on 21 August 2026: National CERT, incident notification, vulnerability disclosure, local hosting, and AI governance. Draft mapping; not legal advice."}
        </p>

        <div style={styles.lightCard}>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 260px' }}>
              <Field label={canManage ? 'Client' : 'Organization'} htmlFor="compliance-client" hint={loading ? 'Loading clients…' : clients.length === 0 ? 'No clients available' : undefined}>
                <Select value={selectedClientId} onChange={(e) => setSelectedClientId(e.target.value)} disabled={loading || clients.length === 0}>
                  <option value="">Select a client</option>
                  {clients.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </Select>
              </Field>
            </div>
            <div style={{ flex: '1 1 260px' }}>
              <Field
                label="Sector"
                htmlFor="compliance-sector"
                hint={
                  !selectedClientId
                    ? 'Choose a client to prefill its sector'
                    : selectedClient?.sector
                      ? canManage
                        ? `From ${selectedClient.name}'s profile; override here if needed`
                        : 'From your organization profile; override here if needed'
                      : 'No sector set on this client — set one on the Clients page, or override here'
                }
              >
                <Select value={effectiveSector} onChange={(e) => setSectorOverride(e.target.value)} disabled={!selectedClientId}>
                  <option value="banking">Banking / Mobile Money</option>
                  <option value="telecom">Telecom</option>
                  <option value="government">Government</option>
                  <option value="sports">Sports (club / federation / academy)</option>
                  <option value="other">Other</option>
                </Select>
              </Field>
            </div>
          </div>
          {selectedClientId && (
            <p style={styles.mutedText}>
              {counts.total} finding{counts.total === 1 ? '' : 's'} across {canManage ? "this client's scans" : 'your scans'}
              {counts.total > 0 && ` — ${counts.critical} critical, ${counts.high} high, ${counts.medium} medium${counts.low ? `, ${counts.low} low` : ''}`}.
            </p>
          )}
        </div>

        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Compliance Summary</h3>
          <Button onClick={runSummary} loading={working} disabled={!selectedClientId}>Run summary</Button>
          {summary && (
            <div style={{ marginTop: '1rem', padding: '1rem', background: SURFACE_SUNKEN, borderRadius: 0 }}>
              <div className="responsive-stat-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                <div><div style={styles.statLabel}>Critical Findings</div><div style={styles.statValue}>{summary.critical}</div></div>
                <div><div style={styles.statLabel}>Reporting Required</div><div style={styles.statValue}>{summary.reporting_required ? 'Yes' : 'No'}</div></div>
                <div><div style={styles.statLabel}>Notification Window</div><div style={styles.statValue}>{summary.cert_notification_window_hours}h</div></div>
              </div>
              <p style={styles.mutedText}>{summary.framework}</p>
              <p style={styles.mutedText}>{summary.disclaimer || 'Draft mapping against Bill No. 25/2026 as passed on 21 August 2026. Confirm article references and the notification window against the published text before relying on it. Not a legal opinion.'}</p>
              <p style={styles.mutedText}>Sector: {sectorLabel(summary.client_sector)}</p>
              <div style={styles.detailLabelLight}>Next Steps</div>
              <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', paddingLeft: 0, color: TEXT_DIM }}>
                {summary.next_steps.map((s: string) => <li key={s}>{s}</li>)}
              </ul>
              {summary.sector_pack && (
                <div style={{ marginTop: '1rem' }}>
                  <div style={styles.detailLabelLight}>Sector Guidance: {summary.sector_pack.label}</div>
                  <p style={{ ...styles.mutedText, marginTop: '0.35rem' }}>{summary.sector_pack.summary}</p>
                  <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', paddingLeft: 0, color: TEXT_DIM }}>
                    {summary.sector_pack.focus_areas.map((f: any) => (
                      <li key={f.area}><strong>{f.area}</strong> — {f.why}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Findings → Bill Mapping</h3>
          <Button variant="secondary" onClick={runMap} loading={working} disabled={!selectedClientId || counts.total === 0}>
            Generate mappings
          </Button>
          {!selectedClientId && (
            <p style={{ ...styles.mutedText, marginTop: '0.75rem' }}>Select a client above to map their real findings.</p>
          )}
          {selectedClientId && counts.total === 0 && (
            <p style={{ ...styles.mutedText, marginTop: '0.75rem' }}>
              {canManage
                ? 'This client has no findings yet — run a scan first.'
                : 'No findings are available for your organization yet.'}
            </p>
          )}
          {mappings.length === 0 && selectedClientId && counts.total > 0 && (
            <p style={{ ...styles.mutedText, marginTop: '0.75rem' }}>
              No mapping generated yet.
            </p>
          )}
          {mappings.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              {mappings.map((m: any, i: number) => (
                <div key={`${m.law_article}-${m.finding_id ?? m.finding_title ?? i}`} style={styles.auditRowLight}>
                  <div style={{ flex: 1 }}>
                    <strong>{m.law_article}</strong>
                    <br />
                    <span style={styles.mutedText}>{m.obligation}</span>
                    {m.sector_action && (
                      <>
                        <br />
                        <span style={styles.mutedText}><strong>Sector action:</strong> {m.sector_action}</span>
                      </>
                    )}
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <Badge tone={m.priority === 'immediate' ? 'danger' : m.priority === 'urgent' ? 'warning' : 'neutral'}>{m.priority}</Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>SOC 2 Readiness (AICPA Trust Services Criteria)</h3>
          <p style={styles.hint}>
            A readiness signal built from the same findings, mapped to SOC 2 control categories —
            not an audit or attestation. Only a licensed CPA firm can issue a SOC 2 report.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div style={{ flex: '0 0 220px' }}>
              <Field label="Target report type" htmlFor="soc2-report-type">
                <Select value={soc2ReportType} onChange={(e) => setSoc2ReportType(e.target.value)}>
                  <option value="type2">Type II (operating effectiveness)</option>
                  <option value="type1">Type I (point in time)</option>
                </Select>
              </Field>
            </div>
            <Button variant="secondary" onClick={runSoc2} loading={soc2Working} disabled={!selectedClientId}>
              Run readiness check
            </Button>
          </div>
          {!selectedClientId && (
            <p style={{ ...styles.mutedText, marginTop: '0.5rem' }}>Select a client above first.</p>
          )}
          {soc2Readiness && (
            <div style={{ marginTop: '1rem' }}>
              <div className="responsive-stat-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                <div><div style={styles.statLabel}>Readiness</div><div style={styles.statValue}>{soc2Readiness.readiness_percent}%</div></div>
                <div><div style={styles.statLabel}>Open Control Gaps</div><div style={styles.statValue}>{soc2Readiness.gap_count}</div></div>
                <div><div style={styles.statLabel}>Critical Gaps</div><div style={styles.statValue}>{soc2Readiness.critical_gap_count}</div></div>
                <div><div style={styles.statLabel}>Not Assessable</div><div style={styles.statValue}>{soc2Readiness.not_assessed_count}</div></div>
              </div>
              <p style={styles.mutedText}>{soc2Readiness.disclaimer}</p>
              <div style={{ marginTop: '0.75rem' }}>
                {soc2Readiness.controls.map((c: any) => (
                  <div key={c.control} style={styles.auditRowLight}>
                    <div style={{ flex: 1 }}>
                      <strong>{c.label}</strong>
                      <br />
                      <span style={styles.mutedText}>{c.description}</span>
                      {c.open_items.length > 0 && (
                        <ul style={{ marginLeft: '1.1rem', marginTop: '0.4rem', paddingLeft: 0, color: TEXT_DIM, fontSize: '0.82rem' }}>
                          {c.open_items.map((item: any, idx: number) => (
                            <li key={item.finding_id ?? idx}>
                              <Badge tone={severityTone(item.severity)}>{item.severity}</Badge> {item.title}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <Badge tone={c.status === 'gap' ? 'warning' : c.status === 'not_assessed' ? 'neutral' : 'success'}>
                        {c.status === 'gap' ? 'Gap' : c.status === 'not_assessed' ? 'Not assessed' : 'No gaps found'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
              <div style={styles.detailLabelLight}>Next Steps</div>
              <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', paddingLeft: 0, color: TEXT_DIM }}>
                {soc2Readiness.next_steps.map((s: string) => <li key={s}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>

        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>ISO/IEC 27001:2022 Readiness (Annex A)</h3>
          <p style={styles.hint}>
            A readiness signal mapped to ISO 27001 Annex A control themes — not a certification
            or Statement of Applicability. Physical and most people controls can't be assessed
            by scanning and are reported as such, not scored as passing.
          </p>
          <Button variant="secondary" onClick={runIso27001} loading={isoWorking} disabled={!selectedClientId}>
            Run readiness check
          </Button>
          {!selectedClientId && (
            <p style={{ ...styles.mutedText, marginTop: '0.5rem' }}>Select a client above first.</p>
          )}
          {isoReadiness && (
            <div style={{ marginTop: '1rem' }}>
              <div className="responsive-stat-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                <div><div style={styles.statLabel}>Readiness</div><div style={styles.statValue}>{isoReadiness.readiness_percent}%</div></div>
                <div><div style={styles.statLabel}>Open Control Gaps</div><div style={styles.statValue}>{isoReadiness.gap_count}</div></div>
                <div><div style={styles.statLabel}>Not Assessable</div><div style={styles.statValue}>{isoReadiness.not_assessed_count}</div></div>
              </div>
              <p style={styles.mutedText}>{isoReadiness.disclaimer}</p>
              <div style={{ marginTop: '0.75rem' }}>
                {isoReadiness.controls.map((c: any) => (
                  <div key={c.control} style={styles.auditRowLight}>
                    <div style={{ flex: 1 }}>
                      <strong>{c.label}</strong> <span style={styles.mutedText}>({c.annex_controls.join(', ')})</span>
                      <br />
                      <span style={styles.mutedText}>{c.description}</span>
                      {c.open_items.length > 0 && (
                        <ul style={{ marginLeft: '1.1rem', marginTop: '0.4rem', paddingLeft: 0, color: TEXT_DIM, fontSize: '0.82rem' }}>
                          {c.open_items.map((item: any, idx: number) => (
                            <li key={item.finding_id ?? idx}>
                              <Badge tone={severityTone(item.severity)}>{item.severity}</Badge> {item.title}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <Badge tone={c.status === 'gap' ? 'warning' : c.status === 'not_assessed' ? 'neutral' : 'success'}>
                        {c.status === 'gap' ? 'Gap' : c.status === 'not_assessed' ? 'Not assessed' : 'No gaps found'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
              <div style={styles.detailLabelLight}>Next Steps</div>
              <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', paddingLeft: 0, color: TEXT_DIM }}>
                {isoReadiness.next_steps.map((s: string) => <li key={s}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>
    )
}

// ============================================================
// REPORTS
// ============================================================
function ReportsSection({ ctx }: { ctx: any }) {
  const { api, token, notify, scans, setScans } = ctx
    const [report, setReport] = useState<any>(null)
    const [markdown, setMarkdown] = useState<string>('')
    const [selectedScan, setSelectedScan] = useState('')

    useEffect(() => {
      api('/scans').then((data: any) => setScans(Array.isArray(data) ? data : []))
    }, [token])

    useEffect(() => {
      if (selectedScan) return
      const first = scans.find((s: any) => s.status === 'completed')
      if (first) setSelectedScan(String(first.id))
    }, [scans, selectedScan])

    const completedScans = scans.filter((s: any) => s.status === 'completed')

    const generateReport = async (scanId: number) => {
      try {
        const res = await api(`/scans/${scanId}/report`)
        setReport(res)
        const mdRes = await api(`/scans/${scanId}/report/markdown`)
        setMarkdown(mdRes.markdown || '')
        notify('Report generated', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not generate the report', 'error')
      }
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Reports</h1>
        <p style={styles.hint}>
          Plain-language reports mapped to business impact and the obligations set out in Bill No. 25/2026 (passed 21 August 2026). Draft mapping; not legal advice.
        </p>

        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Generate Report</h3>
          <div style={{ maxWidth: 420 }}>
            <Field label="Scan" htmlFor="report-scan" hint={completedScans.length === 0 ? 'No completed scans to report on yet.' : undefined}>
              <Select value={selectedScan} onChange={(e) => setSelectedScan(e.target.value)} disabled={completedScans.length === 0}>
                <option value="">Select a completed scan</option>
                {completedScans.map((s: any) => (
                  <option key={s.id} value={s.id}>
                    {s.client?.name} — {s.scan_type}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
          <Button
            onClick={() => { if (selectedScan) generateReport(parseInt(selectedScan)) }}
            disabled={!selectedScan}
          >
            Generate report
          </Button>
        </div>

        {report && (
          <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
            <h3 style={styles.h3}>Report: Scan #{report.scan_id}</h3>
            <div className="responsive-stat-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
              <div><div style={styles.statLabel}>Client</div><div style={styles.statValue}>{report.client_name}</div></div>
              <div><div style={styles.statLabel}>Rating</div><div style={styles.statValue}>{report.overall_rating}</div></div>
              <div><div style={styles.statLabel}>Total Findings</div><div style={styles.statValue}>{report.findings_count.total}</div></div>
            </div>
            <div style={styles.detailLabelLight}>Executive Summary</div>
            <p style={styles.mutedText}>{report.executive_summary}</p>
            <div style={styles.detailLabelLight}>Plain Language</div>
            <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', paddingLeft: 0, color: TEXT_DIM }}>
              {report.plain_language.map((p: string, idx: number) => <li key={`${idx}-${p}`}>{p}</li>)}
            </ul>
            <div style={styles.detailLabelLight}>Recommendations</div>
            <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', paddingLeft: 0, color: TEXT_DIM }}>
              {report.recommendations.map((r: string, idx: number) => <li key={`${idx}-${r}`}>{r}</li>)}
            </ul>
            <div style={styles.detailLabelLight}>Compliance Mappings</div>
            <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', paddingLeft: 0, color: TEXT_DIM }}>
              {report.compliance_mappings
                .filter((m: any, idx: number, arr: any[]) =>
                  arr.findIndex((x: any) => x.law_article === m.law_article && x.action_required === m.action_required) === idx
                )
                .map((m: any, idx: number) => (
                  <li key={`${idx}-${m.law_article}`}>
                    <strong>{m.law_article}:</strong> {m.action_required}
                  </li>
                ))}
            </ul>
          </div>
        )}

        {markdown && (
          <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
              <h3 style={styles.h3}>Markdown Export</h3>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button
                  variant="secondary"
                  onClick={() => { navigator.clipboard?.writeText(markdown); notify('Report copied to clipboard', 'success') }}
                >
                  Copy
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    const blob = new Blob([markdown], { type: 'text/markdown' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `ultorn-report-scan-${report?.scan_id ?? 'export'}.md`
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                >
                  Download .md
                </Button>
              </div>
            </div>
            <div style={{ ...styles.codeBlock, maxHeight: '360px', overflowY: 'auto' }}>{markdown}</div>
          </div>
        )}
      </div>
    )
}

export default Page

// ============================================================
// Styles: light chrome + dark glass "focus panel" split list/detail
// ============================================================
const styles: any = {
  shell: {
    display: 'flex',
    minHeight: '100vh',
    background: BG,
    color: TEXT,
    fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
  sidebar: {
    background: 'var(--c-sidebar-bg)',
    color: TEXT,
    display: 'flex',
    flexDirection: 'column',
    borderRight: `1px solid ${BORDER}`,
  },
  sidebarBrand: { display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '1.5rem 1.25rem 1.25rem' },
  navBrandLogo: { height: '24px', width: 'auto' },
  navBrandDivider: { width: '1px', height: '16px', background: 'var(--c-border-strong)' },
  sidebarBrandText: { fontWeight: '600', fontSize: '0.95rem', color: 'var(--c-text)' },
  sidebarNavScroll: { flex: 1, overflowY: 'auto', paddingBottom: '0.5rem' },
  sidebarNav: { display: 'flex', flexDirection: 'column', gap: '0.15rem', padding: '0.5rem 0.5rem 0.75rem' },
  sidebarGroupLabel: {
    fontSize: '0.68rem',
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--c-sidebar-label)',
    padding: '0.6rem 0.9rem 0.3rem',
  },
  sidebarLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    color: 'var(--c-sidebar-link)',
    background: 'transparent',
    border: 'none',
    padding: '0.7rem 0.9rem',
    borderRadius: 0,
    cursor: 'pointer',
    fontSize: '0.88rem',
    fontWeight: 500,
    textAlign: 'left',
  },
  sidebarLinkActive: { background: ACCENT_SOFT, color: 'var(--c-text)' },
  sidebarIcon: { display: 'flex', alignItems: 'center', justifyContent: 'center', width: '20px', flex: '0 0 auto', color: 'inherit' },
  sidebarFooter: { padding: '1rem', borderTop: '1px solid var(--c-border)' },
  sidebarUser: { display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' },
  sidebarAvatar: {
    width: '32px', height: '32px', borderRadius: '50%', background: ACCENT, color: 'var(--c-on-accent)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, flex: '0 0 auto',
  },
  sidebarUserEmail: { fontSize: '0.8rem', color: 'var(--c-text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  sidebarUserRole: { fontSize: '0.72rem', color: 'var(--c-sidebar-link)', textTransform: 'capitalize' },
  sidebarSignOut: {
    width: '100%',
    background: 'var(--c-danger-bg)',
    color: 'var(--c-danger)',
    border: 'none',
    padding: '0.55rem 0.9rem',
    borderRadius: 0,
    cursor: 'pointer',
    fontSize: '0.82rem',
    fontWeight: 600,
  },
  main: { flex: 1, padding: '2rem', maxWidth: '1180px', margin: '0 auto', width: '100%', boxSizing: 'border-box' },
  section: {},
  pageTitle: { fontSize: '1.9rem', fontWeight: '700', margin: '0 0 1.25rem', color: TEXT, letterSpacing: '-0.02em' },
  hint: { color: TEXT_DIM, fontSize: '0.9rem', marginBottom: '1rem' },

  // Role-shaped dashboard header: workspace identity, scope and one-line job.
  dashHead: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: '1rem',
    flexWrap: 'wrap',
    marginBottom: '1.25rem',
  },
  dashTitle: { fontSize: '1.9rem', fontWeight: '700', margin: 0, color: TEXT, letterSpacing: '-0.02em' },
  dashSub: { color: TEXT_DIM, fontSize: '0.9rem', margin: '0.4rem 0 0', maxWidth: '62ch', lineHeight: 1.55 },
  roleEyebrow: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.45rem',
    marginBottom: '0.5rem',
    fontSize: '0.68rem',
    fontWeight: 700,
    letterSpacing: '0.11em',
    textTransform: 'uppercase',
    color: TEXT_DIM,
  },
  roleDot: {
    width: '6px',
    height: '6px',
    borderRadius: '999px',
    background: ACCENT_BRIGHT,
    flex: '0 0 auto',
  },
  scopeChip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.45rem',
    padding: '0.45rem 0.8rem',
    borderRadius: 0,
    border: `1px solid ${BORDER}`,
    background: SURFACE,
    fontSize: '0.75rem',
    whiteSpace: 'nowrap',
  },
  scopeChipLabel: {
    fontSize: '0.62rem',
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: TEXT_FAINT,
  },
  scopeChipValue: { color: TEXT, fontWeight: 600 },

  // One-line role brief between the metrics and the activity panels.
  rolePanel: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '1rem',
    flexWrap: 'wrap',
    padding: '0.9rem 1.1rem',
    marginBottom: '1rem',
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    borderLeft: `3px solid ${ACCENT_BRIGHT}`,
    borderRadius: 0,
  },
  rolePanelKicker: {
    fontSize: '0.64rem',
    fontWeight: 700,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color: TEXT_FAINT,
    marginBottom: '0.25rem',
  },
  rolePanelText: { fontSize: '0.86rem', color: TEXT_DIM, lineHeight: 1.5 },

  // Client dashboard: one plain-language posture statement as the headline
  // of the page, then three narrative cards -- no operator stat grid, no
  // "Recent Scans"/"Open admin" panels.
  postureBanner: {
    padding: '1.5rem 1.75rem',
    marginBottom: '1.5rem',
    border: `1px solid ${BORDER}`,
    borderLeft: '3px solid transparent',
  },
  postureBannerSuccess: { borderLeftColor: 'var(--c-success)', background: 'var(--c-success-soft)' },
  postureBannerWarning: { borderLeftColor: 'var(--c-warn)', background: 'var(--c-warn-soft)' },
  postureHeadline: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontWeight: 400,
    fontSize: '1.9rem',
    lineHeight: 1.2,
    letterSpacing: '-0.01em',
    color: TEXT,
  },
  postureSub: { fontSize: '0.9rem', color: TEXT_DIM, marginTop: '0.6rem', lineHeight: 1.5 },
  narrativeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '1rem',
  },
  narrativeCard: {
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    padding: '1.5rem',
  },
  narrativeValue: {
    fontSize: '1.7rem',
    fontWeight: '700',
    color: TEXT,
    fontFamily: MONO,
    fontVariantNumeric: 'tabular-nums',
    letterSpacing: '-0.02em',
    marginTop: '0.5rem',
    lineHeight: 1.3,
  },

  // Stat tiles: dark, slightly raised surfaces with a tabular-numeral,
  // monospace value for that instrument-panel feel.
  statGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' },
  statCard: {
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    boxShadow: '0 1px 0 var(--c-inset-highlight) inset, 0 12px 28px var(--c-shadow)',
    borderRadius: 0,
    padding: '1.25rem',
  },
  statCardEmphasis: {
    borderColor: ACCENT_BORDER,
    boxShadow: `0 0 0 1px ${ACCENT_BORDER} inset, 0 16px 36px var(--c-accent-glow)`,
  },
  statLabel: { fontSize: '0.78rem', fontWeight: 600, letterSpacing: '0.02em', color: TEXT_FAINT, marginBottom: '0.5rem' },
  statValue: { fontSize: '2rem', fontWeight: '700', color: TEXT, fontFamily: MONO, fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.02em' },
  statHint: { fontSize: '0.78rem', color: TEXT_FAINT, marginTop: '0.35rem' },
  skeleton: {
    height: '118px',
    borderRadius: 0,
    background: 'var(--c-wash)',
    animation: 'ultorn-pulse 1.4s ease-in-out infinite',
  },
  metricStrip: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
    gap: '0.75rem',
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    borderRadius: 0,
    padding: '0.9rem 1.1rem',
    marginBottom: '1.25rem',
  },
  metricItem: { display: 'flex', flexDirection: 'column', gap: '0.15rem' },
  metricValue: { fontSize: '1.2rem', fontWeight: 700, color: TEXT, fontFamily: MONO, fontVariantNumeric: 'tabular-nums' },
  metricLabel: { fontSize: '0.74rem', color: TEXT_FAINT },

  // Two-up panels on the dashboard
  split: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' },
  tableWrap: { overflowX: 'auto' as const, WebkitOverflowScrolling: 'touch' as const, maxWidth: '100%' },

  // General-purpose card (AI Guard, misc)
  lightCard: {
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    boxShadow: '0 1px 0 var(--c-inset-highlight) inset, 0 12px 28px var(--c-shadow)',
    borderRadius: 0,
    padding: '1.5rem',
    margin: '1rem 0',
  },
  h3: { fontSize: '1.05rem', fontWeight: '600', marginBottom: '0.6rem', color: TEXT },
  h4: { fontSize: '0.92rem', fontWeight: '600', marginBottom: '0.3rem', color: TEXT },
  detailLabel: { fontSize: '0.74rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: TEXT_FAINT, marginTop: '1.1rem', marginBottom: '0.5rem' },

  // Elevated "focus panel": the split list/detail workspace
  panelDark: {
    background: SURFACE_RAISED,
    borderRadius: 0,
    border: `1px solid ${BORDER}`,
    boxShadow: '0 1px 0 var(--c-inset-highlight) inset, 0 20px 44px var(--c-shadow-strong)',
    overflow: 'hidden',
  },
  panelHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1.25rem 1.25rem 0.5rem',
  },
  panelTitle: { margin: 0, fontSize: '1rem', fontWeight: 600, color: 'var(--c-text)' },
  panelBody: { display: 'flex', minHeight: '320px', maxHeight: '560px' },
  listPane: {
    flex: '0 0 40%',
    borderRight: '1px solid var(--c-wash)',
    padding: '0.5rem',
    overflowY: 'auto',
  },
  detailPane: { flex: '1 1 60%', padding: '1.5rem', overflowY: 'auto' },
  listRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.75rem',
    padding: '0.85rem 0.9rem',
    borderRadius: 0,
    cursor: 'pointer',
    marginBottom: '2px',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: 'transparent',
  },
  listRowActive: { background: ACCENT_SOFT, borderColor: ACCENT_BORDER },
  listRowMain: { minWidth: 0 },
  listRowTitle: { fontSize: '0.9rem', fontWeight: 600, color: TEXT, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  listRowSub: { fontSize: '0.78rem', color: TEXT_DIM },
  emptyState: { padding: '2rem 1rem', textAlign: 'center', color: TEXT_FAINT, fontSize: '0.88rem' },

  detailHeading: { fontSize: '1.3rem', fontWeight: 700, color: TEXT, letterSpacing: '-0.01em' },
  detailSub: { fontSize: '0.85rem', color: TEXT_DIM, marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' },

  subCardGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.6rem', marginTop: '1.25rem' },
  subCard: { background: SURFACE_SUNKEN, border: `1px solid ${BORDER}`, borderRadius: 0, padding: '0.85rem' },
  subCardLabel: { fontSize: '0.72rem', color: TEXT_FAINT, marginBottom: '0.35rem' },
  subCardValue: { fontSize: '1.2rem', fontWeight: 700, color: TEXT, fontFamily: MONO },

  scopeRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: `1px solid ${BORDER}`, fontSize: '0.85rem', color: TEXT },

  auditRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.7rem 0', borderTop: `1px solid ${BORDER}`, fontSize: '0.85rem' },

  // Table/typography tokens used throughout; everything in the console is
  // now one dark surface, so these no longer need a separate "light"
  // counterpart the way they did when stat tiles/cards sat on a light page.
  th: {
    padding: '0.75rem 0',
    fontSize: '0.72rem',
    fontWeight: 600,
    color: TEXT_FAINT,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.06em',
  },
  td: { padding: '0.75rem 0', verticalAlign: 'top' as const, color: TEXT },
  tdEmpty: { padding: '2rem 0', color: TEXT_FAINT, textAlign: 'center' as const },
  mutedText: { fontSize: '0.85rem', color: TEXT_DIM },
  detailLabelLight: {
    fontSize: '0.74rem',
    fontWeight: 600,
    letterSpacing: '0.06em',
    textTransform: 'uppercase' as const,
    color: TEXT_FAINT,
    marginTop: '1.1rem',
    marginBottom: '0.5rem',
  },
  auditRowLight: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.75rem',
    padding: '0.7rem 0',
    borderTop: `1px solid ${BORDER}`,
    fontSize: '0.85rem',
    color: TEXT,
  },

  badge: { display: 'inline-flex', padding: '0.2rem 0.6rem', borderRadius: 0, fontSize: '0.72rem', fontWeight: 600, whiteSpace: 'nowrap' },

  darkActionBtn: {
    background: TEXT,
    color: 'var(--c-inverse-ink)',
    border: 'none',
    padding: '0.5rem 1.1rem',
    borderRadius: 0,
    fontWeight: 600,
    cursor: 'pointer',
    fontSize: '0.82rem',
  },

  // Forms (used inside Modal, which is dark-glass itself)
  form: { display: 'flex', flexDirection: 'column', gap: '0.9rem' },
  input: {
    padding: '0.7rem 0.9rem',
    background: 'var(--c-field)',
    border: `1px solid ${BORDER_STRONG}`,
    borderRadius: 0,
    fontSize: '0.95rem',
    color: TEXT,
    width: '100%',
    boxSizing: 'border-box',
  },
  inputSmall: {
    padding: '0.4rem 0.6rem',
    background: 'var(--c-field)',
    border: `1px solid ${BORDER_STRONG}`,
    borderRadius: 0,
    fontSize: '0.9rem',
    color: TEXT,
  },
  button: {
    background: ACCENT,
    color: 'var(--c-on-accent)',
    border: 'none',
    padding: '0.72rem 1.4rem',
    borderRadius: 0,
    fontWeight: '600',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  buttonGhostLight: {
    background: 'var(--c-wash)',
    color: TEXT,
    border: `1px solid ${BORDER_STRONG}`,
    padding: '0.58rem 1.15rem',
    borderRadius: 0,
    fontWeight: '600',
    cursor: 'pointer',
    fontSize: '0.85rem',
  },
  buttonSmall: {
    background: ACCENT_SOFT,
    color: 'var(--c-accent-violet)',
    border: `1px solid ${ACCENT_BORDER}`,
    padding: '0.3rem 0.7rem',
    borderRadius: 0,
    fontWeight: '600',
    cursor: 'pointer',
    fontSize: '0.78rem',
  },
  alert: { padding: '0.75rem 1rem', borderRadius: 0, marginBottom: '1rem', fontSize: '0.9rem' },
  codeBlock: {
    background: 'var(--c-scrim)',
    color: 'var(--c-accent-violet)',
    padding: '1rem',
    borderRadius: 0,
    fontFamily: MONO,
    fontSize: '0.8rem',
    overflowX: 'auto',
    whiteSpace: 'pre-wrap',
    border: `1px solid ${BORDER}`,
  },
  checkboxLabel: { display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: TEXT_DIM },
  textarea: {
    padding: '0.7rem 0.9rem',
    background: 'var(--c-field)',
    border: `1px solid ${BORDER_STRONG}`,
    borderRadius: 0,
    fontSize: '0.95rem',
    color: TEXT,
    width: '100%',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
  },
  formRow: { display: 'flex', gap: '0.5rem', marginTop: '0.5rem', alignItems: 'center', flexWrap: 'wrap' },
}
