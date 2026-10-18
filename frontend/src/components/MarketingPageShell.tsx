import '../app/marketing-page.css'
import MarketingNav from './MarketingNav'
import MarketingFooter from './MarketingFooter'

export default function MarketingPageShell({
  current,
  children,
}: {
  current?: string
  children: React.ReactNode
}) {
  return (
    <div className="mpage">
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;800&display=swap"
        rel="stylesheet"
      />
      <MarketingNav current={current} />
      {children}
      <MarketingFooter />
    </div>
  )
}
