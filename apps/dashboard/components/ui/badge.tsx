import { cn } from "@/lib/utils";

const TONES = {
  active: "bg-info-soft text-info",
  ok: "bg-ok-soft text-ok",
  warn: "bg-warn-soft text-warn",
  bad: "bg-bad-soft text-bad",
  muted: "bg-rule text-ink-muted",
  brand: "bg-brand-soft text-brand-ink",
} as const;

export type BadgeTone = keyof typeof TONES;

export function Badge({
  tone = "muted",
  children,
  className,
}: {
  tone?: BadgeTone;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium", TONES[tone], className)}>
      {children}
    </span>
  );
}
