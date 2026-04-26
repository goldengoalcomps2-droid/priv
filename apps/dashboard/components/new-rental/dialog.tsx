"use client";

import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Upload, X, ArrowRight, CheckCircle2, Search } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * New Rental wizard. Four steps that map to the agent runtime:
 *   1. ID upload → Customer Onboarding agent (or pick existing — no re-upload)
 *   2. Customer details (auto-populated when an existing customer is selected)
 *   3. Vehicle & dates → Hire & Agreement agent runs collision check
 *   4. Agreement preview → "Send for signature" queues an Approval row
 *      (approval queue is the human-in-the-loop gate for this irreversible
 *      customer-facing step).
 *
 * State stays in component-local React state for now; persistence happens
 * when the operator clicks Send (which calls a server action that creates
 * the draft hire + queues the approval).
 */

const STEPS = [
  { id: 1, label: "ID", sub: "upload" },
  { id: 2, label: "Customer", sub: "" },
  { id: 3, label: "Vehicle", sub: "& dates" },
  { id: 4, label: "Agreement", sub: "" },
] as const;

type ExistingCustomer = { id: string; fullName: string; email: string; postcode: string };

export type NewRentalDialogProps = {
  /** Verified customers, supplied by the page (server-fetched) so the
   *  dropdown is populated without an extra round-trip. */
  customers: ExistingCustomer[];
  /** Vehicles in AVAILABLE status — supplied by the page. */
  availableVehicles: { id: string; make: string; model: string; trim: string | null; vrn: string }[];
};

export function NewRentalDialog({ customers, availableVehicles }: NewRentalDialogProps) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [vehicleId, setVehicleId] = useState<string | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);

  const selectedCustomer = customers.find((c) => c.id === selectedCustomerId) ?? null;
  const selectedVehicle = availableVehicles.find((v) => v.id === vehicleId) ?? null;

  function reset() {
    setStep(1);
    setSelectedCustomerId(null);
    setFilename(null);
    setVehicleId(null);
    setStartDate("");
    setEndDate("");
    setSubmitMessage(null);
  }

  function next() {
    setStep((s) => (Math.min(4, s + 1) as 1 | 2 | 3 | 4));
  }

  async function submit() {
    setSubmitting(true);
    setSubmitMessage(null);
    try {
      const res = await fetch("/api/new-rental", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ customerId: selectedCustomerId, vehicleId, startDate, endDate }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as { hireId: string; approvalId: string };
      setSubmitMessage(`Draft hire created (${data.hireId}). Approval queued: ${data.approvalId}.`);
      // Live region announce
      const live = document.getElementById("agent-live");
      if (live) live.textContent = "Hire agreement queued for operator approval.";
    } catch (err) {
      setSubmitMessage(`Could not queue: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) reset();
      }}
    >
      <Dialog.Trigger asChild>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-hover focus-visible:outline-2"
        >
          + New Rental
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-ink/40 backdrop-blur-sm z-40" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-[680px] max-w-[92vw] -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-card shadow-2xl border border-rule focus:outline-none"
          aria-describedby="new-rental-desc"
        >
          <div className="flex items-start justify-between px-6 pt-6 pb-2">
            <Dialog.Title className="text-lg font-semibold sr-only">New Rental</Dialog.Title>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Close dialog"
                className="ml-auto rounded-md p-1.5 text-ink-muted hover:bg-page focus-visible:outline-2"
              >
                <X className="h-4 w-4" aria-hidden />
              </button>
            </Dialog.Close>
          </div>

          {/* Stepper */}
          <ol className="px-8 pb-2 flex items-center justify-between" aria-label="Wizard progress">
            {STEPS.map((s, i) => {
              const done = step > s.id;
              const active = step === s.id;
              return (
                <li key={s.id} className="flex-1 flex items-center">
                  <div className="flex flex-col items-center text-center">
                    <span
                      aria-current={active ? "step" : undefined}
                      className={cn(
                        "h-7 w-7 rounded-full grid place-items-center text-xs font-semibold border-2",
                        done ? "bg-brand border-brand text-white" :
                        active ? "bg-card border-brand text-brand" :
                                 "bg-card border-rule text-ink-subtle",
                      )}
                    >
                      {done ? <CheckCircle2 className="h-4 w-4" aria-hidden /> : s.id}
                    </span>
                    <span className="mt-1 text-[11px] font-medium leading-tight">
                      {s.label}<br />
                      {s.sub && <span className="text-ink-muted">{s.sub}</span>}
                    </span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className={cn("flex-1 h-px mx-2", done ? "bg-brand" : "bg-rule")} aria-hidden />
                  )}
                </li>
              );
            })}
          </ol>

          <div className="px-8 py-6 space-y-4 min-h-[260px]" id="new-rental-desc">
            {step === 1 && (
              <>
                <h3 className="font-semibold">Upload driving licence</h3>
                <p className="text-sm text-ink-muted">
                  Upload the front of the customer's driving licence. We'll extract their details automatically.
                </p>
                <label
                  htmlFor="licence-upload"
                  className="grid place-items-center text-center rounded-xl border-2 border-dashed border-rule bg-page/40 px-6 py-12 cursor-pointer hover:border-brand"
                >
                  <Upload className="h-7 w-7 text-ink-subtle" aria-hidden />
                  <div className="mt-2 text-sm font-medium">{filename ?? "Click to upload or drag & drop"}</div>
                  <div className="mt-1 text-xs text-ink-muted">PNG, JPG up to 10MB</div>
                  <input
                    id="licence-upload"
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="sr-only"
                    onChange={(e) => setFilename(e.target.files?.[0]?.name ?? null)}
                  />
                </label>

                <div className="text-center text-xs text-ink-muted pt-2">— or —</div>
                <label className="block">
                  <span className="text-sm font-medium">Use an existing customer</span>
                  <div className="relative mt-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-subtle" aria-hidden />
                    <select
                      value={selectedCustomerId ?? ""}
                      onChange={(e) => setSelectedCustomerId(e.target.value || null)}
                      className="w-full rounded-md border border-rule bg-card pl-9 pr-3 py-2 text-sm"
                    >
                      <option value="">Select a verified customer…</option>
                      {customers.map((c) => (
                        <option key={c.id} value={c.id}>{c.fullName} — {c.email}</option>
                      ))}
                    </select>
                  </div>
                </label>
              </>
            )}

            {step === 2 && (
              <>
                <h3 className="font-semibold">Customer</h3>
                {selectedCustomer ? (
                  <div className="rounded-md border border-rule p-4">
                    <div className="font-medium">{selectedCustomer.fullName}</div>
                    <div className="text-sm text-ink-muted">{selectedCustomer.email}</div>
                    <div className="text-sm text-ink-muted tabular-nums mt-1">{selectedCustomer.postcode}</div>
                    <p className="mt-3 text-xs text-ink-muted">
                      Existing customer — using stored licence and consent. No re-upload required.
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-ink-muted">
                    Onboarding agent has extracted these fields from the licence — please review and amend if needed.
                  </p>
                )}
              </>
            )}

            {step === 3 && (
              <>
                <h3 className="font-semibold">Vehicle & dates</h3>
                <label className="block">
                  <span className="text-sm font-medium">Vehicle</span>
                  <select
                    value={vehicleId ?? ""}
                    onChange={(e) => setVehicleId(e.target.value || null)}
                    className="mt-1 w-full rounded-md border border-rule bg-card px-3 py-2 text-sm"
                  >
                    <option value="">Select a vehicle…</option>
                    {availableVehicles.map((v) => (
                      <option key={v.id} value={v.id}>{v.make} {v.model} {v.trim ?? ""} — {v.vrn}</option>
                    ))}
                  </select>
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <label className="block">
                    <span className="text-sm font-medium">Start</span>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="mt-1 w-full rounded-md border border-rule bg-card px-3 py-2 text-sm"
                    />
                  </label>
                  <label className="block">
                    <span className="text-sm font-medium">End</span>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="mt-1 w-full rounded-md border border-rule bg-card px-3 py-2 text-sm"
                    />
                  </label>
                </div>
                <p className="text-xs text-ink-muted">
                  When you continue, the Hire & Agreement agent runs a collision check and proposes alternatives if there's overlap.
                </p>
              </>
            )}

            {step === 4 && (
              <>
                <h3 className="font-semibold">Review & send agreement</h3>
                <div className="rounded-md border border-rule p-4 text-sm space-y-1">
                  <div><strong>Customer:</strong> {selectedCustomer?.fullName ?? "—"}</div>
                  <div><strong>Vehicle:</strong> {selectedVehicle ? `${selectedVehicle.make} ${selectedVehicle.model} (${selectedVehicle.vrn})` : "—"}</div>
                  <div><strong>Period:</strong> {startDate || "—"} → {endDate || "—"}</div>
                </div>
                <p className="text-xs text-ink-muted">
                  Sending for signature is irreversible and customer-facing. It will be queued in the operator approval queue;
                  the actual Adobe Sign request fires only after a human Approve.
                </p>
                {submitMessage && (
                  <div role="status" className="rounded-md bg-brand-soft text-brand-ink px-3 py-2 text-sm">
                    {submitMessage}
                  </div>
                )}
              </>
            )}
          </div>

          <footer className="border-t border-rule px-6 py-4 flex items-center justify-end gap-2">
            <Dialog.Close asChild>
              <button
                type="button"
                className="rounded-md border border-rule bg-card px-4 py-2 text-sm font-medium hover:bg-page"
              >
                Cancel
              </button>
            </Dialog.Close>
            {step === 1 && (
              <button
                type="button"
                onClick={() => { setSelectedCustomerId(null); next(); }}
                className="rounded-md border border-rule bg-card px-4 py-2 text-sm font-medium hover:bg-page"
              >
                Skip (manual entry)
              </button>
            )}
            {step < 4 && (
              <button
                type="button"
                onClick={next}
                disabled={step === 1 && !filename && !selectedCustomerId}
                className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next <ArrowRight className="h-4 w-4" aria-hidden />
              </button>
            )}
            {step === 4 && (
              <button
                type="button"
                onClick={submit}
                disabled={submitting || !selectedCustomerId || !vehicleId || !startDate || !endDate}
                className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-hover disabled:opacity-50"
              >
                {submitting ? "Queuing…" : "Queue for approval"}
              </button>
            )}
          </footer>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
