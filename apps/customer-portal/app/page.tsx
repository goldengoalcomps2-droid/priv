import { ShieldCheck, Upload } from "lucide-react";
import { submitOnboarding } from "./actions";
import { SignaturePad } from "@/components/signature-pad";

export default function PortalHomePage() {
  return (
    <>
      <h1 className="text-2xl font-semibold">Hire a vehicle from FleetPro</h1>
      <p className="mt-2 text-ink-muted">
        Complete this short form so we can prepare your hire agreement. Your data is processed under UK GDPR; your licence images
        are encrypted at rest and only viewed by authorised staff.
      </p>

      <form action={submitOnboarding} className="mt-8 space-y-8">
        <fieldset className="rounded-xl border border-rule bg-card p-6">
          <legend className="px-2 text-sm font-semibold">1. Driving licence</legend>
          <p className="text-sm text-ink-muted">Upload the front and back of your licence. PNG or JPG, up to 10 MB each.</p>
          <div className="mt-3 grid sm:grid-cols-2 gap-3">
            <label className="grid place-items-center text-center rounded-md border-2 border-dashed border-rule bg-page/40 px-4 py-8 cursor-pointer hover:border-brand">
              <Upload className="h-6 w-6 text-ink-subtle" aria-hidden />
              <span className="mt-1 text-sm font-medium">Front of licence</span>
              <span className="text-xs text-ink-muted">Click or drop file</span>
              <input name="licenceFront" type="file" accept="image/*" capture="environment" required className="sr-only" aria-required="true" />
            </label>
            <label className="grid place-items-center text-center rounded-md border-2 border-dashed border-rule bg-page/40 px-4 py-8 cursor-pointer hover:border-brand">
              <Upload className="h-6 w-6 text-ink-subtle" aria-hidden />
              <span className="mt-1 text-sm font-medium">Back of licence</span>
              <span className="text-xs text-ink-muted">Click or drop file</span>
              <input name="licenceBack" type="file" accept="image/*" capture="environment" required className="sr-only" aria-required="true" />
            </label>
          </div>
        </fieldset>

        <fieldset className="rounded-xl border border-rule bg-card p-6">
          <legend className="px-2 text-sm font-semibold">2. Your details</legend>
          <div className="grid sm:grid-cols-2 gap-4">
            <Field label="Full name (as on licence)" name="fullName" autoComplete="name" required />
            <Field label="Date of birth" name="dateOfBirth" type="date" autoComplete="bday" required />
            <Field label="Email" name="email" type="email" autoComplete="email" required />
            <Field label="Phone" name="phone" type="tel" autoComplete="tel" required />
            <Field label="Driving licence number" name="licenceNumber" required />
            <Field label="Postcode" name="postcode" autoComplete="postal-code" required />
            <Field label="Address line 1" name="addressLine1" autoComplete="address-line1" required />
            <Field label="Address line 2 (optional)" name="addressLine2" autoComplete="address-line2" />
            <Field label="City" name="city" autoComplete="address-level2" required />
          </div>
        </fieldset>

        <fieldset className="rounded-xl border border-rule bg-card p-6">
          <legend className="px-2 text-sm font-semibold">3. Consent</legend>
          <div className="rounded-md bg-brand-soft text-brand-ink p-4 text-sm flex items-start gap-2">
            <ShieldCheck className="h-4 w-4 mt-0.5" aria-hidden />
            <p>
              We process your data under UK GDPR Article 6(1)(b) (contract performance). Special-category data (licence images)
              is processed only with your explicit consent under Article 9(2)(a). You can withdraw consent at any time.
            </p>
          </div>
          <label className="mt-4 flex items-start gap-2 text-sm">
            <input type="checkbox" name="consentChecked" required className="mt-0.5" aria-required="true" />
            <span>
              I confirm that the licence and details above are accurate, and I consent to FleetPro processing this data
              to operate my vehicle hire and to handle any associated penalty charges or repairs.
            </span>
          </label>

          <div className="mt-4">
            <span className="text-sm font-medium">Signature</span>
            <SignaturePad />
          </div>
        </fieldset>

        <button
          type="submit"
          className="rounded-md bg-brand px-6 py-3 text-sm font-semibold text-white hover:bg-brand-hover focus-visible:outline-2"
        >
          Submit for review
        </button>
      </form>
    </>
  );
}

function Field({
  label,
  name,
  type = "text",
  required,
  autoComplete,
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
  autoComplete?: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium">
        {label}
        {required && <span aria-hidden className="text-bad"> *</span>}
        {required && <span className="sr-only"> (required)</span>}
      </span>
      <input
        name={name}
        type={type}
        autoComplete={autoComplete}
        required={required}
        aria-required={required}
        className="mt-1 w-full rounded-md border border-rule bg-card px-3 py-2 text-sm"
      />
    </label>
  );
}
