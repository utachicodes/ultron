'use client'

import { useState } from 'react'
import { navLinks } from '../content/site'
import Arrow from './Arrow'

export default function MarketingNav({ current }: { current?: string }) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <nav className="mnav">
        <a href="/" className="mlogo">
          <img src="/brand/utachi-logo-white.png" alt="Utachi Industries" />
          <span className="mlogo-divider" />
          <span className="mlogo-product">Ultorn</span>
        </a>

        <div className="mnav-links" aria-label="Primary">
          {navLinks.map((l) => (
            <a key={l.href} href={l.href} aria-current={current === l.href ? 'page' : undefined}>
              {l.label}
            </a>
          ))}
        </div>

        <div className="mnav-actions">
          <a href="/console" className="mbtn mbtn-login">Login</a>
          <a href="/console" className="mbtn mbtn-start">
            Get Started <Arrow />
          </a>
        </div>

        <button
          className="mburger"
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
          aria-controls="mobile-menu"
          onClick={() => setOpen((v) => !v)}
        >
          <span />
        </button>
      </nav>

      <div id="mobile-menu" className={`mmenu${open ? ' open' : ''}`} aria-label="Mobile">
        {navLinks.map((l) => (
          <a key={l.href} href={l.href} onClick={() => setOpen(false)}>{l.label}</a>
        ))}
        <div className="mdivider" />
        <a href="/console" onClick={() => setOpen(false)}>Login</a>
        <a href="/console" className="mstart" onClick={() => setOpen(false)}>
          Get Started <Arrow />
        </a>
      </div>
    </>
  )
}
