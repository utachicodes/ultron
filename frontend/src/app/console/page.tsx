'use client'

import { useState, useEffect } from 'react'
import '../marketing-page.css'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function LoginScreen({ onToken }: { onToken: (token: string) => void }) {
  const [email, setEmail] = useState('admin@ultorn.local')
  const [password, setPassword] = useState('admin123')
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

        <form className="login-form" onSubmit={submit}>
          <label className="sr-only" htmlFor="login-email">Email</label>
          <input
            id="login-email"
            className="login-input"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
          <label className="sr-only" htmlFor="login-password">Password</label>
          <input
            id="login-password"
            className="login-input"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
          {error && <div className="login-error">{error}</div>}
          <button type="submit" className="login-btn" disabled={submitting}>
            {submitting ? 'Verifying…' : 'Sign in'}
          </button>
        </form>

        <p className="login-hint">Default: admin@ultorn.local / admin123</p>
        <a href="/" className="login-back">← Back to home</a>
      </div>
    </div>
  )
}

function Page() {
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    setToken(localStorage.getItem('token'))
  }, [])
  const [user, setUser] = useState<any>(null)
  const [view, setView] = useState('dashboard')
  const [clients, setClients] = useState<any[]>([])
  const [scans, setScans] = useState<any[]>([])
  const [findings, setFindings] = useState<any[]>([])
  const [audit, setAudit] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ text: '', type: 'info' })

  useEffect(() => {
    if (token) {
      fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then((data) => setUser(data))
        .catch(() => {})
    }
  }, [token])

  const api = async (path: string, opts: any = {}) => {
    const res = await fetch(`${API_URL}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...opts.headers,
      },
      ...opts,
    })
    if (res.status === 401) {
      localStorage.removeItem('token')
      setToken(null)
      setView('login')
    }
    return res.json()
  }

  const notify = (text: string, type: string = 'info') => {
    setMessage({ text, type })
    setTimeout(() => setMessage({ text: '', type: 'info' }), 5000)
  }

  // ---------- LOGIN ----------
  if (!token) {
    return <LoginScreen onToken={(t: string) => { setToken(t); setView('dashboard') }} />
  }

  // ---------- MAIN LAYOUT ----------
  return (
    <div style={styles.app}>
      <nav style={styles.nav}>
        <div style={styles.navBrand}>
          <img src="/brand/utachi-logo-white.png" alt="Utachi Industries" style={styles.navBrandLogo} />
          <span style={styles.navBrandDivider} />
          <span style={styles.navBrandAccent}>Ultorn</span>
        </div>
        <div style={styles.navLinks}>
          <button
            onClick={() => setView('dashboard')}
            style={view === 'dashboard' ? { ...styles.navLink, ...styles.navActive } : styles.navLink}
          >
            Dashboard
          </button>
          <button
            onClick={() => setView('clients')}
            style={view === 'clients' ? { ...styles.navLink, ...styles.navActive } : styles.navLink}
          >
            Clients
          </button>
          <button
            onClick={() => setView('scans')}
            style={view === 'scans' ? { ...styles.navLink, ...styles.navActive } : styles.navLink}
          >
            Scans
          </button>
          <button
            onClick={() => setView('findings')}
            style={view === 'findings' ? { ...styles.navLink, ...styles.navActive } : styles.navLink}
          >
            Findings
          </button>
          <button
            onClick={() => setView('ai')}
            style={view === 'ai' ? { ...styles.navLink, ...styles.navActive } : styles.navLink}
          >
            AI Guard (Sovereign)
          </button>
          <button
            onClick={() => setView('audit')}
            style={view === 'audit' ? { ...styles.navLink, ...styles.navActive } : styles.navLink}
          >
            Audit Log
          </button>
          {user?.role === 'admin' && (
            <button
              onClick={() => setView('admin')}
              style={view === 'admin' ? { ...styles.navLink, ...styles.navActive } : styles.navLink}
            >
              Admin
            </button>
          )}
          <button
            onClick={() => {
              localStorage.removeItem('token')
              setToken(null)
              setView('login')
            }}
            style={{ ...styles.navLink, background: '#fee2e2', color: '#991b1b' }}
          >
            Sign out
          </button>
        </div>
      </nav>

      <main style={styles.main}>
        {message.text && (
          <div
            style={{
              ...styles.alert,
              background: message.type === 'error' ? '#fee2e2' : '#dbeafe',
              color: message.type === 'error' ? '#991b1b' : '#1e40af',
              border: message.type === 'error' ? '1px solid #fecaca' : '1px solid #bfdbfe',
            }}
          >
            {message.text}
          </div>
        )}

        {view === 'dashboard' && <Dashboard />}
        {view === 'clients' && <ClientsSection />}
        {view === 'scans' && <ScansSection />}
        {view === 'findings' && <FindingsSection />}
        {view === 'ai' && <AISection />}
        {view === 'audit' && <AuditSection />}
        {view === 'admin' && user?.role === 'admin' && <AdminSection />}
      </main>
    </div>
  )

  // ============================================================
  // DASHBOARD
  // ============================================================
  function Dashboard() {
    const [stats, setStats] = useState<any>({})

    useEffect(() => {
      api('/scans').then((data: any) => {
        setScans(data)
        const critical = data.reduce(
          (acc: number, s: any) => acc + (s.summary?.critical || 0),
          0
        )
        const high = data.reduce(
          (acc: number, s: any) => acc + (s.summary?.high || 0),
          0
        )
        setStats({ totalScans: data.length, critical, high })
      })
      api('/clients').then((data: any) => setClients(data))
      api('/audit').then((data: any) => setAudit(data.slice(0, 5)))
    }, [token])

    return (
      <div style={styles.section}>
        <h2 style={styles.h2}>Dashboard</h2>
        <div style={styles.statGrid}>
          <StatCard label="Total Scans" value={stats.totalScans || 0} color="#3b82f6" />
          <StatCard label="Critical Findings" value={stats.critical || 0} color="#ef4444" />
          <StatCard label="High Findings" value={stats.high || 0} color="#f59e0b" />
          <StatCard label="Clients" value={clients.length} color="#10b981" />
        </div>

        <div style={styles.sectionGrid}>
          <div style={styles.card}>
            <h3 style={styles.h3}>Recent Scans</h3>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th>Client</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Findings</th>
                </tr>
              </thead>
              <tbody>
                {(scans || []).slice(0, 5).map((s: any) => (
                  <tr key={s.id} style={styles.tableRow}>
                    <td>{s.client?.name || '—'}</td>
                    <td>{s.scan_type}</td>
                    <td
                      style={{
                        ...styles.tableCell,
                        color: s.status === 'completed' ? '#10b981' : '#f59e0b',
                      }}
                    >
                      {s.status}
                    </td>
                    <td>
                      {s.summary?.total_findings || 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={styles.card}>
            <h3 style={styles.h3}>Recent Audit Activity</h3>
            <ul style={styles.list}>
              {(audit || []).map((a: any) => (
                <li key={a.id} style={styles.listItem}>
                  <strong>{a.action}</strong>{' — '}
                  {a.resource_type} #{a.resource_id} <br />
                  <span style={{ color: '#6b7280', fontSize: '0.85rem' }}>
                    {new Date(a.created_at).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================
  // CLIENTS
  // ============================================================
  function ClientsSection() {
    const [newClient, setNewClient] = useState({ name: '', contact_email: '' })

    useEffect(() => {
      api('/clients').then((data: any) => setClients(data))
    }, [token])

    const createClient = async (e: any) => {
      e.preventDefault()
      await api('/clients', {
        method: 'POST',
        body: JSON.stringify(newClient),
      })
      setNewClient({ name: '', contact_email: '' })
      api('/clients').then((data: any) => setClients(data))
      notify('Client created')
    }

    return (
      <div style={styles.section}>
        <h2 style={styles.h2}>Clients</h2>
        <form onSubmit={createClient} style={styles.form}>
          <input
            placeholder="Client name"
            value={newClient.name}
            onChange={(e) => setNewClient({ ...newClient, name: e.target.value })}
            style={styles.input}
          />
          <input
            placeholder="Contact email"
            value={newClient.contact_email}
            onChange={(e) => setNewClient({ ...newClient, contact_email: e.target.value })}
            style={styles.input}
          />
          <button type="submit" style={styles.button}>Add Client</button>
        </form>

        <table style={styles.table}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((c: any) => (
              <tr key={c.id} style={styles.tableRow}>
                <td>{c.name}</td>
                <td>{c.contact_email || '—'}</td>
                <td>{c.is_active ? 'Active' : 'Inactive'}</td>
                <td>
                  <button
                    onClick={() => {
                      setView('scans')
                      notify(`Scopes for ${c.name}`)
                    }}
                    style={styles.buttonSmall}
                  >
                    Manage Scopes
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  // ============================================================
  // SCANS
  // ============================================================
  function ScansSection() {
    const [newScan, setNewScan] = useState({ client_id: '', scan_type: 'vulnerability' })

    useEffect(() => {
      api('/scans').then((data: any) => setScans(data))
      api('/clients').then((data: any) => setClients(data))
    }, [token])

    const startScan = async (e: any) => {
      e.preventDefault()
      await api('/scans', {
        method: 'POST',
        body: JSON.stringify({ client_id: parseInt(newScan.client_id), scan_type: newScan.scan_type }),
      })
      api('/scans').then((data: any) => setScans(data))
      notify('Scan started — runs on all scopes, no verification gate')
    }

    const runScan = async (id: number) => {
      const res = await api(`/scans/${id}/run`, { method: 'POST' })
      notify(res.status || 'Scan completed')
      api('/scans').then((data: any) => setScans(data))
    }

    return (
      <div style={styles.section}>
        <h2 style={styles.h2}>Security Assessments</h2>
        <p style={styles.hint}>
          No verification gate — scans run on all in-scope targets immediately.
          Full data extraction: banners, headers, page content, body.
        </p>

        <form onSubmit={startScan} style={{ ...styles.form, marginBottom: '1rem' }}>
          <select
            value={newScan.client_id}
            onChange={(e) => setNewScan({ ...newScan, client_id: e.target.value })}
            style={styles.input}
          >
            <option value="">Select client</option>
            {clients.map((c: any) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <select
            value={newScan.scan_type}
            onChange={(e) => setNewScan({ ...newScan, scan_type: e.target.value })}
            style={styles.input}
          >
            <option value="vulnerability">Vulnerability Assessment</option>
            <option value="code">AI Code Scan</option>
            <option value="monitoring">Continuous Monitoring</option>
          </select>
          <button type="submit" style={styles.button}>Start Scan</button>
        </form>

        <table style={styles.table}>
          <thead>
            <tr>
              <th>Client</th>
              <th>Type</th>
              <th>Status</th>
              <th>Critical</th>
              <th>High</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {scans.map((s: any) => {
              const summary = s.summary || {}
              return (
                <tr key={s.id} style={styles.tableRow}>
                  <td>{s.client?.name || '—'}</td>
                  <td>{s.scan_type}</td>
                  <td style={{ color: s.status === 'completed' ? '#10b981' : '#f59e0b' }}>
                    {s.status}
                  </td>
                  <td>{summary.critical || 0}</td>
                  <td>{summary.high || 0}</td>
                  <td>
                    {s.status !== 'running' && (
                      <button
                        onClick={() => runScan(s.id)}
                        style={styles.buttonSmall}
                      >
                        Run Scan
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    )
  }

  // ============================================================
  // FINDINGS
  // ============================================================
  function FindingsSection() {
    const [review, setReview] = useState({ findingId: '', status: 'open' })

    useEffect(() => {
      api('/scans').then((data: any) => {
        const allFindings = data.flatMap((s: any) => s.findings || [])
        setFindings(allFindings)
      })
    }, [token])

    const reviewFinding = async (e: any) => {
      e.preventDefault()
      await api(`/findings/${review.findingId}/review`, {
        method: 'POST',
        body: JSON.stringify({ status: review.status }),
      })
      notify('Finding reviewed — human analyst attested')
    }

    return (
      <div style={styles.section}>
        <h2 style={styles.h2}>Findings & Remediation</h2>
        <p style={styles.hint}>
          Critical and high findings require named human analyst review before
          remediation. No autonomous exploitation.
        </p>

        <table style={styles.table}>
          <thead>
            <tr>
              <th>Title</th>
              <th>Severity</th>
              <th>Target</th>
              <th>Status</th>
              <th>Reviewed By</th>
              <th>Evidence</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((f: any) => {
              const evidence = f.evidence ? JSON.parse(f.evidence) : {}
              return (
                <tr key={f.id} style={styles.tableRow}>
                  <td>{f.title}</td>
                  <td style={{ color: severityColor(f.severity), fontWeight: '600' }}>
                    {f.severity}
                  </td>
                  <td>{f.target}</td>
                  <td>{f.status}</td>
                  <td>{f.reviewed_by_user?.email || '—'}</td>
                  <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '0.8rem', color: '#6b7280' }}>
                    {JSON.stringify(evidence).slice(0, 100)}...
                  </td>
                  <td>
                    {f.severity === 'critical' || f.severity === 'high' ? (
                      <select
                        value={review.status}
                        onChange={(e) => setReview({ ...review, status: e.target.value })}
                        style={styles.inputSmall}
                      >
                        <option value="open">Open</option>
                        <option value="fixed">Fixed</option>
                        <option value="false_positive">False Positive</option>
                        <option value="acknowledged">Acknowledged</option>
                      </select>
                    ) : (
                      <span style={{ color: '#6b7280', fontSize: '0.85rem' }}>Auto-cleared</span>
                    )}
                  </td>
                  <td>
                    {(f.severity === 'critical' || f.severity === 'high') && (
                      <button
                        onClick={() => setReview({ findingId: f.id, status: review.status })}
                        style={styles.buttonSmall}
                      >
                        Submit Review
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        <div style={{ ...styles.card, marginTop: '1rem' }}>
          <h3 style={styles.h3}>Human Review Attestation</h3>
          <form onSubmit={reviewFinding} style={styles.form}>
            <input
              placeholder="Finding ID"
              value={review.findingId}
              onChange={(e) => setReview({ ...review, findingId: e.target.value })}
              style={styles.input}
            />
            <select
              value={review.status}
              onChange={(e) => setReview({ ...review, status: e.target.value })}
              style={styles.input}
            >
              <option value="open">Open</option>
              <option value="fixed">Fixed</option>
              <option value="false_positive">False Positive</option>
              <option value="acknowledged">Acknowledged</option>
            </select>
            <button type="submit" style={styles.button}>Attest Review</button>
          </form>
        </div>
      </div>
    )
  }

  function severityColor(s: string) {
    switch (s) {
      case 'critical': return '#dc2626'
      case 'high': return '#ea580c'
      case 'medium': return '#d97706'
      case 'low': return '#65a30d'
      default: return '#6b7280'
    }
  }

  // ============================================================
  // AI / SOVEREIGNTY
  // ============================================================
  function AISection() {
    const [prompt, setPrompt] = useState('')
    const [clientName, setClientName] = useState('')
    const [response, setResponse] = useState('')
    const [sanitized, setSanitized] = useState('')
    const [forceLocal, setForceLocal] = useState(false)

    const queryAI = async () => {
      const res = await api('/ai/query', {
        method: 'POST',
        body: JSON.stringify({ prompt, client_name: clientName || undefined, force_local: forceLocal }),
      })
      setResponse(res.response || 'No response')
    }

    const doSanitize = () => {
      fetch(`${API_URL}/sanitize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ text: prompt, client_name: clientName || undefined }),
      }).then((r) => r.json()).then((data: any) => setSanitized(data.sanitized || ''))
    }

    return (
      <div style={styles.section}>
        <h2 style={styles.h2}>AI Guard — Sovereignty Layer</h2>
        <p style={styles.hint}>
          Prompts are sanitized (client names, IPs, credentials, PII stripped)
          before reaching any external model. Sensitive data stays local.
          Every query is immutably logged.
        </p>

        <div style={styles.card}>
          <h3 style={styles.h3}>Send to AI</h3>
          <textarea
            placeholder="e.g. 'Analyze this vulnerability report for client Acme Corp at 10.0.0.5 with API key sk-12345'"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            style={styles.textarea}
            rows={4}
          />
          <div style={styles.formRow}>
            <input
              placeholder="Client name (will be redacted)"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              style={styles.input}
            />
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={forceLocal}
                onChange={(e) => setForceLocal(e.target.checked)}
              />
              Force local processing (no external model)
            </label>
          </div>
          <button onClick={queryAI} style={styles.button}>Query AI</button>
          <button onClick={doSanitize} style={styles.buttonSmall}>Preview Sanitization</button>
        </div>

        {response && (
          <div style={styles.card}>
            <h3 style={styles.h3}>AI Response</h3>
            <div style={styles.codeBlock}>{response}</div>
          </div>
        )}

        {sanitized && (
          <div style={styles.card}>
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
  function AuditSection() {
    useEffect(() => {
      api('/audit').then((data: any) => setAudit(data))
    }, [token])

    return (
      <div style={styles.section}>
        <h2 style={styles.h2}>Immutable Audit Log</h2>
        <p style={styles.hint}>
          Every action, scan, AI query, and review is logged. This log is the
          authoritative record for regulatory and client accountability.
        </p>

        <table style={styles.table}>
          <thead>
            <tr>
              <th>Action</th>
              <th>User</th>
              <th>Resource</th>
              <th>Details</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {audit.map((a: any) => (
              <tr key={a.id} style={styles.tableRow}>
                <td style={{ fontWeight: '600' }}>{a.action}</td>
                <td>{a.user_email || 'system'}</td>
                <td>{a.resource_type || '—'} #{a.resource_id || '—'}</td>
                <td style={{ fontSize: '0.85rem', color: '#6b7280' }}>{a.details || '—'}</td>
                <td style={{ fontSize: '0.85rem' }}>{new Date(a.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }
  // ============================================================
  // ADMIN — users & API keys
  // ============================================================
  function AdminSection() {
    const [users, setUsers] = useState<any[]>([])
    const [apiKeys, setApiKeys] = useState<any[]>([])
    const [newKeyName, setNewKeyName] = useState('')
    const [mintedKey, setMintedKey] = useState<string | null>(null)

    const loadUsers = () => api('/admin/users').then((data: any) => setUsers(Array.isArray(data) ? data : []))
    const loadKeys = () => api('/admin/api-keys').then((data: any) => setApiKeys(Array.isArray(data) ? data : []))

    useEffect(() => {
      loadUsers()
      loadKeys()
    }, [token])

    const changeRole = async (userId: number, role: string) => {
      await api(`/admin/users/${userId}`, {
        method: 'PATCH',
        body: JSON.stringify({ role }),
      })
      loadUsers()
      notify('User role updated')
    }

    const toggleActive = async (u: any) => {
      await api(`/admin/users/${u.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !u.is_active }),
      })
      loadUsers()
      notify(u.is_active ? 'User deactivated' : 'User reactivated')
    }

    const createKey = async (e: any) => {
      e.preventDefault()
      if (!newKeyName.trim()) return
      const created = await api('/admin/api-keys', {
        method: 'POST',
        body: JSON.stringify({ name: newKeyName }),
      })
      setMintedKey(created.api_key || null)
      setNewKeyName('')
      loadKeys()
      notify('API key created — copy it now, it will not be shown again')
    }

    const revokeKey = async (id: number) => {
      await api(`/admin/api-keys/${id}`, { method: 'DELETE' })
      loadKeys()
      notify('API key revoked')
    }

    return (
      <div style={styles.section}>
        <h2 style={styles.h2}>Admin</h2>
        <p style={styles.hint}>
          Manage platform users and programmatic API keys. Admin-only.
        </p>

        <div style={styles.card}>
          <h3 style={styles.h3}>Users</h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th>Email</th>
                <th>Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u: any) => (
                <tr key={u.id} style={styles.tableRow}>
                  <td>{u.email}</td>
                  <td>{u.full_name || '—'}</td>
                  <td>
                    <select
                      value={u.role}
                      onChange={(e) => changeRole(u.id, e.target.value)}
                      style={styles.inputSmall}
                    >
                      <option value="admin">Admin</option>
                      <option value="analyst">Analyst</option>
                      <option value="client">Client</option>
                    </select>
                  </td>
                  <td style={{ color: u.is_active ? '#10b981' : '#dc2626' }}>
                    {u.is_active ? 'Active' : 'Disabled'}
                  </td>
                  <td>
                    <button onClick={() => toggleActive(u)} style={styles.buttonSmall}>
                      {u.is_active ? 'Disable' : 'Enable'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ ...styles.card, marginTop: '1rem' }}>
          <h3 style={styles.h3}>API Keys</h3>
          <p style={styles.hint}>
            Keys authenticate programmatic access via the <code>X-API-Key</code> header,
            scoped to the admin account that minted them.
          </p>

          <form onSubmit={createKey} style={{ ...styles.form, flexDirection: 'row', gap: '0.5rem' }}>
            <input
              placeholder="Key name (e.g. ci-pipeline)"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              style={styles.input}
            />
            <button type="submit" style={styles.button}>Create Key</button>
          </form>

          {mintedKey && (
            <div style={{ ...styles.codeBlock, marginTop: '1rem' }}>
              {mintedKey}
              <div style={{ color: '#f59e0b', marginTop: '0.5rem', fontFamily: 'inherit' }}>
                Copy this now — it will not be shown again.
              </div>
            </div>
          )}

          <table style={styles.table}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Prefix</th>
                <th>Owner</th>
                <th>Status</th>
                <th>Last Used</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {apiKeys.map((k: any) => (
                <tr key={k.id} style={styles.tableRow}>
                  <td>{k.name}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{k.key_prefix}…</td>
                  <td>{k.owner_id}</td>
                  <td style={{ color: k.is_active ? '#10b981' : '#6b7280' }}>
                    {k.is_active ? 'Active' : 'Revoked'}
                  </td>
                  <td>{k.last_used_at ? new Date(k.last_used_at).toLocaleString() : 'Never'}</td>
                  <td>
                    {k.is_active && (
                      <button onClick={() => revokeKey(k.id)} style={styles.buttonSmall}>
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }
}

export default Page

// ============================================================
// Shared Components
// ============================================================
function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div
      style={{
        ...styles.statCard,
        borderTop: `4px solid ${color}`,
      }}
    >
      <div style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: '0.25rem' }}>
        {label}
      </div>
      <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#111827' }}>{value}</div>
    </div>
  )
}

// ============================================================
// Styles
// ============================================================
const styles: any = {
  page: {
    minHeight: '100vh',
    background: '#f3f4f6',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    background: '#ffffff',
    padding: '2rem',
    borderRadius: '12px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    margin: '1rem 0',
  },
  h1: { fontSize: '2.5rem', fontWeight: '800', margin: '0 0 0.5rem 0', color: '#111827' },
  sub: { color: '#6b7280', margin: '0 0 1.5rem 0' },
  form: { display: 'flex', flexDirection: 'column', gap: '0.75rem' },
  input: {
    padding: '0.6rem 0.9rem',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '0.95rem',
    width: '100%',
    boxSizing: 'border-box',
  },
  inputSmall: {
    padding: '0.4rem 0.6rem',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '0.9rem',
  },
  button: {
    background: '#111827',
    color: '#fff',
    border: 'none',
    padding: '0.7rem 1.5rem',
    borderRadius: '6px',
    fontWeight: '600',
    cursor: 'pointer',
    fontSize: '0.95rem',
  },
  buttonSmall: {
    background: '#111827',
    color: '#fff',
    border: 'none',
    padding: '0.35rem 0.8rem',
    borderRadius: '4px',
    fontWeight: '600',
    cursor: 'pointer',
    fontSize: '0.85rem',
    marginRight: '0.4rem',
  },
  hint: { color: '#6b7280', fontSize: '0.9rem', marginBottom: '1rem' },
  app: { display: 'flex', minHeight: '100vh' },
  nav: {
    background: '#111827',
    color: '#fff',
    padding: '1rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 100,
  },
  navBrand: { display: 'flex', alignItems: 'center', gap: '0.6rem' },
  navBrandLogo: { height: '30px', width: 'auto', display: 'block' },
  navBrandDivider: { width: '1px', height: '16px', background: 'rgba(255,255,255,0.22)' },
  navBrandAccent: { color: '#e5e7eb', fontWeight: '600', fontSize: '0.95rem' },
  navLinks: { display: 'flex', gap: '0.5rem' },
  navLink: {
    color: '#e5e7eb',
    background: 'transparent',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  navActive: { background: '#3b82f6', color: '#fff' },
  main: { flex: 1, padding: '80px 2rem 2rem 2rem', maxWidth: '1200px', margin: '0 auto', width: '100%', boxSizing: 'border-box' },
  section: {},
  h2: { fontSize: '1.5rem', fontWeight: '700', marginBottom: '1rem', color: '#111827' },
  h3: { fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#111827' },
  statGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' },
  statCard: { background: '#fff', padding: '1rem', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  sectionGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' },
  table: { width: '100%', borderCollapse: 'collapse', marginTop: '0.5rem' },
  tableRow: { borderBottom: '1px solid #e5e7eb' },
  tableCell: { padding: '0.75rem', textAlign: 'left' },
  list: { listStyle: 'none', padding: 0, margin: 0 },
  listItem: { padding: '0.5rem 0', borderBottom: '1px solid #f3f4f6' },
  alert: { padding: '0.75rem 1rem', borderRadius: '6px', marginBottom: '1rem', fontSize: '0.9rem' },
  codeBlock: {
    background: '#1f2937',
    color: '#10b981',
    padding: '1rem',
    borderRadius: '6px',
    fontFamily: 'monospace',
    fontSize: '0.85rem',
    overflowX: 'auto',
    whiteSpace: 'pre-wrap',
  },
  checkboxLabel: { display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#6b7280' },
  textarea: {
    padding: '0.6rem 0.9rem',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '0.95rem',
    width: '100%',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
  },
  formRow: { display: 'flex', gap: '0.5rem', marginTop: '0.5rem', alignItems: 'center' },
}
