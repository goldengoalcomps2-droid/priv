import { CheckCircle2 } from "lucide-react";

export default async function ThankYouPage({ searchParams }: { searchParams: Promise<{ ref?: string }> }) {
  const { ref } = await searchParams;
  return (
    <section className="rounded-xl border border-rule bg-card p-8 text-center">
      <CheckCircle2 className="mx-auto h-10 w-10 text-brand" aria-hidden />
      <h1 className="mt-3 text-xl font-semibold">Thank you — submitted</h1>
      <p className="mt-2 text-sm text-ink-muted">
        Your details are with our onboarding team. We'll email you once your hire agreement is ready to sign.
      </p>
      {ref && <p className="mt-4 text-xs text-ink-subtle font-mono">Reference: {ref}</p>}
      <p className="mt-6 text-xs text-ink-muted">
        Need to update or remove your data? Email{" "}
        <a className="text-brand underline" href="mailto:dpo@fleetpro.example">dpo@fleetpro.example</a>{" "}
        — we honour UK GDPR rights of access, rectification, and erasure within one calendar month.
      </p>
    </section>
  );
}
