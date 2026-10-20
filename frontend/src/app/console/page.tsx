'use client'

import { useState, useEffect, useRef } from 'react'
import '../marketing-page.css'
import '../console.css'
import Modal from '../../components/Modal'
import { Button, ConfirmDialog, Field, Select, TextInput, Textarea, Toast } from './ui'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const ACCENT = '#7c3aed'
const ACCENT_SOFT = 'rgba(124,58,237,0.12)'
const ACCENT_BORDER = 'rgba(124,58,237,0.3)'

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
}

function LoginScreen({ onToken, notice }: { onToken: (token: string) => void; notice?: string }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const res = await fetch(`${API_URL}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
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
        <h1 className="login-title">Welcome back.</h1>
        <p className="login-sub">Sign in to the operator console.</p>
        {notice && <div className="login-notice" role="status">{notice}</div>}

        <form className="login-form" onSubmit={submit}>
          <div className="login-field">
            <label className="login-label" htmlFor="login-email">Email</label>
            <input
              id="login-email"
              className="login-input"
              type="email"
              placeholder="you@company.sn"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              autoFocus
            />
          </div>
          <div className="login-field">
            <label className="login-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              className="login-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          {error && <div className="login-error" role="alert">{error}</div>}
          <button type="submit" className="login-btn" disabled={submitting} aria-busy={submitting}>
            {submitting ? 'Verifying…' : 'Sign in'}
          </button>
        </form>

        <p className="login-hint">Access is provisioned by your Ultorn administrator.</p>
        <a href="/" className="login-back">← Back to home</a>
      </div>
    </div>
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
          border: '1px solid rgba(255,255,255,0.14)',
          color: 'rgba(255,255,255,0.72)',
          padding: '0.5rem 0.9rem',
          borderRadius: '10px',
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
              <div role="alert" style={{ color: '#fca5a5', fontSize: '0.82rem', marginBottom: '0.8rem' }}>
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
            <p style={{ color: 'rgba(255,255,255,0.58)', fontSize: '0.78rem', margin: '0.9rem 0 0' }}>
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
    tone === 'danger' ? '#b91c1c' : tone === 'warning' ? '#92400e' : tone === 'success' ? '#166534' : '#111113'
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
    neutral: { background: 'rgba(255,255,255,0.08)', color: '#d4d4d8' },
    success: { background: 'rgba(52,211,153,0.15)', color: '#6ee7b7' },
    warning: { background: 'rgba(251,191,36,0.15)', color: '#fcd34d' },
    danger: { background: 'rgba(248,113,113,0.15)', color: '#fca5a5' },
    accent: { background: ACCENT_SOFT, color: '#d8b4fe' },
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
  const [message, setMessage] = useState<{ text: string; type: ToastTone } | null>(null)
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const messageTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    setCollapsed(localStorage.getItem('ultorn_sidebar_collapsed') === 'true')
  }, [])

  useEffect(() => {
    if (!token) return
    fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (r.status === 401) throw new Error('Session expired')
        if (!r.ok) throw new Error('Could not load your profile')
        return r.json()
      })
      .then((data) => setUser(data))
      .catch(() => {
        localStorage.removeItem('token')
        setToken(null)
      })
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
      setView('login')
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
          setToken(t)
          setView('dashboard')
        }}
      />
    )
  }

  // Grouped so no menu exposes more than four choices at once (Hick's Law),
  // and ordered by the job an analyst is doing rather than by internal module.
  const NAV_GROUPS = [
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
        { key: 'compliance', label: 'Compliance', icon: 'compliance' },
        { key: 'reports', label: 'Reports', icon: 'reports' },
        { key: 'ai', label: 'AI Guard', icon: 'ai' },
      ],
    },
    {
      label: 'Governance',
      items: [
        { key: 'audit', label: 'Audit', icon: 'audit' },
        ...(user?.role === 'admin' ? [{ key: 'admin', label: 'Admin', icon: 'admin' }] : []),
      ],
    },
  ]

  const currentLabel = NAV_GROUPS.flatMap((g) => g.items).find((i) => i.key === view)?.label || 'Ultorn'

  const ctx = {
    token, api, notify, user,
    clients, setClients,
    scans, setScans,
    findings, setFindings,
    audit, setAudit,
    monitors, setMonitors,
    alerts, setAlerts,
    codeScans, setCodeScans,
    setView,
  }

  // ---------- MAIN LAYOUT ----------
  return (
    <div className="console-shell" style={styles.shell}>
      <div
        className={`console-backdrop${mobileOpen ? ' open' : ''}`}
        onClick={() => setMobileOpen(false)}
      />

      <aside className={`console-sidebar${collapsed ? ' collapsed' : ''}${mobileOpen ? ' mobile-open' : ''}`} style={styles.sidebar}>
        <div className="sidebar-brand" style={styles.sidebarBrand}>
          <img src="/brand/utachi-logo-white.png" alt="Utachi Industries" className="sidebar-logo-img" style={styles.navBrandLogo} />
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
        </div>

        <a
          href="/"
          className="sidebar-link sidebar-home"
          aria-label="Back to landing page"
          title="Back to landing page"
          style={{
            ...styles.sidebarLink,
            color: 'rgba(255,255,255,0.5)',
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

        <div style={styles.sidebarNavScroll}>
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
              <div style={styles.sidebarUserRole}>{user?.role || ''}</div>
            </div>
          </div>
          <ChangePasswordButton
            api={api}
            onChanged={(notice) => {
              setAuthNotice(notice)
              localStorage.removeItem('token')
              setToken(null)
              setView('login')
            }}
          />
          <button onClick={() => { localStorage.removeItem('token'); setToken(null); setView('login') }} style={styles.sidebarSignOut}>
            Sign out
          </button>
        </div>
      </aside>

      <div className="console-main" style={{ flex: 1, minWidth: 0 }}>
        <div className="console-mobile-bar">
          <button className="sidebar-burger" aria-label="Open menu" onClick={() => setMobileOpen(true)}>
            {ICONS.menu}
          </button>
          <img src="/brand/utachi-logo.png" alt="Utachi Industries" style={{ height: '20px' }} />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{currentLabel}</span>
        </div>

        <main style={styles.main}>
          {message && (
            <Toast message={message.text} tone={message.type} onDismiss={() => setMessage(null)} />
          )}

          {view === 'dashboard' && <Dashboard ctx={ctx} />}
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

function Dashboard({ ctx }: { ctx: any }) {
  const { api, token, clients, setClients, scans, setScans, audit, setAudit, setView } = ctx
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
        const [scansData, clientsData, auditData, alertsData, monitorsData, codeData] = await Promise.all([
          api('/scans'),
          api('/clients'),
          api('/audit?limit=8'),
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

    useEffect(() => { load() }, [token])

    const openAlerts = alerts.filter((a: any) => a.status === 'open')
    const activeMonitors = monitors.filter((m: any) => m.is_active)

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
        <StatCard
          emphasis
          label="Code issues"
          value={codeIssues}
          tone={codeIssues > 0 ? 'warning' : 'success'}
          hint="Across code scans"
        />
        <StatCard
          emphasis
          label="Active monitors"
          value={activeMonitors.length}
          tone="neutral"
          hint={`${monitors.length} configured`}
        />
      </div>
    )

    if (loading) {
      return (
        <div style={styles.section}>
          <h1 style={styles.pageTitle}>Dashboard</h1>
          <p style={styles.hint}>Live posture across scanning, continuous monitoring, and AI code review.</p>
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
          <h1 style={styles.pageTitle}>Dashboard</h1>
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
        <h1 style={styles.pageTitle}>Dashboard</h1>
        <p style={styles.hint}>
          Live posture across scanning, continuous monitoring, and AI code review.
        </p>
        {primary}

        <div style={styles.metricStrip} className="metric-strip">
          <Metric label="Total scans" value={stats.totalScans || 0} />
          <Metric label="High findings" value={stats.high || 0} />
          <Metric label="Clients" value={clients.length} />
          <Metric label="Monitors" value={monitors.length} />
        </div>

        <div style={styles.split}>
          <div style={styles.panelDark}>
            <div style={styles.panelHeader}>
              <h3 style={styles.panelTitle}>Recent Scans</h3>
              <button type="button" onClick={() => setView('scans')} style={styles.darkActionBtn}>Start a scan</button>
            </div>
            <div style={{ padding: '0 1.25rem 1.25rem' }}>
              {scans.slice(0, 6).map((s: any) => (
                <div key={s.id} style={styles.auditRow}>
                  <div>
                    <strong style={{ color: '#f5f5f7' }}>{s.client?.name || '-'}</strong>
                    <span style={styles.listRowSub}> · {s.scan_type}</span>
                  </div>
                  <Badge tone={s.status === 'completed' ? 'success' : 'warning'}>{s.status}</Badge>
                </div>
              ))}
              {scans.length === 0 && (
                <div style={styles.emptyState}>
                  No scans yet — a scan maps your attack surface and files findings for review.
                  <div style={{ marginTop: '0.75rem' }}>
                    <button type="button" onClick={() => setView('scans')} style={styles.darkActionBtn}>Start the first scan</button>
                  </div>
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
                    <strong style={{ color: '#f5f5f7' }}>{a.title}</strong>
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

        <div style={{ ...styles.panelDark, marginTop: '1rem' }}>
          <div style={styles.panelHeader}>
            <h3 style={styles.panelTitle}>Recent Audit Activity</h3>
            <button type="button" onClick={() => setView('audit')} style={styles.darkActionBtn}>View log</button>
          </div>
          <div style={{ padding: '0 1.25rem 1.25rem' }}>
            {audit.map((a: any) => (
              <div key={a.id} style={styles.auditRow}>
                <div>
                  <strong style={{ color: '#f5f5f7' }}>{a.action}</strong>
                  <span style={styles.listRowSub}> · {a.resource_type} #{a.resource_id}</span>
                </div>
                <span style={styles.listRowSub}>{new Date(a.created_at).toLocaleString()}</span>
              </div>
            ))}
            {audit.length === 0 && <div style={styles.emptyState}>No activity recorded yet.</div>}
          </div>
        </div>
      </div>
    )
  }

// ============================================================
// CLIENTS
// ============================================================
function ClientsSection({ ctx }: { ctx: any }) {
  const { api, token, notify, clients, setClients } = ctx
    const [newClient, setNewClient] = useState({ name: '', legal_name: '', contact_email: '', contact_phone: '' })
    const [showAdd, setShowAdd] = useState(false)
    const [selectedId, setSelectedId] = useState<any>(null)
    const [scopes, setScopes] = useState<any[]>([])
    const [newScope, setNewScope] = useState({ target: '', target_type: 'domain' })
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)

    useEffect(() => {
      api('/clients')
        .then((data: any) => setClients(Array.isArray(data) ? data : []))
        .catch((e: any) => notify(e.message || 'Could not load clients', 'error'))
        .finally(() => setLoading(false))
    }, [token])

    useEffect(() => {
      if (selectedId) {
        api(`/clients/${selectedId}/scopes`)
          .then((data: any) => setScopes(Array.isArray(data) ? data : []))
          .catch((e: any) => notify(e.message || 'Could not load scopes', 'error'))
      }
    }, [selectedId])

    const createClient = async (e: any) => {
      e.preventDefault()
      setSubmitting(true)
      try {
        await api('/clients', { method: 'POST', body: JSON.stringify(newClient) })
        setNewClient({ name: '', legal_name: '', contact_email: '', contact_phone: '' })
        setShowAdd(false)
        const data = await api('/clients')
        setClients(Array.isArray(data) ? data : [])
        notify('Client created', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not create the client', 'error')
      } finally {
        setSubmitting(false)
      }
    }

    const addScope = async (e: any) => {
      e.preventDefault()
      try {
        await api(`/clients/${selectedId}/scopes`, { method: 'POST', body: JSON.stringify(newScope) })
        setNewScope({ target: '', target_type: 'domain' })
        const data = await api(`/clients/${selectedId}/scopes`)
        setScopes(Array.isArray(data) ? data : [])
        notify('Scope added', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not add the scope', 'error')
      }
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Clients</h1>
        <p style={styles.hint}>Onboard clients, then register the domains, IPs, and URLs they have authorised you to assess.</p>

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
              <Button type="submit" loading={submitting} disabled={!newClient.name.trim()}>
                Add client
              </Button>
            </form>
          </Modal>
        )}

        <SplitPanel
          title="All Clients"
          loading={loading}
          action={<button type="button" onClick={() => setShowAdd(true)} style={styles.darkActionBtn}>+ Add client</button>}
          items={clients}
          selectedId={selectedId}
          onSelect={(c) => setSelectedId(c.id)}
          emptyLabel="No clients yet."
          emptyHint="Add a client to start registering scan scopes."
          renderRow={(c) => (
            <>
              <div style={styles.listRowMain}>
                <div style={styles.listRowTitle}>{c.name}</div>
                <div style={styles.listRowSub}>{c.contact_email || 'No contact email'}</div>
              </div>
              <Badge tone={c.is_active ? 'success' : 'neutral'}>{c.is_active ? 'Active' : 'Inactive'}</Badge>
            </>
          )}
          renderDetail={(c) => (
            <>
              <div style={styles.detailHeading}>{c.name}</div>
              {c.legal_name && <div style={styles.listRowSub}>{c.legal_name}</div>}
              <div style={styles.detailSub}>
                {c.contact_email || 'No contact email'} · {c.contact_phone || 'No contact phone'}
              </div>

              <div style={{ marginTop: '1.25rem' }}>
                <div style={styles.detailLabel}>Scan scopes</div>
                {scopes.length === 0 && <div style={styles.listRowSub}>No scopes added.</div>}
                {scopes.map((s: any) => (
                  <div key={s.id} style={styles.scopeRow}>
                    <span>{s.target}</span>
                    <Badge tone="neutral">{s.target_type}</Badge>
                  </div>
                ))}
                <form onSubmit={addScope} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                  <input
                    aria-label="Scope target (domain, IP, or URL)"
                    value={newScope.target}
                    onChange={(e) => setNewScope({ ...newScope, target: e.target.value })}
                    style={{ ...styles.input, flex: '1 1 200px', background: 'rgba(255,255,255,0.07)', color: '#f5f5f7', border: '1px solid rgba(255,255,255,0.18)' }}
                  />
                  <select
                    aria-label="Scope type"
                    value={newScope.target_type}
                    onChange={(e) => setNewScope({ ...newScope, target_type: e.target.value })}
                    style={{ ...styles.inputSmall, background: 'rgba(255,255,255,0.07)', color: '#f5f5f7', border: '1px solid rgba(255,255,255,0.18)' }}
                  >
                    <option value="domain">Domain</option>
                    <option value="ip">IP</option>
                    <option value="url">URL</option>
                  </select>
                  <button type="submit" disabled={!newScope.target.trim()} style={{ ...styles.darkActionBtn, opacity: newScope.target.trim() ? 1 : 0.5 }}>Add</button>
                </form>
              </div>
            </>
          )}
        />
      </div>
    )
  }

// ============================================================
// SCANS
// ============================================================
function ScansSection({ ctx }: { ctx: any }) {
  const { api, token, notify, clients, setClients, scans, setScans } = ctx
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
          No verification gate. Scans run on all in-scope targets immediately. Full data extraction: banners, headers, page content, body.
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
          action={<button type="button" onClick={() => setShowStart(true)} style={styles.darkActionBtn}>+ Start scan</button>}
          items={scans}
          selectedId={selectedId}
          onSelect={(s) => setSelectedId(s.id)}
          emptyLabel="No scans yet."
          emptyHint="Start a scan to map the client's attack surface."
          renderRow={(s) => (
            <>
              <div style={styles.listRowMain}>
                <div style={styles.listRowTitle}>{s.client?.name || '-'}</div>
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
              {s.status !== 'running' && (
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
  const { api, token, notify, findings, setFindings } = ctx
    const [selectedId, setSelectedId] = useState<any>(null)
    const [reviewStatus, setReviewStatus] = useState('fixed')

    useEffect(() => {
      api('/scans').then((data: any) => {
        setFindings(data.flatMap((s: any) => s.findings || []))
      })
    }, [token])

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
                <div style={styles.listRowTitle}>{f.title}</div>
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

                {needsReview && (
                  <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.5rem' }}>
                    <select
                      aria-label="New status for this finding"
                      value={reviewStatus}
                      onChange={(e) => setReviewStatus(e.target.value)}
                      style={{ ...styles.input, background: 'rgba(255,255,255,0.07)', color: '#f5f5f7', border: '1px solid rgba(255,255,255,0.18)' }}
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
  const { api, token, notify } = ctx
    const [prompt, setPrompt] = useState('')
    const [clientName, setClientName] = useState('')
    const [response, setResponse] = useState('')
    const [aiMeta, setAiMeta] = useState<any>(null)
    const [sanitized, setSanitized] = useState('')
    const [forceLocal, setForceLocal] = useState(false)
    const [busy, setBusy] = useState(false)

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
          Prompts are sanitized (client names, IPs, credentials, PII stripped) before reaching any external model.
          Sensitive data stays local. Every query is immutably logged.
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
              placeholder="e.g. 'Analyze this vulnerability report for client Acme Corp at 10.0.0.5 with API key sk-12345'"
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
                <div style={styles.listRowTitle}>{a.action}</div>
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
          items={users}
          selectedId={selectedUserId}
          onSelect={(u) => setSelectedUserId(u.id)}
          emptyLabel="No users yet."
          renderRow={(u) => (
            <>
              <div style={styles.listRowMain}>
                <div style={styles.listRowTitle}>{u.email}</div>
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
                style={{ ...styles.input, background: 'rgba(255,255,255,0.07)', color: '#f5f5f7', border: '1px solid rgba(255,255,255,0.18)' }}
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
          <p style={{ ...styles.hint, padding: '0 1.25rem', color: 'rgba(255,255,255,0.68)' }}>
            Keys authenticate programmatic access via the <code>X-API-Key</code> header, scoped to the admin account that minted them.
          </p>

          {showCreate && (
            <Modal title="Create API key" onClose={() => setShowCreate(false)}>
              {mintedKey ? (
                <>
                  <div style={styles.codeBlock}>
                    {mintedKey}
                    <div style={{ color: '#fcd34d', marginTop: '0.5rem', fontFamily: 'inherit' }}>Copy this now. It will not be shown again.</div>
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
                  <strong style={{ color: '#f5f5f7' }}>{k.name}</strong>
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

        {resetUser && (
          <Modal title={`Reset password for ${resetUser.email}`} onClose={closeReset}>
            {temporaryPassword ? (
              <>
                <p style={{ color: 'rgba(255,255,255,0.72)', fontSize: '0.85rem', marginTop: 0 }}>
                  Share this temporary password securely. The user should change it after signing in.
                </p>
                <div style={styles.codeBlock}>
                  {temporaryPassword}
                  <div style={{ color: '#fcd34d', marginTop: '0.5rem', fontFamily: 'inherit' }}>
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
                <p style={{ color: 'rgba(255,255,255,0.72)', fontSize: '0.85rem', marginTop: 0 }}>
                  This replaces the user&apos;s current password immediately. Their existing session may stay active until it expires.
                </p>
                {resetError && (
                  <div role="alert" style={{ color: '#fca5a5', fontSize: '0.82rem', marginBottom: '0.8rem' }}>
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
  const { api, token, notify, monitors, setMonitors } = ctx
    const [newMonitor, setNewMonitor] = useState({ target: '', monitor_type: 'access_anomaly', client_id: '' })
    const [clientsForMonitor, setClientsForMonitor] = useState<any[]>([])
    const [selectedId, setSelectedId] = useState<any>(null)
    const [monitorAlerts, setMonitorAlerts] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [pendingDelete, setPendingDelete] = useState<any>(null)

    useEffect(() => {
      Promise.all([api('/monitors'), api('/clients')])
        .then(([monitorsData, clientsData]) => {
          setMonitors(Array.isArray(monitorsData) ? monitorsData : [])
          setClientsForMonitor(Array.isArray(clientsData) ? clientsData : [])
        })
        .catch((e: any) => notify(e.message || 'Could not load monitors', 'error'))
        .finally(() => setLoading(false))
    }, [token])

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

    const canSubmit = Boolean(newMonitor.client_id && newMonitor.target.trim())

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Continuous Monitoring</h1>
        <p style={styles.hint}>
          AI agents continuously watch for anomalous access, config drift, leaked credentials,
          and policy violations before they go live.
        </p>

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
                <div style={styles.listRowTitle}>{m.target}</div>
                <div style={styles.listRowSub}>{m.monitor_type}</div>
              </div>
              <Badge tone={m.is_active ? 'success' : 'neutral'}>{m.is_active ? 'Active' : 'Inactive'}</Badge>
            </>
          )}
          renderDetail={(m) => (
            <>
              <div style={styles.detailHeading}>{m.target}</div>
              <div style={styles.detailSub}>{m.monitor_type} · last check {m.last_check ? new Date(m.last_check).toLocaleString() : 'never'}</div>
              <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button type="button" onClick={() => runCheck(m.id)} style={styles.darkActionBtn}>Run check now</button>
                <button type="button" onClick={() => toggleActive(m)} style={styles.darkActionBtn}>
                  {m.is_active ? 'Pause' : 'Resume'}
                </button>
                <button type="button" onClick={() => setPendingDelete(m)} style={styles.darkActionBtn}>Delete</button>
              </div>
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
  const { api, token, notify } = ctx
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
          {openCount > 0
            ? `${openCount} open alert${openCount === 1 ? '' : 's'} need review. Acknowledge to claim one, resolve when fixed.`
            : 'No open alerts right now. Acknowledge and resolve each alert as it arrives.'}
        </p>

        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <select
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
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 620 }}>
              <caption className="sr-only">Monitoring alerts with severity, status, and time detected</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
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
                <tr key={a.id} style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
                  <td style={styles.td}>
                    <div>{a.title}</div>
                    {a.description && <div style={{ fontSize: '0.78rem', color: 'rgba(17,17,19,0.62)' }}>{a.description}</div>}
                  </td>
                  <td style={styles.td}><Badge tone={severityTone(a.severity)}>{a.severity}</Badge></td>
                  <td style={styles.td}>{a.status.replace('_', ' ')}</td>
                  <td style={{ ...styles.td, fontSize: '0.8rem', color: 'rgba(17,17,19,0.62)' }}>{new Date(a.created_at).toLocaleString()}</td>
                  <td style={{ ...styles.td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {a.status === 'open' && (
                      <button
                        type="button"
                        onClick={() => setStatus(a, 'acknowledged')}
                        disabled={busyId === a.id}
                        style={styles.buttonGhostLight}
                      >
                        Acknowledge
                      </button>
                    )}
                    {a.status !== 'resolved' && (
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
  const { api, token, notify } = ctx
    const [schedules, setSchedules] = useState<any[]>([])
    const [clientsForSchedule, setClientsForSchedule] = useState<any[]>([])
    const [newSchedule, setNewSchedule] = useState({ client_id: '', scan_type: 'vulnerability', interval_minutes: '1440' })
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [pendingDelete, setPendingDelete] = useState<any>(null)

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

    const humanInterval = (minutes: number) => {
      if (minutes % 1440 === 0) return `${minutes / 1440} day(s)`
      if (minutes % 60 === 0) return `${minutes / 60} hour(s)`
      return `${minutes} min`
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Recurring Scans</h1>
        <p style={styles.hint}>
          Schedule vulnerability assessments to run automatically. Each run uses the client's
          current non-excluded scopes and files findings for human review.
        </p>

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

        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Schedules</h3>
          <div style={styles.tableWrap}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 680 }}>
              <caption className="sr-only">Recurring scan schedules with their next run time</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
                <th scope="col" style={styles.th}>Client</th>
                <th scope="col" style={styles.th}>Type</th>
                <th scope="col" style={styles.th}>Every</th>
                <th scope="col" style={styles.th}>Next run</th>
                <th scope="col" style={styles.th}><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={5} style={styles.tdEmpty} role="status">Loading schedules…</td></tr>
              )}
              {!loading && schedules.length === 0 && (
                <tr><td colSpan={5} style={styles.tdEmpty}>No schedules yet. Create one above to run scans automatically.</td></tr>
              )}
              {schedules.map((s: any) => (
                <tr key={s.id} style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
                  <td style={styles.td}>{s.client?.name || s.client_id}</td>
                  <td style={styles.td}>{s.scan_type}</td>
                  <td style={styles.td}>{humanInterval(s.interval_minutes)}</td>
                  <td style={{ ...styles.td, fontSize: '0.8rem', color: 'rgba(17,17,19,0.62)' }}>
                    {s.next_run ? new Date(s.next_run).toLocaleString() : '—'}
                  </td>
                  <td style={{ ...styles.td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <Badge tone={s.is_active ? 'success' : 'neutral'}>{s.is_active ? 'Active' : 'Paused'}</Badge>
                    <button type="button" onClick={() => runNow(s)} style={{ ...styles.buttonGhostLight, marginLeft: '0.4rem' }}>Run now</button>
                    <button type="button" onClick={() => toggle(s)} style={{ ...styles.buttonGhostLight, marginLeft: '0.4rem' }}>{s.is_active ? 'Pause' : 'Resume'}</button>
                    <button type="button" onClick={() => setPendingDelete(s)} style={{ ...styles.buttonGhostLight, marginLeft: '0.4rem' }}>Delete</button>
                  </td>
                </tr>
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
  const { api, token, notify, codeScans, setCodeScans } = ctx
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

        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Code Scans</h3>
          <div style={styles.tableWrap}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 620 }}>
              <caption className="sr-only">Code scans and the issues found in each</caption>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
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
                <tr key={s.id} style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
                  <td style={styles.td}>{s.repository_url || '-'}</td>
                  <td style={styles.td}>{s.branch}</td>
                  <td style={styles.td}><Badge tone={s.status === 'completed' ? 'success' : 'warning'}>{s.status}</Badge></td>
                  <td style={styles.td}>{s.issues_found}</td>
                  <td style={{ ...styles.td, textAlign: 'right' }}>
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
// COMPLIANCE
// ============================================================
function ComplianceSection({ ctx }: { ctx: any }) {
  const { api, notify } = ctx
    const [summary, setSummary] = useState<any>(null)
    const [mappings, setMappings] = useState<any[]>([])
    const [clientSector, setClientSector] = useState('banking')

    const runSummary = async () => {
      try {
        const res = await api(`/compliance/summary?total_findings=10&critical=2&high=3&medium=4&client_sector=${clientSector}`)
        setSummary(res)
      } catch (e: any) {
        notify(e.message || 'Could not build the summary', 'error')
      }
    }

    const runMap = async () => {
      const findings = [
        { title: 'Open SSH port on public IP', severity: 'high', id: 1 },
        { title: 'Hardcoded API key in source', severity: 'critical', id: 2 },
        { title: 'SSL verification disabled', severity: 'medium', id: 3 },
      ]
      try {
        const res = await api('/compliance/map', {
          method: 'POST',
          body: JSON.stringify({ findings, client_sector: clientSector }),
        })
        setMappings(res.mappings || [])
        notify('Compliance mapping generated', 'success')
      } catch (e: any) {
        notify(e.message || 'Could not generate the mapping', 'error')
      }
    }

    return (
      <div style={styles.section}>
        <h1 style={styles.pageTitle}>Compliance — Senegal Cyber Law 2026</h1>
        <p style={styles.hint}>
          Map findings to regulatory obligations under Senegal's new cybersecurity law:
          National CERT, mandatory incident reporting, vulnerability disclosure,
          local hosting, and AI governance.
        </p>

        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Compliance Summary</h3>
          <div style={{ maxWidth: 320 }}>
            <Field label="Client sector" htmlFor="compliance-sector">
              <Select value={clientSector} onChange={(e) => setClientSector(e.target.value)}>
                <option value="banking">Banking / Mobile Money</option>
                <option value="telecom">Telecom</option>
                <option value="government">Government</option>
                <option value="other">Other</option>
              </Select>
            </Field>
          </div>
          <Button onClick={runSummary}>Run summary</Button>
          {summary && (
            <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,0,0,0.04)', borderRadius: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                <div><div style={styles.statLabel}>Critical Findings</div><div style={styles.statValue}>{summary.critical}</div></div>
                <div><div style={styles.statLabel}>Reporting Required</div><div style={styles.statValue}>{summary.reporting_required ? 'Yes' : 'No'}</div></div>
                <div><div style={styles.statLabel}>CERT Window</div><div style={styles.statValue}>{summary.cert_notification_window_hours}h</div></div>
              </div>
              <p style={styles.mutedText}>{summary.framework}</p>
              <p style={styles.mutedText}>Sector: {summary.client_sector}</p>
              <div style={styles.detailLabelLight}>Next Steps</div>
              <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', color: 'rgba(17,17,19,0.75)' }}>
                {summary.next_steps.map((s: string) => <li key={s}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>

        <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Findings → Law Mapping</h3>
          <Button variant="secondary" onClick={runMap}>Generate mappings</Button>
          {mappings.length === 0 && (
            <p style={{ ...styles.mutedText, marginTop: '0.75rem' }}>
              No mapping generated yet. This maps sample findings to Senegal Cyber Law obligations.
            </p>
          )}
          {mappings.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              {mappings.map((m: any) => (
                <div key={m.law_article} style={styles.auditRowLight}>
                  <div style={{ flex: 1 }}>
                    <strong>{m.law_article}</strong>
                    <br />
                    <span style={styles.mutedText}>{m.obligation}</span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <Badge tone={m.priority === 'immediate' ? 'danger' : m.priority === 'urgent' ? 'warning' : 'neutral'}>{m.priority}</Badge>
                  </div>
                </div>
              ))}
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
          Plain-language reports mapped to business impact and Senegal Cyber Law 2026 obligations.
        </p>

        <div style={styles.lightCard}>
          <h3 style={styles.h3}>Generate Report</h3>
          <div style={{ maxWidth: 420 }}>
            <Field label="Scan" htmlFor="report-scan" hint={scans.length === 0 ? 'No completed scans to report on yet.' : undefined}>
              <Select value={selectedScan} onChange={(e) => setSelectedScan(e.target.value)} disabled={scans.length === 0}>
                <option value="">Select a scan</option>
                {scans.map((s: any) => (
                  <option key={s.id} value={s.id}>
                    {s.client?.name} — {s.scan_type} ({s.status})
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
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
              <div><div style={styles.statLabel}>Client</div><div style={styles.statValue}>{report.client_name}</div></div>
              <div><div style={styles.statLabel}>Rating</div><div style={styles.statValue}>{report.overall_rating}</div></div>
              <div><div style={styles.statLabel}>Total Findings</div><div style={styles.statValue}>{report.findings_count.total}</div></div>
            </div>
            <div style={styles.detailLabelLight}>Executive Summary</div>
            <p style={styles.mutedText}>{report.executive_summary}</p>
            <div style={styles.detailLabelLight}>Plain Language</div>
            <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', color: 'rgba(17,17,19,0.75)' }}>
              {report.plain_language.map((p: string) => <li key={p}>{p}</li>)}
            </ul>
            <div style={styles.detailLabelLight}>Recommendations</div>
            <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', color: 'rgba(17,17,19,0.75)' }}>
              {report.recommendations.map((r: string) => <li key={r}>{r}</li>)}
            </ul>
            <div style={styles.detailLabelLight}>Compliance Mappings</div>
            <ul style={{ marginLeft: '1.25rem', marginTop: '0.5rem', color: 'rgba(17,17,19,0.75)' }}>
              {report.compliance_mappings.map((m: any) => (
                <li key={m.law_article}>
                  <strong>{m.law_article}:</strong> {m.action_required}
                </li>
              ))}
            </ul>
          </div>
        )}

        {markdown && (
          <div style={{ ...styles.lightCard, marginTop: '1rem' }}>
            <h3 style={styles.h3}>Markdown Export</h3>
            <div style={styles.codeBlock}>{markdown}</div>
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
    background: '#f5f5f7',
    color: '#111113',
    fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
  sidebar: {
    background: '#111113',
    color: '#f5f5f7',
    display: 'flex',
    flexDirection: 'column',
  },
  sidebarBrand: { display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '1.5rem 1.25rem 1.25rem' },
  navBrandLogo: { height: '24px', width: 'auto' },
  navBrandDivider: { width: '1px', height: '16px', background: 'rgba(255,255,255,0.2)' },
  sidebarBrandText: { fontWeight: '600', fontSize: '0.95rem', color: '#f5f5f7' },
  sidebarNavScroll: { flex: 1, overflowY: 'auto', paddingBottom: '0.5rem' },
  sidebarNav: { display: 'flex', flexDirection: 'column', gap: '0.15rem', padding: '0.5rem 0.5rem 0.75rem' },
  sidebarGroupLabel: {
    fontSize: '0.68rem',
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'rgba(255,255,255,0.48)',
    padding: '0.6rem 0.9rem 0.3rem',
  },
  sidebarLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    color: 'rgba(255,255,255,0.6)',
    background: 'transparent',
    border: 'none',
    padding: '0.7rem 0.9rem',
    borderRadius: '12px',
    cursor: 'pointer',
    fontSize: '0.88rem',
    fontWeight: 500,
    textAlign: 'left',
  },
  sidebarLinkActive: { background: ACCENT_SOFT, color: '#fff' },
  sidebarIcon: { display: 'flex', alignItems: 'center', justifyContent: 'center', width: '20px', flex: '0 0 auto', color: 'inherit' },
  sidebarFooter: { padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.08)' },
  sidebarUser: { display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' },
  sidebarAvatar: {
    width: '32px', height: '32px', borderRadius: '50%', background: ACCENT, color: '#fff',
    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, flex: '0 0 auto',
  },
  sidebarUserEmail: { fontSize: '0.8rem', color: '#f5f5f7', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  sidebarUserRole: { fontSize: '0.72rem', color: 'rgba(255,255,255,0.6)', textTransform: 'capitalize' },
  sidebarSignOut: {
    width: '100%',
    background: 'rgba(220,38,38,0.12)',
    color: '#fca5a5',
    border: 'none',
    padding: '0.55rem 0.9rem',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '0.82rem',
    fontWeight: 600,
  },
  main: { flex: 1, padding: '2rem', maxWidth: '1180px', margin: '0 auto', width: '100%', boxSizing: 'border-box' },
  section: {},
  pageTitle: { fontSize: '1.75rem', fontWeight: '600', margin: '0 0 1.25rem', color: '#111113', letterSpacing: '-0.01em' },
  hint: { color: 'rgba(17,17,19,0.68)', fontSize: '0.9rem', marginBottom: '1rem' },

  // Light stat tiles
  statGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' },
  statCard: {
    background: 'rgba(255,255,255,0.8)',
    border: '1px solid rgba(0,0,0,0.06)',
    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
    borderRadius: '18px',
    padding: '1.25rem',
  },
  statCardEmphasis: {
    borderTop: `3px solid ${ACCENT_BORDER}`,
    boxShadow: '0 6px 24px rgba(17,17,19,0.05)',
  },
  statLabel: { fontSize: '0.8rem', color: 'rgba(17,17,19,0.62)', marginBottom: '0.4rem' },
  statValue: { fontSize: '1.9rem', fontWeight: '700', color: '#111113' },
  statHint: { fontSize: '0.78rem', color: 'rgba(17,17,19,0.58)', marginTop: '0.3rem' },
  skeleton: {
    height: '118px',
    borderRadius: '18px',
    background: 'linear-gradient(90deg, rgba(0,0,0,0.05), rgba(0,0,0,0.09), rgba(0,0,0,0.05))',
    backgroundSize: '200% 100%',
    animation: 'ultorn-sheen 1.4s ease-in-out infinite',
  },
  metricStrip: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
    gap: '0.75rem',
    background: 'rgba(255,255,255,0.65)',
    border: '1px solid rgba(0,0,0,0.06)',
    borderRadius: '18px',
    padding: '0.9rem 1.1rem',
    marginBottom: '1.25rem',
  },
  metricItem: { display: 'flex', flexDirection: 'column', gap: '0.1rem' },
  metricValue: { fontSize: '1.15rem', fontWeight: 700, color: '#111113' },
  metricLabel: { fontSize: '0.75rem', color: 'rgba(17,17,19,0.6)' },

  // Two-up dark panels on the dashboard
  split: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' },
  tableWrap: { overflowX: 'auto' as const, WebkitOverflowScrolling: 'touch' as const, maxWidth: '100%' },

  // Light card (AI Guard, misc)
  lightCard: {
    background: 'rgba(255,255,255,0.8)',
    border: '1px solid rgba(0,0,0,0.06)',
    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
    borderRadius: '18px',
    padding: '1.5rem',
    margin: '1rem 0',
  },
  h3: { fontSize: '1.05rem', fontWeight: '600', marginBottom: '0.6rem', color: '#111113' },
  detailLabel: { fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.58)', marginTop: '1.1rem', marginBottom: '0.5rem' },

  // Dark glass "focus panel": the split list/detail workspace
  panelDark: {
    background: '#16161a',
    borderRadius: '24px',
    border: '1px solid rgba(255,255,255,0.06)',
    overflow: 'hidden',
  },
  panelHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1.25rem 1.25rem 0.5rem',
  },
  panelTitle: { margin: 0, fontSize: '1rem', fontWeight: 600, color: '#f5f5f7' },
  panelBody: { display: 'flex', minHeight: '320px', maxHeight: '560px' },
  listPane: {
    flex: '0 0 40%',
    borderRight: '1px solid rgba(255,255,255,0.06)',
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
    borderRadius: '14px',
    cursor: 'pointer',
    marginBottom: '2px',
  },
  listRowActive: { background: ACCENT_SOFT },
  listRowMain: { minWidth: 0 },
  listRowTitle: { fontSize: '0.9rem', fontWeight: 600, color: '#f5f5f7', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  listRowSub: { fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)' },
  emptyState: { padding: '2rem 1rem', textAlign: 'center', color: 'rgba(255,255,255,0.58)', fontSize: '0.88rem' },

  detailHeading: { fontSize: '1.25rem', fontWeight: 600, color: '#f5f5f7' },
  detailSub: { fontSize: '0.85rem', color: 'rgba(255,255,255,0.68)', marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' },

  subCardGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.6rem', marginTop: '1.25rem' },
  subCard: { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '14px', padding: '0.85rem' },
  subCardLabel: { fontSize: '0.72rem', color: 'rgba(255,255,255,0.6)', marginBottom: '0.3rem' },
  subCardValue: { fontSize: '1.2rem', fontWeight: 700, color: '#f5f5f7' },

  scopeRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(255,255,255,0.06)', fontSize: '0.85rem', color: '#e5e7eb' },

  auditRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.7rem 0', borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: '0.85rem' },

  // Light-surface counterparts (used inside light cards; the dark versions
  // render white text and would be unreadable on white).
  th: {
    padding: '0.75rem 0',
    fontSize: '0.75rem',
    fontWeight: 600,
    color: 'rgba(17,17,19,0.62)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  td: { padding: '0.75rem 0', verticalAlign: 'top' as const },
  tdEmpty: { padding: '2rem 0', color: 'rgba(17,17,19,0.62)', textAlign: 'center' as const },
  mutedText: { fontSize: '0.85rem', color: 'rgba(17,17,19,0.68)' },
  detailLabelLight: {
    fontSize: '0.75rem',
    fontWeight: 600,
    letterSpacing: '0.04em',
    textTransform: 'uppercase' as const,
    color: 'rgba(17,17,19,0.6)',
    marginTop: '1.1rem',
    marginBottom: '0.5rem',
  },
  auditRowLight: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.75rem',
    padding: '0.7rem 0',
    borderTop: '1px solid rgba(0,0,0,0.08)',
    fontSize: '0.85rem',
    color: '#111113',
  },

  badge: { display: 'inline-flex', padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.72rem', fontWeight: 600, whiteSpace: 'nowrap' },

  darkActionBtn: {
    background: '#fdfdfd',
    color: '#050505',
    border: 'none',
    padding: '0.5rem 1.1rem',
    borderRadius: '999px',
    fontWeight: 600,
    cursor: 'pointer',
    fontSize: '0.82rem',
  },

  // Forms (used inside Modal, which is dark-glass itself)
  form: { display: 'flex', flexDirection: 'column', gap: '0.9rem' },
  input: {
    padding: '0.7rem 0.9rem',
    background: 'rgba(0,0,0,0.04)',
    border: '1px solid rgba(0,0,0,0.1)',
    borderRadius: '10px',
    fontSize: '0.95rem',
    color: 'inherit',
    width: '100%',
    boxSizing: 'border-box',
  },
  inputSmall: {
    padding: '0.4rem 0.6rem',
    background: 'rgba(0,0,0,0.04)',
    border: '1px solid rgba(0,0,0,0.1)',
    borderRadius: '8px',
    fontSize: '0.9rem',
  },
  button: {
    background: ACCENT,
    color: '#fff',
    border: 'none',
    padding: '0.75rem 1.5rem',
    borderRadius: '999px',
    fontWeight: '600',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  buttonGhostLight: {
    background: 'rgba(0,0,0,0.05)',
    color: '#111113',
    border: '1px solid rgba(0,0,0,0.1)',
    padding: '0.6rem 1.2rem',
    borderRadius: '999px',
    fontWeight: '600',
    cursor: 'pointer',
    fontSize: '0.85rem',
  },
  buttonSmall: {
    background: ACCENT_SOFT,
    color: '#d8b4fe',
    border: `1px solid ${ACCENT_BORDER}`,
    padding: '0.3rem 0.7rem',
    borderRadius: '999px',
    fontWeight: '600',
    cursor: 'pointer',
    fontSize: '0.78rem',
  },
  alert: { padding: '0.75rem 1rem', borderRadius: '14px', marginBottom: '1rem', fontSize: '0.9rem' },
  codeBlock: {
    background: 'rgba(0,0,0,0.3)',
    color: '#d8b4fe',
    padding: '1rem',
    borderRadius: '12px',
    fontFamily: 'monospace',
    fontSize: '0.8rem',
    overflowX: 'auto',
    whiteSpace: 'pre-wrap',
    border: '1px solid rgba(255,255,255,0.08)',
  },
  checkboxLabel: { display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'rgba(17,17,19,0.6)' },
  textarea: {
    padding: '0.7rem 0.9rem',
    background: 'rgba(0,0,0,0.04)',
    border: '1px solid rgba(0,0,0,0.1)',
    borderRadius: '10px',
    fontSize: '0.95rem',
    color: 'inherit',
    width: '100%',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
  },
  formRow: { display: 'flex', gap: '0.5rem', marginTop: '0.5rem', alignItems: 'center', flexWrap: 'wrap' },
}
