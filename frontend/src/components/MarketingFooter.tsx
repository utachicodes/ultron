import { legalLinks } from '../content/site'

export default function MarketingFooter() {
  return (
    <footer className="mfooter">
      Opening an Ultorn account signals that you accept our{' '}
      <a href={legalLinks.privacy.href}>{legalLinks.privacy.label}</a> and{' '}
      <a href={legalLinks.service.href}>{legalLinks.service.label}</a>.
    </footer>
  )
}
