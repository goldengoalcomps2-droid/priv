# FleetPro

Multi-agent dashboard for a UK salvage vehicle hire business. The system runs
with ~90% autonomy across six business domains; a human operator confirms only
the irreversible / customer-facing steps via a unified approval queue.

> **Status:** scaffold + reference implementation. Every external integration
> (DVLA/DVSA, Adobe Sign, telematics, valuations, OCR, procurement feeds) ships
> as a typed tool stub the operator wires up to their own provider account.

## Repository layout

```
apps/
  dashboard/         — Next.js 15 operator dashboard (port 3000)
  customer-portal/   — Next.js public onboarding form (port 3001)
packages/
  agents/            — Anthropic SDK orchestrator + 6 agents + tool registry
  db/                — Prisma schema + deterministic seed
e2e/                 — Playwright golden-path tests, one per agent
.env.example         — every env var any package reads, grouped by integration
```

## Prerequisites

| Tool          | Version |
| ------------- | ------- |
| Node.js       | ≥ 20.10 |
| pnpm          | ≥ 9.0   |
| PostgreSQL    | ≥ 14    |
| Redis         | ≥ 6     (BullMQ queues for long-running agent workloads) |

## Quick start

```bash
pnpm install
cp .env.example .env                  # fill in DATABASE_URL + ANTHROPIC_API_KEY
pnpm db:generate
pnpm db:migrate                       # creates schema
pnpm db:seed                          # populates a representative fleet
pnpm dev                              # runs both apps in parallel
```

Open:

- Dashboard: <http://localhost:3000>
- Customer onboarding: <http://localhost:3001>

> Every dashboard widget is computed live from the database — no hardcoded
> totals — so it scales from 5 vehicles to 500 without code changes.

## Architecture

### Frontend

- **React 19 + TypeScript + Tailwind**, in-house shadcn-style primitives
- **@tanstack/react-table** for data grids (Vehicles, Vehicle P&L, Customers, Fines)
- **Recharts** for analytics (revenue-by-month bar chart, fleet-mix donut)
- **CSS-grid Gantt** for the timeline (no heavyweight Gantt lib pulled in)
- **react-aria-components / Radix UI** for the New Rental dialog and other a11y-sensitive primitives

### Backend

- **Next.js route handlers** (`app/api/*`) + **server actions** for the customer portal
- **PostgreSQL via Prisma** (`packages/db`) — single schema, every domain modelled
- **Redis** (BullMQ) for long-running agent jobs (vendor-feed scans, weekly market digest)
- **S3-compatible object storage** for licence images, fine photos, signed PDFs

### Auth & RBAC

- **Auth.js** (or **Clerk**) with three roles: `OWNER`, `ADMIN`, `CUSTOMER_PORTAL`
- The customer portal exposes only the public submission flow; all dashboard
  routes are operator-only

### Agent runtime (`packages/agents`)

Orchestrator pattern with the **Anthropic SDK** (`@anthropic-ai/sdk`) on
`claude-sonnet-4-6`. Every agent is a triple of `{ system prompt, tools,
entry function }`. The orchestrator runs a manual tool-use loop:

1. send `messages + tools` to the model
2. for each `tool_use` block in the response:
   - `requiresApproval` set → write an `Approval` row, return synthetic `tool_result`
   - else → execute the handler, log to `AgentActivity`, return `tool_result`
3. when `stop_reason == "end_turn"`, return the final assistant text + audit trail

Every model call and tool call is persisted to `AgentActivity`, which is what
the dashboard's **Agent Activity** feed reads.

### Observability

- All tool calls (input, output, duration, errors) → `AgentActivity`
- Decisions → `AgentActivity` rows of kind `DECISION`, with `reasoning` +
  `citations` JSON populated from the model response
- Approvals → `Approval` rows (separate table for queue ergonomics)
- GDPR access events (licence-image VIEW / DOWNLOAD) → `AccessLog`

## The six agents

| # | Agent | Role | Approval-gated tools |
|---|-------|------|----------------------|
| 1 | **Customer Onboarding** | Validates licence + identity from the portal; persists `Customer`; flags mismatches | `request_operator_contact` |
| 2 | **Hire & Agreement** | Gantt collision detection, draft-hire creation, agreement PDF generation | `send_for_signature` |
| 3 | **Fines & PCN** | OCR PCN, match to active hire at offence datetime, build Transfer-of-Liability pack | `charge_customer_admin_fee`, `submit_pcn_challenge` |
| 4 | **Fleet Maintenance** | DVSA MOT pull, DVLA VES tax pull, calendar reminders, dealer lookup | none — read-only / low-risk |
| 5 | **Procurement** | Watch Copart / IAA / eBay / AutoTrader / Car & Classic / Facebook Marketplace; score against operator strategy; weekly market digest | `place_bid` |
| 6 | **Analytics & Defleet** | Telematics mileage, repair-invoice OCR, valuation refresh, RAG status (Green / Amber / Red) | `trigger_defleet_sale` |

Each agent's full system prompt and tool list is in
`packages/agents/src/agents/<name>.ts`.

## The human approval queue

When an agent calls a tool whose `requiresApproval` is set, the orchestrator
**does not execute** the side effect. Instead it writes a row to `Approval`
(table `approvals`) with:

- `agent` — which agent proposed the action
- `kind` — one of `SEND_HIRE_AGREEMENT`, `SUBMIT_PCN_CHALLENGE`,
  `CHARGE_CUSTOMER_FOR_FINE`, `PLACE_PROCUREMENT_BID`,
  `TRIGGER_DEFLEET_SALE`, `CONTACT_CUSTOMER`
- `proposedAction` — `{ tool, args }` JSON the dashboard will replay if approved
- `rationale` — model-generated narrative of why the action is needed
- `citations` — JSON array of supporting evidence (hire IDs, market data, etc.)
- `status` — `PENDING` | `APPROVED` | `REJECTED` | `EXPIRED`
- polymorphic context FKs (`hireId`, `fineId`, `procurementOpportunityId`, …)

### Operator workflow

1. The dashboard sidebar will show a count badge when approvals are pending.
2. The operator opens the queue, reads the rationale + citations, optionally
   inspects the linked entity (hire / fine / opportunity).
3. **Approve** → `resolveApproval()` flips the row to `APPROVED` and writes
   an `APPROVAL_RESOLUTION` activity. The dashboard then replays
   `proposedAction.tool` against the same handler that direct-execution would
   have used (Adobe Sign API, council PCN URL, procurement vendor API, …).
4. **Reject** → flips to `REJECTED`, writes the audit row, and the agent is
   notified next turn so it can adjust its plan.

This design keeps the orchestrator agnostic of which side-effects are
sensitive — sensitivity is declared per-tool, in the agent's tool registry,
not buried in glue code.

## Accessibility (WCAG 2.2 AA)

- **Skip link** as the first focusable element on every page
- **Visible focus rings** (`:focus-visible`) on every interactive element
- **ARIA landmarks** (`<main id="main">`, `<nav aria-label="Primary navigation">`)
- **`aria-live` polite region** (`#agent-live`) for agent notifications
- **`aria-current="page"`** on the active sidebar link
- **`prefers-reduced-motion`** halts animations / transitions
- **Colour contrast ≥ 4.5 : 1** on all body text; status pills (red / amber /
  green) all clear AA on a white background
- **Semantic headings** (`<h1>` per page, sectioned `<h2>`s)
- **Screen-reader labels** on every icon-only button (e.g. `aria-label="Close dialog"`)
- **Form errors announced** via the same `aria-live` region
- **`aria-required="true"`** on every required field, plus a sr-only "(required)"
  string so screen readers don't depend on the visual asterisk

## UK GDPR — DPIA notes

| Concern                              | How FleetPro handles it |
| ------------------------------------ | ----------------------- |
| Lawful basis for hire processing     | Article 6(1)(b) — necessary for performance of the hire contract |
| Special-category data (licence image) | Article 9(2)(a) — explicit consent captured + signed at portal submission |
| Consent record                       | `Customer.consentText` + `consentSignedAt` + `consentSignatureSvg` + `consentIpAddress`, immutable after creation |
| Data minimisation                    | Onboarding form collects only the fields required to verify the licence and contact the customer; selfie / liveness step is optional |
| Encryption at rest                   | Licence images (`LicenceImage.s3Key`) are stored in an S3 bucket with KMS-managed CMK; the CMK ID is recorded per row in `s3KmsKeyId` so key rotation is auditable |
| Access audit                         | Every read of `LicenceImage` is recorded in `AccessLog` (userId, IP, user-agent, action) |
| Right to erasure (Article 17)        | `DELETE /api/customers/:id` → flips `deletionRequestedAt`; nightly job pseudonymises personal fields, removes licence images from S3, and writes `pseudonymisedAt`. Hires are retained (financial record) but customer link is anonymised. |
| Right of access (Article 15)         | `GET /api/customers/:id/export` returns a JSON dump of every row referencing that customer ID |
| Retention                            | Hire agreements: 7 years (HMRC); fines: 7 years; licence images: deleted on contract close + 12 months unless flagged for fraud review; agent activity: 24 months |
| Cross-border transfers               | None by default — Postgres + S3 hosted in `eu-west-2` per `S3_REGION` |
| DPO contact                          | Configured at the customer-portal footer; emails route to `dpo@fleetpro.example` |

The DPIA template, full retention table, and the cookie / lawful-interest
register live in `docs/dpia.md` (operator-maintained, not committed in this
scaffold).

## Environment variables

Every variable any package reads is documented in `.env.example`, grouped by
integration. The notable ones:

| Var                            | Used by                          | Notes |
| ------------------------------ | -------------------------------- | ----- |
| `DATABASE_URL`                 | `@fleetpro/db`                   | Postgres connection string |
| `ANTHROPIC_API_KEY`            | `@fleetpro/agents`               | Required to run any agent |
| `ANTHROPIC_MODEL`              | `@fleetpro/agents`               | Defaults to `claude-sonnet-4-6` |
| `S3_BUCKET` / `S3_KMS_KEY_ID`  | onboarding + fines + analytics   | Licence images, PCN photos, repair invoices |
| `DVSA_MOT_HISTORY_API_KEY`     | Fleet Maintenance agent          | DVSA MOT History API |
| `DVLA_VES_API_KEY`             | Fleet Maintenance agent          | DVLA Vehicle Enquiry Service |
| `ADOBE_SIGN_INTEGRATION_KEY`   | Hire & Agreement agent           | E-signature handoff |
| `ADOBE_SIGN_WEBHOOK_SECRET`    | Hire & Agreement agent           | Used to verify the signed-PDF webhook |
| `GOOGLE_CALENDAR_CREDENTIALS_JSON` / `MICROSOFT_GRAPH_*` | Fleet Maintenance agent | MOT 7-days-before reminder |
| `TELEMATICS_API_BASE_URL` / `TELEMATICS_API_KEY`        | Analytics & Defleet agent | GPS mileage |
| `VALUATION_PROVIDER` / `VALUATION_API_KEY`              | Analytics & Defleet agent | CAP HPI / Glass's / AutoTrader Retail Rating |
| `COPART_API_KEY` / `IAA_API_KEY` / `EBAY_OAUTH_TOKEN` / `AUTOTRADER_API_KEY` / `CAR_AND_CLASSIC_API_KEY` / `FACEBOOK_MARKETPLACE_TOKEN` | Procurement agent | Vendor feeds |
| `OCR_PROVIDER` / `OCR_API_KEY` | Onboarding + Fines + Analytics   | AWS Textract or Google Vision |
| `APPROVAL_QUEUE_BASE_URL`      | dashboard email notifications    | Operator-facing approval queue URL |

## Testing

```bash
pnpm test:e2e
```

The Playwright suite covers each agent's golden path:

| Test                                | Verifies |
| ----------------------------------- | -------- |
| Customer Onboarding portal          | GDPR copy, signature pad, required fields with `aria-required` |
| Hire & Agreement wizard             | 4-step stepper, manual-entry skip, queue-disabled-until-valid |
| Fines & PCN page                    | Camera-capture dropzone, auto-match copy, summary cards |
| Fleet Maintenance bucketed view     | Overdue / Due-soon / All-good sections, MOT/Ins/Svc pills |
| Procurement activity feed           | Seeded scan surfaces in the dashboard's Agent Activity feed |
| Analytics & Defleet                 | Recharts revenue + donut charts, live-computed summary |
| Accessibility smoke                 | Skip link, landmarks, ARIA live region |

The suite intentionally does **not** call the real Anthropic API — it
exercises the dashboard / portal UI surface plus the database side-effects
of the tool handlers. Stub the model in unit tests if you need to assert
specific prompts.

## Scripts

| Script                         | What it does |
| ------------------------------ | ------------ |
| `pnpm dev`                     | Both apps in parallel |
| `pnpm dev:dashboard`           | Operator dashboard only (`:3000`) |
| `pnpm dev:portal`              | Customer portal only (`:3001`) |
| `pnpm db:generate`             | Prisma client |
| `pnpm db:migrate`              | Apply schema |
| `pnpm db:seed`                 | Populate representative fleet |
| `pnpm test:e2e`                | Playwright |
| `pnpm typecheck`               | Workspace-wide TS check |
| `pnpm build`                   | Production build of every package |
