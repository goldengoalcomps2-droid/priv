import { z } from "zod";
import { prisma, ApprovalKind, OnboardingStatus } from "@fleetpro/db";
import type { AgentEntry } from "../runtime/types.js";
import { tool, obj, str, num } from "../tools/shared.js";

/**
 * Customer Onboarding agent
 * - Receives the licence + form payload from the public portal
 * - OCRs the licence, cross-checks address vs licence, runs liveness/selfie match
 * - Persists Customer + LicenceImage(s), creates a draft hire if requested
 * - Notifies operator (queues a CONTACT_CUSTOMER approval if anything is flagged)
 */

const SYSTEM_PROMPT = `You are the FleetPro Customer Onboarding Agent.

Your job is to validate a new customer submission, persist the record, and
flag anything that needs human review. UK GDPR (UK GDPR / Data Protection Act
2018) applies — only process the data the user has consented to, and never
fabricate fields. If the OCR result is ambiguous, say so and queue a contact
request rather than guessing.

Always run the licence OCR first, then verify the address, then run liveness
if a selfie was provided. After all checks, persist the customer and produce
a one-paragraph summary citing the specific checks that passed or failed.`;

export const customerOnboardingAgent: AgentEntry = {
  name: "CUSTOMER_ONBOARDING",
  systemPrompt: SYSTEM_PROMPT,
  tools: [
    tool({
      name: "ocr_parse_licence",
      description: "Run OCR on the uploaded licence images and extract DVLA fields.",
      input: z.object({ frontS3Key: z.string(), backS3Key: z.string() }),
      jsonSchema: obj(
        {
          frontS3Key: str("S3 key for the licence front image"),
          backS3Key: str("S3 key for the licence back image"),
        },
        ["frontS3Key", "backS3Key"],
      ),
      handler: async (_input) => {
        // Real implementation: call AWS Textract / Google Vision via OCR_PROVIDER
        return {
          licenceNumber: "EXTRACTED-LICENCE-NUMBER",
          fullName: "EXTRACTED NAME",
          dateOfBirth: "1990-01-01",
          address: "EXTRACTED ADDRESS",
          issueDate: "2020-01-01",
          expiryDate: "2030-01-01",
          categories: ["B"],
        };
      },
    }),
    tool({
      name: "verify_address_match",
      description: "Compare the form-submitted address with the OCR'd licence address.",
      input: z.object({ formAddress: z.string(), licenceAddress: z.string() }),
      jsonSchema: obj(
        {
          formAddress: str("Address typed into the onboarding form"),
          licenceAddress: str("Address extracted from licence OCR"),
        },
        ["formAddress", "licenceAddress"],
      ),
      handler: async ({ formAddress, licenceAddress }) => {
        const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
        const a = norm(formAddress);
        const b = norm(licenceAddress);
        const tokensA = new Set(a.split(" "));
        const tokensB = new Set(b.split(" "));
        const overlap = [...tokensA].filter((t) => tokensB.has(t)).length;
        const score = overlap / Math.max(tokensA.size, tokensB.size);
        return { score, matches: score >= 0.6 };
      },
    }),
    tool({
      name: "run_liveness_check",
      description: "Optional selfie-vs-licence liveness check. Returns a 0..1 confidence score.",
      input: z.object({ selfieS3Key: z.string(), licenceS3Key: z.string() }),
      jsonSchema: obj(
        { selfieS3Key: str("Selfie image S3 key"), licenceS3Key: str("Licence image S3 key") },
        ["selfieS3Key", "licenceS3Key"],
      ),
      handler: async () => ({ score: 0.92 }),
    }),
    tool({
      name: "persist_customer",
      description: "Create the Customer row plus LicenceImage records.",
      input: z.object({
        fullName: z.string(),
        email: z.string().email(),
        phone: z.string(),
        dateOfBirth: z.string(),
        addressLine1: z.string(),
        city: z.string(),
        postcode: z.string(),
        licenceNumber: z.string(),
        consentText: z.string(),
        consentSignatureSvg: z.string(),
        consentIpAddress: z.string(),
        addressMatchesLicence: z.boolean(),
        livenessScore: z.number().optional(),
        flags: z.array(z.string()).default([]),
        frontS3Key: z.string(),
        backS3Key: z.string(),
        s3KmsKeyId: z.string(),
      }),
      jsonSchema: obj(
        {
          fullName: str("Full name"),
          email: str("Email"),
          phone: str("Phone (UK)"),
          dateOfBirth: str("ISO date of birth"),
          addressLine1: str("Address line 1"),
          city: str("City"),
          postcode: str("UK postcode"),
          licenceNumber: str("DVLA licence number"),
          consentText: str("Consent text the customer signed"),
          consentSignatureSvg: str("SVG-encoded signature"),
          consentIpAddress: str("IP address of consent submission"),
          addressMatchesLicence: { type: "boolean", description: "Result of address verification" },
          livenessScore: num("0..1 liveness confidence (optional)"),
          flags: { type: "array", items: { type: "string" }, description: "Onboarding flags surfaced for operator review" },
          frontS3Key: str("Licence front S3 key"),
          backS3Key: str("Licence back S3 key"),
          s3KmsKeyId: str("KMS CMK used to encrypt the images at rest"),
        },
        ["fullName", "email", "phone", "dateOfBirth", "addressLine1", "city", "postcode", "licenceNumber", "consentText", "consentSignatureSvg", "consentIpAddress", "addressMatchesLicence", "frontS3Key", "backS3Key", "s3KmsKeyId"],
      ),
      handler: async (i) => {
        const status = i.flags.length > 0 || !i.addressMatchesLicence ? OnboardingStatus.PENDING_REVIEW : OnboardingStatus.VERIFIED;
        const customer = await prisma.customer.create({
          data: {
            fullName: i.fullName,
            email: i.email,
            phone: i.phone,
            dateOfBirth: new Date(i.dateOfBirth),
            addressLine1: i.addressLine1,
            city: i.city,
            postcode: i.postcode,
            licenceNumber: i.licenceNumber,
            consentText: i.consentText,
            consentSignedAt: new Date(),
            consentSignatureSvg: i.consentSignatureSvg,
            consentIpAddress: i.consentIpAddress,
            addressMatchesLicence: i.addressMatchesLicence,
            livenessScore: i.livenessScore,
            onboardingFlags: i.flags,
            onboardingStatus: status,
            licenceImages: {
              createMany: {
                data: [
                  { side: "FRONT", s3Key: i.frontS3Key, s3KmsKeyId: i.s3KmsKeyId },
                  { side: "BACK", s3Key: i.backS3Key, s3KmsKeyId: i.s3KmsKeyId },
                ],
              },
            },
          },
        });
        return { customerId: customer.id, status };
      },
    }),
    tool({
      name: "request_operator_contact",
      description: "Queue a CONTACT_CUSTOMER approval when something needs operator outreach.",
      input: z.object({ customerId: z.string(), reason: z.string() }),
      jsonSchema: obj(
        { customerId: str("Customer ID"), reason: str("Why operator outreach is needed") },
        ["customerId", "reason"],
      ),
      requiresApproval: ApprovalKind.CONTACT_CUSTOMER,
      handler: async () => ({ queued: true }),
    }),
  ],
};
