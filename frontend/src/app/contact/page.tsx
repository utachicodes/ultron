import MarketingPageShell from '../../components/MarketingPageShell'
import { company, pageHeroes } from '../../content/site'

export const metadata = {
  title: 'Contact | ULTORN',
  description: 'Real contact channels for Ultorn, operated by Utachi Industries.',
}

export default function ContactPage() {
  const hero = pageHeroes.contact
  return (
    <MarketingPageShell current="/contact">
      <div className="page-hero">
        <div className="page-eyebrow">{hero.eyebrow}</div>
        <h1 className="page-title">{hero.title}</h1>
        <p className="page-lede">
          {hero.lede} Ultorn is operated by{' '}
          <a href={company.operator.url} target="_blank" rel="noreferrer">{company.operator.name}</a>,
          based in {company.operator.location}.
        </p>
      </div>

      <div className="page-body">
        <ul className="contact-grid">
          <li>
            <span>WhatsApp</span>
            <a href={company.contact.whatsapp.href} target="_blank" rel="noreferrer">
              {company.contact.whatsapp.label}
            </a>
          </li>
          <li>
            <span>Instagram</span>
            <a href={company.contact.instagram.href} target="_blank" rel="noreferrer">
              {company.contact.instagram.label}
            </a>
          </li>
          <li>
            <span>Platform admin</span>
            <a href={company.contact.email.href}>{company.contact.email.label}</a>
          </li>
        </ul>
        <a href="/" className="back-link">← Back to home</a>
      </div>
    </MarketingPageShell>
  )
}
