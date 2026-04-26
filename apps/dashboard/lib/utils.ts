import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** £ formatting from pence. e.g. 7749800 → "£77,498" */
export function gbp(pence: number | null | undefined, opts: { whole?: boolean } = { whole: true }): string {
  if (pence == null) return "—";
  const pounds = pence / 100;
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: opts.whole ? 0 : 2,
  }).format(pounds);
}

/** Compact £ for big numbers: 1,057,000 → "£1057k" */
export function gbpCompact(pence: number | null | undefined): string {
  if (pence == null) return "—";
  const pounds = pence / 100;
  if (Math.abs(pounds) >= 1_000_000) return `£${(pounds / 1_000_000).toFixed(1)}m`;
  if (Math.abs(pounds) >= 1_000) return `£${Math.round(pounds / 1_000)}k`;
  return `£${Math.round(pounds)}`;
}

export function pct(n: number, digits = 0): string {
  return `${(n * 100).toFixed(digits)}%`;
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]!.toUpperCase())
    .join("");
}

export function formatDate(d: Date | string | null | undefined): string {
  if (!d) return "—";
  const date = typeof d === "string" ? new Date(d) : d;
  return date.toLocaleDateString("en-GB", { year: "numeric", month: "2-digit", day: "2-digit" });
}

export function daysUntil(d: Date | string): number {
  const date = typeof d === "string" ? new Date(d) : d;
  return Math.ceil((date.getTime() - Date.now()) / 86_400_000);
}
