import MarketingPageShell from '../../components/MarketingPageShell'
import { privacyNotice } from '../../content/site'

export const metadata = {
  title: 'Privacy Notice — ULTORN',
  description: 'A plain-language description of what Ultorn actually stores and does with data.',
}

export default function PrivacyNoticePage() {
  return (
    <MarketingPageShell current="/privacy-notice">
      <div className="page-hero">
        <div className="page-eyebrow">Privacy Notice</div>
        <h1 className="page-title">What we do with your data.</h1>
        <div className="page-updated">Last reviewed {privacyNotice.updated}</div>
      </div>

      <div className="page-body">
        <div className="legal-doc">
          {privacyNotice.sections.map((s) => (
            <div key={s.heading}>
              <h2>{s.heading}</h2>
              <p>{s.body}</p>
            </div>
          ))}
        </div>
        <a href="/" className="back-link">← Back to home</a>
      </div>
    </MarketingPageShell>
  )
}
