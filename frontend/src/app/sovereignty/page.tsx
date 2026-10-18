import MarketingPageShell from '../../components/MarketingPageShell'
import { pageHeroes, sovereigntyPrinciples } from '../../content/site'

export const metadata = {
  title: 'Sovereignty — ULTORN',
  description: 'How Ultorn’s AI sovereignty layer sanitizes, routes, and audits every AI query.',
}

export default function SovereigntyPage() {
  const hero = pageHeroes.sovereignty
  return (
    <MarketingPageShell current="/sovereignty">
      <div className="page-hero">
        <div className="page-eyebrow">{hero.eyebrow}</div>
        <h1 className="page-title">{hero.title}</h1>
        <p className="page-lede">{hero.lede}</p>
      </div>

      <div className="page-body">
        <ul className="feature-grid">
          {sovereigntyPrinciples.map((f) => (
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
