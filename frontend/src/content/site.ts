// Central source of truth for marketing-site copy and links.
// Every page (landing + subpages) reads from here so nothing drifts or duplicates.

export const company = {
  name: 'Ultorn',
  legalName: 'Ultorn, a Utachi Industries Labs product',
  tagline: 'Sovereign cybersecurity for the continent that built it.',
  operator: {
    name: 'Utachi Industries',
    url: 'https://www.utachiindustries.space/',
    location: 'Dakar, Senegal',
  },
  contact: {
    whatsapp: { label: '+221 78 108 05 06', href: 'https://wa.me/221781080506' },
    instagram: { label: '@utachiindustries', href: 'https://instagram.com/utachiindustries' },
    email: { label: 'admin@ultorn.local', href: 'mailto:admin@ultorn.local' },
  },
}

export const navLinks = [
  { label: 'Platform', href: '/platform' },
  { label: 'Scanning', href: '/scanning' },
  { label: 'Sovereignty', href: '/sovereignty' },
  { label: 'Contact', href: '/contact' },
]

export const legalLinks = {
  privacy: { label: 'Privacy Notice', href: '/privacy-notice' },
  service: { label: 'Service Agreement', href: '/service-agreement' },
}

// ------------------------------------------------------------------
// Per-page hero copy — eyebrow / title / lede, Palantir-register:
// short, declarative, confident. No filler adjectives.
// ------------------------------------------------------------------
export const pageHeroes = {
  platform: {
    eyebrow: 'Platform',
    title: 'Operations, not spreadsheets.',
    lede: 'One system of record for every client, every scope, every finding. Built for operators who answer for what they ship.',
  },
  scanning: {
    eyebrow: 'Scanning',
    title: 'See what’s exposed. Immediately.',
    lede: 'Three engines, one scope. Nothing waits on a verification queue — exposure is a fact, not a ticket.',
  },
  sovereignty: {
    eyebrow: 'Sovereignty',
    title: 'Your data never leaves the room.',
    lede: 'Every prompt is stripped before it reaches a model outside your walls. No foreign vendor holds your client’s name.',
  },
  contact: {
    eyebrow: 'Contact',
    title: 'Talk to the people who built it.',
    lede: 'No ticket queue, no chatbot. Real channels, answered by Utachi Industries.',
  },
}

export const platformFeatures = [
  {
    title: 'Client onboarding',
    body: 'Every client gets a named owner and a scoped authorization agreement from day one. Nothing is scanned that wasn’t explicitly put in scope.',
  },
  {
    title: 'Scan scopes',
    body: 'Domains, IPs, URLs — add what’s in play, exclude what isn’t. The scope is the contract.',
  },
  {
    title: 'Findings & human review',
    body: 'Every finding carries severity, evidence, and remediation. Critical and high findings don’t close without a named analyst’s signature.',
  },
  {
    title: 'Immutable audit log',
    body: 'Every action, every scan, every AI query, every review — written once, never edited. The record that survives the dispute.',
  },
  {
    title: 'Admin controls',
    body: 'Own the roster. Mint and revoke API keys. Full control over who can touch what, enforced at the endpoint, not just the UI.',
  },
]

export const scanningCapabilities = [
  {
    title: 'Nuclei template matching',
    body: 'Thousands of community-maintained templates, matched against every in-scope target and normalized into evidence-backed findings.',
  },
  {
    title: 'Nmap service detection',
    body: 'Open ports, service banners, version strings. What’s actually listening, not what’s documented.',
  },
  {
    title: 'HTTP/HTTPS extraction',
    body: 'Headers, titles, response bodies — captured as evidence, not summarized away.',
  },
  {
    title: 'No verification gate',
    body: 'A scope is added, a scan runs. No approval queue standing between you and knowing what’s exposed.',
  },
  {
    title: 'Defensive-only',
    body: 'Find and report. No exploitation, no lateral movement, no exfiltration beyond the evidence a finding needs.',
  },
]

export const sovereigntyPrinciples = [
  {
    title: 'Prompt sanitization',
    body: 'Client names, IPs, credentials, tokens, emails, card numbers — stripped before a single byte leaves the premises.',
  },
  {
    title: 'Model abstraction',
    body: 'Anthropic today, OpenAI tomorrow, local only forever if you want it. No model vendor owns your workflow.',
  },
  {
    title: 'Local fallback',
    body: 'If a prompt still looks sensitive after sanitization — or you tell it to — it never leaves. A local responder answers instead.',
  },
  {
    title: 'Immutable AI audit log',
    body: 'Every query logged: provider, model, whether it was sanitized, a hash of prompt and response. Never the raw content.',
  },
]

export const privacyNotice = {
  updated: '2026-10-18',
  sections: [
    {
      heading: 'What we store',
      body: 'Ultorn stores the data you give it directly: user accounts (email, hashed password, role), client records, scan scopes (domains/IPs/URLs you add), scan results and findings (including evidence such as HTTP headers, banners, and page content captured during a scan), and an audit log of actions taken in the platform.',
    },
    {
      heading: 'AI queries',
      body: 'When you use the AI Guard feature, your prompt is sanitized to strip client names, IPs, credentials, and other sensitive patterns before it is sent to an external model (or kept local if it is still sensitive, or if you request local-only processing). We log the provider, model, and a one-way hash of the prompt and response — not the raw text.',
    },
    {
      heading: 'Where it lives',
      body: 'In the default self-hosted configuration, all data is stored in a local SQLite database under your own infrastructure. Nothing is sent to Utachi Industries or any third party except the AI provider you configure, and only for the sanitized portion of a query you explicitly submit.',
    },
    {
      heading: 'Who can see it',
      body: 'Access is role-gated: clients see only their own clients/scans/findings, analysts and admins see all records, and only admins can view the audit log, manage users, or manage API keys. API keys authenticate as the admin account that minted them.',
    },
    {
      heading: 'Retention & deletion',
      body: 'Records persist until you delete them at the infrastructure level (there is no automatic expiry in this MVP). Because the audit log is immutable by design, actions remain logged even if the underlying record is later removed.',
    },
    {
      heading: 'Status',
      body: 'This is a plain-language description of what the current Ultorn codebase actually does with data — it is not a substitute for a lawyer-reviewed privacy policy for your jurisdiction or client contracts, and should be reviewed before commercial use.',
    },
  ],
}

export const serviceAgreement = {
  updated: '2026-10-18',
  sections: [
    {
      heading: 'Scope of service',
      body: 'Ultorn is a defensive security scanning and findings-management platform. Scanning is limited to targets you explicitly add as a scan scope for a client you control or are contractually authorized to test. You are responsible for obtaining authorization before adding a target.',
    },
    {
      heading: 'No offensive capability',
      body: 'The platform finds and reports exposures only: port/service enumeration, template-based vulnerability matching, and HTTP/banner evidence capture. It performs no exploitation, no lateral movement, and no data exfiltration beyond that evidence.',
    },
    {
      heading: 'Human review',
      body: 'Critical and high-severity findings are flagged for named analyst review inside the product. Remediation decisions and any resulting action against a client’s environment remain the responsibility of the reviewing analyst and the client relationship, not the platform.',
    },
    {
      heading: 'Accounts & access',
      body: 'You are responsible for the credentials and API keys issued under your account. Admins can revoke access at any time from the Admin panel. Revoked API keys and disabled users lose access immediately.',
    },
    {
      heading: 'Availability',
      body: 'This is an MVP self-hosted platform provided as-is, without uptime guarantees, run on infrastructure you control.',
    },
    {
      heading: 'Status',
      body: 'This is a plain-language description of how the current Ultorn codebase behaves — it is not a substitute for a lawyer-drafted service agreement or master services agreement with your clients, and should be reviewed before commercial use.',
    },
  ],
}
