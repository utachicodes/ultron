import MarketingPageShell from '../../components/MarketingPageShell'
import { pageHeroes, scanningCapabilities } from '../../content/site'

export const metadata = {
  title: 'Scanning — ULTORN',
  description: 'What Ultorn’s scan engine does: Nuclei, Nmap, and HTTP evidence extraction.',
}

export default function ScanningPage() {
  const hero = pageHeroes.scanning
  return (
    <MarketingPageShell current="/scanning">
      <div className="page-hero">
        <div className="page-eyebrow">{hero.eyebrow}</div>
        <h1 className="page-title">{hero.title}</h1>
        <p className="page-lede">{hero.lede}</p>
      </div>

      <div className="page-body">
        <ul className="feature-grid">
          {scanningCapabilities.map((f) => (
            <li key={f.title}>
              <h2>{f.title}</h2>
              <p>{f.body}</p>
            </li>
          ))}
        </ul>
        <a href="/" className="back-link">← Back to home</a>
      </div>
    </MarketingPageShell>
  )
}
