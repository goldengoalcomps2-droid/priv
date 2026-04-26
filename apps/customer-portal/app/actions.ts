"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { z } from "zod";
import { prisma, OnboardingStatus, AgentName, ActivityKind } from "@fleetpro/db";

const Submission = z.object({
  fullName: z.string().min(2),
  dateOfBirth: z.string().min(1),
  email: z.string().email(),
  phone: z.string().min(8),
  addressLine1: z.string().min(2),
  addressLine2: z.string().optional().nullable(),
  city: z.string().min(2),
  postcode: z.string().min(3),
  licenceNumber: z.string().min(4),
  consentChecked: z.string(), // checkbox value "on" | undefined
  consentSignatureSvg: z.string(),
});

/**
 * Server action invoked by the customer-portal form. The server handles:
 *   1. Validate consent + capture IP + signature SVG (Article 7 record)
 *   2. (In a real deploy) push licence images to S3 with KMS encryption
 *      and attach LicenceImage rows; here we no-op the S3 step
 *   3. Persist the customer with onboardingStatus=PENDING_REVIEW so the
 *      Customer Onboarding agent / operator can verify
 *   4. Write to AgentActivity so the dashboard shows the new submission
 *      in the Agent Activity feed
 */
export async function submitOnboarding(formData: FormData) {
  const raw = Object.fromEntries(formData.entries());
  const parsed = Submission.safeParse({
    ...raw,
    addressLine2: raw.addressLine2 ?? null,
  });
  if (!parsed.success) {
    return { ok: false as const, error: parsed.error.flatten() };
  }
  const data = parsed.data;
  if (data.consentChecked !== "on") {
    return { ok: false as const, error: "You must confirm consent before submitting." };
  }

  const h = await headers();
  const ip = h.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "0.0.0.0";

  const customer = await prisma.customer.create({
    data: {
      fullName: data.fullName,
      email: data.email,
      phone: data.phone,
      dateOfBirth: new Date(data.dateOfBirth),
      addressLine1: data.addressLine1,
      addressLine2: data.addressLine2 ?? undefined,
      city: data.city,
      postcode: data.postcode.toUpperCase(),
      licenceNumber: data.licenceNumber.toUpperCase(),
      consentText:
        "I confirm the licence and details I have provided are accurate, and I consent to FleetPro processing this data to operate my vehicle hire under UK GDPR.",
      consentSignedAt: new Date(),
      consentSignatureSvg: data.consentSignatureSvg,
      consentIpAddress: ip,
      addressMatchesLicence: false, // will be set by Onboarding agent OCR check
      onboardingStatus: OnboardingStatus.PENDING_REVIEW,
    },
  });

  await prisma.agentActivity.create({
    data: {
      agent: AgentName.CUSTOMER_ONBOARDING,
      kind: ActivityKind.NOTIFICATION,
      summary: `New customer submission from ${data.fullName} — pending review`,
      customerId: customer.id,
      toolName: "portal.submit",
      toolInput: { email: data.email, postcode: data.postcode },
    },
  });

  redirect(`/thank-you?ref=${customer.id}`);
}
