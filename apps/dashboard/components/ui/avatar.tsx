import { initials } from "@/lib/utils";

export function Avatar({ name, size = "md" }: { name: string; size?: "sm" | "md" }) {
  const dim = size === "sm" ? "h-6 w-6 text-[10px]" : "h-8 w-8 text-xs";
  return (
    <div
      aria-hidden
      className={`${dim} rounded-full bg-brand-soft text-brand-ink font-semibold grid place-items-center shrink-0`}
    >
      {initials(name)}
    </div>
  );
}
