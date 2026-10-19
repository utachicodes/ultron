import MarketingPageShell from '../../components/MarketingPageShell'
import { pageHeroes, platformFeatures } from '../../content/site'

export const metadata = {
  title: 'Platform | ULTORN',
  description: 'What the Ultorn platform actually does: onboarding, scopes, findings, audit, and admin controls.',
}

export default function PlatformPage() {
  const hero = pageHeroes.platform
  return (
    <MarketingPageShell current="/platform">
      <div className="page-hero">
        <div className="page-eyebrow">{hero.eyebrow}</div>
        <h1 className="page-title">{hero.title}</h1>
        <p className="page-lede">{hero.lede}</p>
      </div>

      <div className="page-body">
        <ul className="feature-grid">
          {platformFeatures.map((f) => (
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
