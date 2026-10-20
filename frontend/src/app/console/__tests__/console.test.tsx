import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Page from '../page'

function mockFetchSequence(impl: (url: string, opts?: RequestInit) => Promise<any>) {
  global.fetch = jest.fn(impl) as unknown as typeof fetch
}

function jsonResponse(body: any, ok = true, status = 200) {
  return {
    ok,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as Response
}

describe('Console auth gate (smoke)', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.restoreAllMocks()
  })

  it('renders the login screen when no token is in localStorage', () => {
    render(<Page />)

    expect(screen.getByText(/sign in to the operator console/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()

    // Authenticated-only content must not be present.
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
    expect(screen.queryByRole('navigation', { name: /overview navigation/i })).not.toBeInTheDocument()
  })

  it('shows email and password inputs on the login form', () => {
    render(<Page />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('does not crash when submitting the login form with empty fields', async () => {
    mockFetchSequence(async () => jsonResponse({ detail: 'Invalid credentials' }, false, 401))

    const user = userEvent.setup()
    render(<Page />)

    const submit = screen.getByRole('button', { name: /sign in/i })
    await user.click(submit)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })

    // Still on the login screen, no crash.
    expect(screen.getByText(/sign in to the operator console/i)).toBeInTheDocument()
  })

  it('renders the authenticated console shell after a successful login', async () => {
    mockFetchSequence(async (url: any) => {
      const u = String(url)
      if (u.includes('/auth/token')) {
        return jsonResponse({ access_token: 'fake-token' })
      }
      if (u.includes('/auth/me')) {
        return jsonResponse({ id: 1, email: 'operator@example.com', role: 'analyst' })
      }
      // Dashboard data loads (scans, clients, audit, alerts, monitors, code-scans).
      return jsonResponse([])
    })

    const user = userEvent.setup()
    render(<Page />)

    await user.type(screen.getByLabelText(/email/i), 'operator@example.com')
    await user.type(screen.getByLabelText(/password/i), 'supersecret')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('operator@example.com')).toBeInTheDocument()
    })

    // The sidebar nav and dashboard heading confirm the authenticated shell rendered.
    expect(screen.getByRole('navigation', { name: /overview navigation/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
    expect(screen.queryByText(/sign in to the operator console/i)).not.toBeInTheDocument()

    expect(localStorage.getItem('token')).toBe('fake-token')
  })
})
