import MarketingPageShell from '../../components/MarketingPageShell'
import { serviceAgreement } from '../../content/site'

export const metadata = {
  title: 'Service Agreement — ULTORN',
  description: 'A plain-language description of how the Ultorn platform is intended to be used.',
}

export default function ServiceAgreementPage() {
  return (
    <MarketingPageShell current="/service-agreement">
      <div className="page-hero">
        <div className="page-eyebrow">Service Agreement</div>
        <h1 className="page-title">The terms of the deal.</h1>
        <div className="page-updated">Last reviewed {serviceAgreement.updated}</div>
      </div>

      <div className="page-body">
        <div className="legal-doc">
          {serviceAgreement.sections.map((s) => (
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
