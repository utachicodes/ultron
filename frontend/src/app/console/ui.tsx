'use client'

/**
 * Shared console UI primitives.
 *
 * Every control pairs a visible <label> with its input (WCAG 3.3.2), exposes
 * busy/error state to assistive tech, and uses the same spacing and focus
 * treatment so the console behaves consistently (Jakob's Law).
 */

import React, { useEffect, useRef } from 'react'

const ACCENT = '#7c3aed'

const S = {
  field: { display: 'flex', flexDirection: 'column' as const, gap: '0.35rem', marginBottom: '0.9rem' },
  label: { fontSize: '0.78rem', fontWeight: 600, color: 'rgba(17,17,19,0.72)', letterSpacing: '0.01em' },
  required: { color: '#b91c1c', marginLeft: '0.15rem' },
  hint: { fontSize: '0.75rem', color: 'rgba(17,17,19,0.62)' },
  error: { fontSize: '0.75rem', color: '#b91c1c' },
  control: {
    width: '100%',
    padding: '0.65rem 0.8rem',
    borderRadius: '10px',
    border: '1px solid rgba(0,0,0,0.14)',
    background: '#fff',
    color: '#111113',
    fontSize: '0.9rem',
    minHeight: 44,
    outline: 'none',
  },
  controlError: { borderColor: '#dc2626' },
  button: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.45rem',
    padding: '0.6rem 1rem',
    borderRadius: '10px',
    border: '1px solid transparent',
    fontSize: '0.875rem',
    fontWeight: 600,
    cursor: 'pointer',
    minHeight: 40,
    transition: 'background-color 120ms ease, border-color 120ms ease, opacity 120ms ease',
  },
  primary: { background: ACCENT, color: '#fff' },
  secondary: { background: 'rgba(17,17,19,0.06)', color: '#111113', borderColor: 'rgba(17,17,19,0.12)' },
  ghost: { background: 'transparent', color: '#4c1d95', borderColor: 'rgba(124,58,237,0.35)' },
  danger: { background: '#b91c1c', color: '#fff' },
  disabled: { opacity: 0.55, cursor: 'not-allowed' },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.25rem',
    padding: '0.15rem 0.5rem',
    borderRadius: 999,
    fontSize: '0.72rem',
    fontWeight: 700,
    letterSpacing: '0.02em',
    textTransform: 'uppercase' as const,
    whiteSpace: 'nowrap' as const,
  },
  empty: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center' as const,
    gap: '0.4rem',
    padding: '2.5rem 1rem',
    color: 'rgba(17,17,19,0.62)',
  },
  spinner: {
    width: 16,
    height: 16,
    borderRadius: '50%',
    border: '2px solid rgba(255,255,255,0.35)',
    borderTopColor: '#fff',
    animation: 'ultorn-spin 700ms linear infinite',
  },
}

const TONES: Record<string, React.CSSProperties> = {
  critical: { background: 'rgba(185,28,28,0.12)', color: '#991b1b' },
  high: { background: 'rgba(194,65,12,0.12)', color: '#9a3412' },
  medium: { background: 'rgba(161,98,7,0.14)', color: '#854d0e' },
  low: { background: 'rgba(21,128,61,0.12)', color: '#166534' },
  success: { background: 'rgba(21,128,61,0.12)', color: '#166534' },
  warning: { background: 'rgba(161,98,7,0.14)', color: '#854d0e' },
  danger: { background: 'rgba(185,28,28,0.12)', color: '#991b1b' },
  neutral: { background: 'rgba(17,17,19,0.07)', color: 'rgba(17,17,19,0.72)' },
  info: { background: 'rgba(124,58,237,0.12)', color: '#5b21b6' },
}

export function Badge({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: string }) {
  return <span style={{ ...S.badge, ...(TONES[tone] || TONES.neutral) }}>{children}</span>
}

export function Field({
  label,
  htmlFor,
  hint,
  error,
  required,
  tone = 'light',
  children,
}: {
  label: string
  htmlFor: string
  hint?: string
  error?: string
  required?: boolean
  tone?: 'light' | 'dark'
  children: React.ReactNode
}) {
  const dark = tone === 'dark'
  const describedBy = [hint ? `${htmlFor}-hint` : null, error ? `${htmlFor}-error` : null]
    .filter(Boolean)
    .join(' ')
  return (
    <div style={S.field}>
      <label htmlFor={htmlFor} style={{ ...S.label, ...(dark ? { color: 'rgba(255,255,255,0.82)' } : {}) }}>
        {label}
        {required && (
          <span style={{ ...S.required, ...(dark ? { color: '#fca5a5' } : {}) }} aria-hidden="true">
            *
          </span>
        )}
      </label>
      {React.isValidElement(children)
        ? React.cloneElement(children as React.ReactElement<any>, {
            id: htmlFor,
            tone,
            'aria-describedby': describedBy || undefined,
            'aria-invalid': error ? true : undefined,
            'aria-required': required || undefined,
          })
        : children}
      {hint && (
        <span id={`${htmlFor}-hint`} style={{ ...S.hint, ...(dark ? { color: 'rgba(255,255,255,0.62)' } : {}) }}>
          {hint}
        </span>
      )}
      {error && (
        <span id={`${htmlFor}-error`} style={{ ...S.error, ...(dark ? { color: '#fca5a5' } : {}) }} role="alert">
          {error}
        </span>
      )}
    </div>
  )
}

const DARK_CONTROL: React.CSSProperties = {
  background: 'rgba(255,255,255,0.07)',
  border: '1px solid rgba(255,255,255,0.18)',
  color: '#f5f5f7',
}

function controlStyle(tone: 'light' | 'dark', invalid?: boolean, style?: React.CSSProperties): React.CSSProperties {
  return {
    ...S.control,
    ...(tone === 'dark' ? DARK_CONTROL : {}),
    ...(invalid ? S.controlError : {}),
    ...style,
  }
}

export function TextInput({
  invalid,
  tone = 'light',
  style,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean; tone?: 'light' | 'dark' }) {
  return <input {...props} style={controlStyle(tone, invalid, style)} />
}

export function Select({
  invalid,
  tone = 'light',
  style,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { invalid?: boolean; tone?: 'light' | 'dark' }) {
  return (
    <select {...props} style={controlStyle(tone, invalid, style)}>
      {children}
    </select>
  )
}

export function Textarea({
  invalid,
  tone = 'light',
  style,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean; tone?: 'light' | 'dark' }) {
  return <textarea {...props} style={controlStyle(tone, invalid, style)} />
}

export const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
    loading?: boolean
  }
>(function Button(
  { variant = 'primary', loading = false, children, disabled, style, type = 'button', ...props },
  ref
) {
  const isDisabled = disabled || loading
  return (
    <button
      {...props}
      ref={ref}
      type={type}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      style={{
        ...S.button,
        ...S[variant],
        ...(isDisabled ? S.disabled : {}),
        ...style,
      }}
    >
      {loading && <span style={S.spinner} aria-hidden="true" />}
      {loading ? 'Working…' : children}
    </button>
  )
})

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: React.ReactNode
}) {
  return (
    <div style={S.empty}>
      <strong style={{ color: 'rgba(17,17,19,0.8)' }}>{title}</strong>
      {description && <span style={{ fontSize: '0.85rem', maxWidth: 420 }}>{description}</span>}
      {action}
    </div>
  )
}

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" style={{ ...S.empty, flexDirection: 'row', padding: '1.5rem' }}>
      <span style={{ ...S.spinner, borderColor: 'rgba(124,58,237,0.25)', borderTopColor: ACCENT }} />
      <span style={{ fontSize: '0.85rem' }}>{label}…</span>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" style={{ ...S.empty, color: '#991b1b' }}>
      <strong>Something went wrong</strong>
      <span style={{ fontSize: '0.85rem', maxWidth: 480 }}>{message}</span>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  )
}

export function Toast({
  message,
  tone = 'info',
  onDismiss,
}: {
  message: string
  tone?: 'info' | 'error' | 'success'
  onDismiss: () => void
}) {
  const bg =
    tone === 'error' ? 'rgba(220,38,38,0.1)' : tone === 'success' ? 'rgba(21,128,61,0.1)' : 'rgba(124,58,237,0.1)'
  const color = tone === 'error' ? '#b91c1c' : tone === 'success' ? '#166534' : '#5b21b6'
  const border =
    tone === 'error' ? 'rgba(220,38,38,0.3)' : tone === 'success' ? 'rgba(21,128,61,0.3)' : 'rgba(124,58,237,0.3)'

  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      aria-live={tone === 'error' ? 'assertive' : 'polite'}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        background: bg,
        color,
        border: `1px solid ${border}`,
        borderRadius: 10,
        padding: '0.7rem 0.9rem',
        marginBottom: '1rem',
        fontSize: '0.87rem',
        fontWeight: 500,
      }}
    >
      <span>{message}</span>
      <button
        onClick={onDismiss}
        aria-label="Dismiss notification"
        style={{ background: 'none', border: 'none', color, cursor: 'pointer', fontSize: '1rem', lineHeight: 1 }}
      >
        ×
      </button>
    </div>
  )
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  tone = 'danger',
  onConfirm,
  onCancel,
}: {
  open: boolean
  title: string
  description: string
  confirmLabel?: string
  tone?: 'danger' | 'primary'
  onConfirm: () => void
  onCancel: () => void
}) {
  const cancelRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)
  const onCancelRef = useRef(onCancel)
  onCancelRef.current = onCancel
  const titleId = React.useId()
  const descId = React.useId()

  useEffect(() => {
    if (!open) return
    const previous = document.activeElement as HTMLElement | null
    cancelRef.current?.focus()
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onCancelRef.current()
        return
      }
      if (e.key !== 'Tab' || !dialogRef.current) return
      const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = previousOverflow
      previous?.focus?.()
    }
  }, [open])

  if (!open) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 300,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
        background: 'rgba(8,8,12,0.55)',
        backdropFilter: 'blur(4px)',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel()
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        style={{
          width: '100%',
          maxWidth: 420,
          background: '#fff',
          borderRadius: 18,
          padding: '1.5rem',
          boxShadow: '0 24px 80px rgba(0,0,0,0.35)',
        }}
      >
        <h2 id={titleId} style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem', color: '#111113' }}>
          {title}
        </h2>
        <p id={descId} style={{ fontSize: '0.9rem', color: 'rgba(17,17,19,0.65)', marginBottom: '1.25rem' }}>
          {description}
        </p>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
          <Button ref={cancelRef} variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant={tone} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
