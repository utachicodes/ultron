export default function Arrow({ className = 'marw' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 12 10" fill="none" aria-hidden="true">
      <path
        d="M0.8 5h10M7.1 1.4 10.9 5l-3.8 3.6"
        stroke="currentColor"
        strokeWidth="1.35"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
