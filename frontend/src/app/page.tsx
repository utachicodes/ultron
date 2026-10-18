'use client'

import { useEffect } from 'react'
import Script from 'next/script'
import './hero.css'
import { legalLinks, navLinks as NAV_LINKS } from '../content/site'
import Arrow from '../components/Arrow'

// Served from public/media — downloaded and re-compressed locally
// (37MB -> 2.2MB via ffmpeg) to avoid cross-origin latency and double-fetch lag.
const BG_VIDEO_URL: string | null = '/media/globe.mp4'
const BG_POSTER_URL: string | null = '/media/globe-poster.webp'

const ARROW = <Arrow className="arw" />

// Section 10A — arms synchronously, before paint, so there is no flash of
// unanimated content. Runs once, then fully detaches (removes its own classes).
const ENTRANCE_SCRIPT = `
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var html = document.documentElement;
  html.classList.add('hanim');
  var booted = false, bootTimer = null;
  function boot() {
    if (booted) return; booted = true;
    bootTimer = setTimeout(start, 900);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(start, start);
    } else {
      start();
    }
  }
  var started = false;
  function start() {
    if (started) return; started = true;
    if (bootTimer) clearTimeout(bootTimer);
    document.addEventListener('animationend', onEnd, true);
    setTimeout(clean, 2600);
    html.classList.add('hgo');
  }
  function onEnd(e) {
    if (e.animationName === 'pillIn' && e.target.classList && e.target.classList.contains('btn-ghost')) {
      clean();
    }
  }
  var cleaned = false;
  function clean() {
    if (cleaned) return; cleaned = true;
    document.removeEventListener('animationend', onEnd, true);
    html.classList.remove('hanim', 'hgo');
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
`

// Section 10B — mobile menu toggle, operating on the elements by id.
const BURGER_SCRIPT = `
(function () {
  var burger = document.getElementById('burger');
  var menu = document.getElementById('menu');
  if (!burger || !menu) return;
  function set(open) {
    menu.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  }
  burger.addEventListener('click', function (e) {
    e.stopPropagation();
    set(!menu.classList.contains('open'));
  });
  menu.addEventListener('click', function (e) {
    if (e.target.closest('a')) set(false);
  });
  document.addEventListener('click', function (e) {
    if (!menu.classList.contains('open')) return;
    if (menu.contains(e.target) || burger.contains(e.target)) return;
    set(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && menu.classList.contains('open')) {
      set(false);
      burger.focus();
    }
  });
})();
`

// Original canvas-rendered rotating dot-matrix globe — used in place of the
// spec's hosted video (that asset belongs to a different product). No image
// or video dependency: every dot, arc, and the orbiting satellite are drawn
// from geometry each frame. Renders a single static frame under
// prefers-reduced-motion instead of looping.
const GLOBE_SCRIPT = `
(function () {
  var canvas = document.getElementById('globeCanvas');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  if (!ctx) return;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var w = 0, h = 0;
  function resize() {
    var rect = canvas.getBoundingClientRect();
    w = rect.width; h = rect.height;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener('resize', resize);

  // Starfield — fixed, generated once.
  var stars = [];
  for (var i = 0; i < 180; i++) {
    stars.push({
      x: Math.random(),
      y: Math.random(),
      r: Math.random() * 1.1 + 0.2,
      a: Math.random() * 0.6 + 0.25,
    });
  }

  // Sphere point cloud (lat/lon grid projected to 3D).
  var pts = [];
  var LAT_STEPS = 22, LON_STEPS = 40;
  for (var la = 0; la <= LAT_STEPS; la++) {
    var theta = (la / LAT_STEPS) * Math.PI;
    for (var lo = 0; lo < LON_STEPS; lo++) {
      var phi = (lo / LON_STEPS) * Math.PI * 2;
      pts.push({
        x: Math.sin(theta) * Math.cos(phi),
        y: Math.cos(theta),
        z: Math.sin(theta) * Math.sin(phi),
      });
    }
  }

  var angle = 0;
  var satelliteAngle = 0;
  var t0 = null;

  function frame(now) {
    if (t0 === null) t0 = now;
    var elapsed = (now - t0) / 1000;

    var cx = w * 0.5, cy = h * 0.46;
    var radius = Math.min(w, h) * 0.3;

    ctx.clearRect(0, 0, w, h);

    // Starfield
    for (var i = 0; i < stars.length; i++) {
      var s = stars[i];
      ctx.beginPath();
      ctx.arc(s.x * w, s.y * h, s.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,' + s.a + ')';
      ctx.fill();
    }

    // Breathing rim glow behind the globe
    var pulse = reduced ? 0.5 : 0.5 + 0.5 * Math.sin(elapsed * 0.6);
    var glow = ctx.createRadialGradient(cx, cy, radius * 0.6, cx, cy, radius * 1.45);
    glow.addColorStop(0, 'rgba(139,92,246,' + (0.22 + 0.1 * pulse) + ')');
    glow.addColorStop(1, 'rgba(139,92,246,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, w, h);

    // Sphere dots — rotate right-to-left (decreasing x over time), depth-shaded.
    var cos = Math.cos(angle), sin = Math.sin(angle);
    for (var j = 0; j < pts.length; j++) {
      var p = pts[j];
      var rx = p.x * cos - p.z * sin;
      var rz = p.x * sin + p.z * cos;
      if (rz < -0.08) continue; // cull the far hemisphere for a wireframe feel
      var depth = (rz + 1) / 2;
      var px = cx + rx * radius;
      var py = cy - p.y * radius;
      var size = 0.6 + depth * 1.6;
      var alpha = 0.18 + depth * 0.62;
      ctx.beginPath();
      ctx.arc(px, py, size, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(167,139,250,' + alpha + ')';
      ctx.fill();
    }

    // Orbiting satellite
    var orbitR = radius * 1.22;
    var sx = cx + Math.cos(satelliteAngle) * orbitR;
    var sy = cy + Math.sin(satelliteAngle) * orbitR * 0.38;
    ctx.beginPath();
    ctx.arc(sx, sy, 2.4, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(224,214,255,0.95)';
    ctx.shadowColor = 'rgba(167,139,250,0.9)';
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Pulsing light arc tracing the rim
    var arcPulse = reduced ? 0.4 : 0.25 + 0.35 * (0.5 + 0.5 * Math.sin(elapsed * 0.9 + 1.2));
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 1.02, -0.9, 0.9);
    ctx.strokeStyle = 'rgba(196,181,253,' + arcPulse + ')';
    ctx.lineWidth = 1.2;
    ctx.stroke();

    if (!reduced) {
      angle -= 0.0016;
      satelliteAngle += 0.006;
      requestAnimationFrame(frame);
    }
  }

  requestAnimationFrame(frame);
})();
`

// Section 10C — two-video crossfade loop. Bails cleanly if there's no video
// (BG_VIDEO_URL is null), since the elements won't exist in the DOM at all.
const VIDEO_SCRIPT = `
(function () {
  var A = document.getElementById('bgVideoA');
  var B = document.getElementById('bgVideoB');
  if (!A || !B) return;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced) {
    A.removeAttribute('autoplay');
    try { B.pause(); A.pause(); A.currentTime = 0; } catch (e) {}
    return;
  }
  var FADE = 0.9, cur = A, nxt = B, swapping = false;
  function play(v) {
    var p = v.play();
    if (p && p.catch) p.catch(function () {});
  }
  play(A);
  function tick() {
    if (swapping || !cur.duration) return;
    if (cur.duration - cur.currentTime > FADE) return;
    swapping = true;
    var out = cur;
    nxt.currentTime = 0;
    play(nxt);
    nxt.classList.add('is-active');
    out.classList.remove('is-active');
    var tmp = cur; cur = nxt; nxt = tmp;
    setTimeout(function () {
      out.pause();
      out.currentTime = 0;
      swapping = false;
    }, FADE * 1000 + 100);
  }
  A.addEventListener('timeupdate', tick);
  B.addEventListener('timeupdate', tick);
})();
`

export default function LandingPage() {
  useEffect(() => {
    document.documentElement.classList.add('hero-locked')
    return () => document.documentElement.classList.remove('hero-locked')
  }, [])

  return (
    <>
      <Script id="hero-entrance" strategy="beforeInteractive">
        {ENTRANCE_SCRIPT}
      </Script>

      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;800&display=block"
        rel="stylesheet"
      />

      <main className="hero">
        <div
          className="bg"
          role="img"
          aria-label="Stylised violet dot-matrix globe against a starfield, slowly rotating"
        >
          {BG_VIDEO_URL ? (
            <>
              <video
                className="bg-video is-active"
                id="bgVideoA"
                autoPlay
                muted
                loop
                playsInline
                preload="auto"
                disablePictureInPicture
                aria-hidden="true"
                poster={BG_POSTER_URL || undefined}
              >
                <source src={BG_VIDEO_URL} type="video/mp4" />
              </video>
              <video
                className="bg-video"
                id="bgVideoB"
                muted
                loop
                playsInline
                preload="auto"
                disablePictureInPicture
                aria-hidden="true"
                poster={BG_POSTER_URL || undefined}
              >
                <source src={BG_VIDEO_URL} type="video/mp4" />
              </video>
            </>
          ) : (
            <>
              <div className="bg-fallback" />
              <canvas id="globeCanvas" className="globe-canvas" aria-hidden="true" />
            </>
          )}
          <div className="bg-scrim" />
        </div>

        <header className="nav">
          <a href="/" className="logo">
            <img src="/brand/utachi-logo-white.png" alt="Utachi Industries" />
            <span className="logo-divider" />
            <span className="logo-product">Ultorn</span>
          </a>

          <nav className="nav-links" aria-label="Primary">
            {NAV_LINKS.map((l) => (
              <a key={l.href} href={l.href}>{l.label}</a>
            ))}
          </nav>

          <div className="nav-actions">
            <a href="/console" className="btn btn-login">Login</a>
            <a href="/console" className="btn btn-nav-start">
              Get Started {ARROW}
            </a>
          </div>

          <button
            id="burger"
            className="burger"
            aria-label="Open menu"
            aria-expanded="false"
            aria-controls="menu"
          >
            <span />
          </button>
        </header>

        <nav className="menu" id="menu" aria-label="Mobile">
          {NAV_LINKS.filter((l) => l.href !== '/contact').map((l) => (
            <a key={l.href} href={l.href}>{l.label}</a>
          ))}
          <div className="divider" />
          <a href="/console">Login</a>
        </nav>

        <div className="hero-inner">
          <h1 className="hero-h1">
            <span className="ln"><span className="ln-i">Know before</span></span>
            <span className="ln"><span className="ln-i">they do.</span></span>
          </h1>
          <p className="sub">
            Every scan is evidence.<br />
            Every finding has a name behind it.<br />
            Every byte stays exactly where it belongs.
          </p>
          <div className="ctas">
            <a href="/console" className="btn btn-lg btn-primary">
              Get Started {ARROW}
            </a>
            <a href="/contact" className="btn btn-lg btn-ghost">
              Contact us {ARROW}
            </a>
          </div>
        </div>

        <div className="hero-legal">
          Built by Utachi Industries ·{' '}
          <a href={legalLinks.privacy.href}>{legalLinks.privacy.label}</a> ·{' '}
          <a href={legalLinks.service.href}>{legalLinks.service.label}</a>
        </div>
      </main>

      <Script id="hero-burger" strategy="afterInteractive">
        {BURGER_SCRIPT}
      </Script>
      {BG_VIDEO_URL ? (
        <Script id="hero-video" strategy="afterInteractive">
          {VIDEO_SCRIPT}
        </Script>
      ) : (
        <Script id="hero-globe" strategy="afterInteractive">
          {GLOBE_SCRIPT}
        </Script>
      )}
    </>
  )
}
