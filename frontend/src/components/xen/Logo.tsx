export function LogoMark({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <path d="M5 5 L16 16 L27 5" fill="none" stroke="var(--color-primary)" strokeWidth="3" strokeLinecap="round" />
      <path d="M16 16 L5 27 M16 16 L22 22 L27 27" fill="none" stroke="var(--color-cyan)" strokeWidth="3" strokeLinecap="round" />
      <circle cx="16" cy="16" r="2.6" fill="var(--color-foreground)" />
      <circle cx="22" cy="22" r="1.8" fill="var(--color-cyan)" />
    </svg>
  );
}

export function Logo() {
  return (
    <span className="flex items-center gap-2 font-semibold tracking-tight">
      <LogoMark />
      <span className="text-lg">XenMind</span>
    </span>
  );
}
