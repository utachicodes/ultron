import './globals.css'

export const metadata = {
  title: 'ULTORN | Your sovereign shield for the African security network',
  description: 'West African-owned cybersecurity and digital-trust infrastructure, by Utachi Industries.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
