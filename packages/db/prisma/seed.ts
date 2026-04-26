/**
 * FleetPro seed — produces a representative UK salvage hire fleet.
 *
 * The dashboard never hardcodes numbers; every widget queries live data.
 * This seed just gives a fresh database something realistic to render.
 *
 * Deterministic: re-running yields the same dataset.
 */
import {
  PrismaClient,
  VehicleClass,
  FuelType,
  OwnershipType,
  VehicleStatus,
  RagStatus,
  HireStatus,
  FineStatus,
  OnboardingStatus,
  AgentName,
  ActivityKind,
  ApprovalKind,
  ApprovalStatus,
  ProcurementSource,
  DamageCategory,
  ProcurementOutcome,
  MotResult,
  UserRole,
} from "@prisma/client";

const prisma = new PrismaClient();

// Deterministic PRNG so re-seeding is stable
let _seed = 42;
const rand = () => {
  _seed = (_seed * 9301 + 49297) % 233280;
  return _seed / 233280;
};
const pick = <T>(xs: readonly T[]): T => xs[Math.floor(rand() * xs.length)]!;
const between = (lo: number, hi: number) => Math.floor(lo + rand() * (hi - lo));
const daysAgo = (n: number) => new Date(Date.now() - n * 86_400_000);
const daysAhead = (n: number) => new Date(Date.now() + n * 86_400_000);

// ─── Reference data ────────────────────────────────────────────────────

const VEHICLE_CATALOG: Array<{
  make: string;
  model: string;
  trim: string;
  cls: VehicleClass;
  fuel: FuelType;
  baseRate: number; // £/month in pence
  basePrice: number; // £ in pence
}> = [
  { make: "Mercedes-Benz", model: "A 200", trim: "AMG Line Executive", cls: "EXECUTIVE", fuel: "PETROL", baseRate: 170_000, basePrice: 1_760_000 },
  { make: "Seat", model: "Leon", trim: "FR Technology Ecotsi", cls: "COMPACT", fuel: "PETROL", baseRate: 90_000, basePrice: 1_240_000 },
  { make: "Seat", model: "Leon", trim: "FR Technology TSI S-", cls: "COMPACT", fuel: "PETROL", baseRate: 90_000, basePrice: 1_010_000 },
  { make: "Tesla", model: "Model 3", trim: "Performance Dual", cls: "ELECTRIC", fuel: "ELECTRIC", baseRate: 250_000, basePrice: 6_500_000 },
  { make: "Bentley", model: "Bentayga", trim: "V8 Auto 4.0", cls: "PREMIUM_SUV", fuel: "PETROL", baseRate: 250_000, basePrice: 8_130_000 },
  { make: "Vauxhall", model: "Astra", trim: "Elite Nav Turbo S/S", cls: "COMPACT", fuel: "PETROL", baseRate: 90_000, basePrice: 920_000 },
  { make: "Volvo", model: "V40", trim: "Inscriptionc Edition D", cls: "COMPACT", fuel: "DIESEL", baseRate: 90_000, basePrice: 950_000 },
  { make: "Toyota", model: "Aygo", trim: "X-Play VVT-I CVT 1.0", cls: "COMPACT", fuel: "PETROL", baseRate: 80_000, basePrice: 720_000 },
  { make: "Audi", model: "A3", trim: "S Line 40 TFSIe Auto", cls: "EXECUTIVE", fuel: "PHEV", baseRate: 160_000, basePrice: 2_180_000 },
  { make: "Audi", model: "Q8", trim: "S Line 50 TDI Quattro", cls: "PREMIUM_SUV", fuel: "DIESEL", baseRate: 240_000, basePrice: 4_650_000 },
  { make: "BMW", model: "Mini Cooper S", trim: "Sport 5Dr Auto", cls: "COMPACT", fuel: "PETROL", baseRate: 110_000, basePrice: 1_580_000 },
  { make: "BMW", model: "Mini Cooper S", trim: "Sport Cabriolet", cls: "COMPACT", fuel: "PETROL", baseRate: 120_000, basePrice: 1_680_000 },
  { make: "Range Rover", model: "Evoque", trim: "HSE Dynamic", cls: "SUV", fuel: "DIESEL", baseRate: 195_000, basePrice: 2_990_000 },
  { make: "Ford", model: "Transit", trim: "Custom Limited", cls: "VAN", fuel: "DIESEL", baseRate: 130_000, basePrice: 1_840_000 },
  { make: "Volkswagen", model: "Golf", trim: "GTI Performance", cls: "COMPACT", fuel: "PETROL", baseRate: 115_000, basePrice: 2_050_000 },
];

const FIRST_NAMES = ["Freddie", "Lucas", "Esme", "Maya", "Lily", "Jacob", "James", "Liam", "Daniel", "Olivia", "Sophie", "Harry", "Amelia", "Oscar", "Ava", "Charlie", "Mia", "Leo", "Isla", "Theo"];
const LAST_NAMES = ["Harris", "Hall", "Patel", "Lewis", "Jones", "Smith", "Walker", "Khan", "Wright", "Edwards", "Green", "Hill", "Cole", "Hughes", "Reed", "Cox", "Ward", "Bell", "Wood", "Foster"];
const STREETS = ["Oak Lane", "High Street", "Mill Road", "Church Lane", "Park Avenue", "Queens Road", "Victoria Street", "Albert Drive", "King's Way", "Manor Close"];
const CITIES = ["London", "Manchester", "Birmingham", "Leeds", "Bristol", "Liverpool", "Sheffield", "Newcastle"];
const COUNCILS = ["Lambeth Council", "Westminster City Council", "Camden Council", "Manchester City Council", "Birmingham City Council", "Transport for London"];

const randPlate = () => {
  const letters = "ABCDEFGHJKLMNOPRSTUVWXYZ";
  const a = `${letters[between(0, 24)]}${letters[between(0, 24)]}${between(10, 99)}`;
  const b = `${letters[between(0, 24)]}${letters[between(0, 24)]}${letters[between(0, 24)]}`;
  return `${a} ${b}`;
};

// ─── Seed ─────────────────────────────────────────────────────────────

async function main() {
  console.log("→ wiping existing data");
  await prisma.$transaction([
    prisma.agentActivity.deleteMany(),
    prisma.approval.deleteMany(),
    prisma.fine.deleteMany(),
    prisma.repairInvoice.deleteMany(),
    prisma.serviceRecord.deleteMany(),
    prisma.motRecord.deleteMany(),
    prisma.document.deleteMany(),
    prisma.hire.deleteMany(),
    prisma.licenceImage.deleteMany(),
    prisma.customer.deleteMany(),
    prisma.procurementOpportunity.deleteMany(),
    prisma.procurementStrategy.deleteMany(),
    prisma.vehicle.deleteMany(),
    prisma.user.deleteMany(),
  ]);

  console.log("→ users");
  const owner = await prisma.user.create({
    data: { email: "abraham@fleetpro.local", name: "Abraham P.", role: UserRole.OWNER },
  });

  console.log("→ vehicles");
  const fleetSize = 40;
  const vehicles = await Promise.all(
    Array.from({ length: fleetSize }).map(async (_, i) => {
      const cat = VEHICLE_CATALOG[i % VEHICLE_CATALOG.length]!;
      const yom = between(2017, 2022);
      const purchaseDate = daysAgo(between(120, 2200));
      const mileage = between(2000, 90_000);
      const motDue = rand() < 0.4 ? daysAgo(between(1, 60)) : daysAhead(between(15, 320));
      const taxDue = rand() < 0.25 ? daysAgo(between(1, 30)) : daysAhead(between(15, 360));
      return prisma.vehicle.create({
        data: {
          vrn: randPlate(),
          make: cat.make,
          model: cat.model,
          trim: cat.trim,
          yearOfManufacture: yom,
          vehicleClass: cat.cls,
          fuelType: cat.fuel,
          ownership: pick([OwnershipType.OWN, OwnershipType.OWN, OwnershipType.OWN, OwnershipType.PCP, OwnershipType.LEASE_PURCHASE]),
          v5cReference: String(between(10_000_000_000, 99_999_999_999)),
          purchasePriceGbp: cat.basePrice + between(-150_000, 150_000),
          purchaseDate,
          purchaseMileage: between(0, 30_000),
          status: VehicleStatus.AVAILABLE, // will be flipped by hire creation
          currentMileage: mileage,
          monthlyRateGbp: cat.baseRate,
          ragStatus: pick([RagStatus.GREEN, RagStatus.GREEN, RagStatus.GREEN, RagStatus.AMBER, RagStatus.RED]),
          motDue,
          taxDue,
          insuranceDue: daysAhead(between(30, 360)),
          marketValueGbp: cat.basePrice + between(-200_000, 100_000),
          salvageAdjustedGbp: Math.floor((cat.basePrice + between(-200_000, 100_000)) * 0.85),
          valuationProvider: "cap-hpi",
          valuationAt: daysAgo(between(1, 14)),
        },
      });
    }),
  );

  console.log("→ flag a couple in maintenance / cleaning");
  await prisma.vehicle.update({ where: { id: vehicles[0]!.id }, data: { status: VehicleStatus.MAINTENANCE } });
  await prisma.vehicle.update({ where: { id: vehicles[3]!.id }, data: { status: VehicleStatus.CLEANING } });
  await prisma.vehicle.update({ where: { id: vehicles[4]!.id }, data: { status: VehicleStatus.CLEANING } });

  console.log("→ customers");
  const numCustomers = 60;
  const customers = await Promise.all(
    Array.from({ length: numCustomers }).map((_, i) =>
      prisma.customer.create({
        data: {
          fullName: `${pick(FIRST_NAMES)} ${pick(LAST_NAMES)}`,
          dateOfBirth: daysAgo(between(20, 60) * 365),
          email: `customer${i}@example.com`,
          phone: `07${between(100_000_000, 999_999_999)}`,
          addressLine1: `${between(1, 200)} ${pick(STREETS)}`,
          city: pick(CITIES),
          postcode: `${pick(["SW", "N", "E", "M", "B"])}${between(1, 19)} ${between(1, 9)}${pick(["AA", "BB", "CD", "EF"])}`,
          licenceNumber: `LIC${between(100000, 999999)}${i}`,
          licenceIssued: daysAgo(between(365, 3650)),
          licenceExpires: daysAhead(between(120, 3500)),
          licenceCategories: ["B"],
          licencePoints: rand() < 0.85 ? 0 : between(3, 9),
          consentText: "I consent to FleetPro processing my personal data per the Privacy Notice.",
          consentSignedAt: daysAgo(between(1, 540)),
          consentSignatureSvg: "<svg xmlns='http://www.w3.org/2000/svg'/>",
          consentIpAddress: `92.0.${between(0, 255)}.${between(0, 255)}`,
          addressMatchesLicence: rand() < 0.92,
          livenessScore: 0.85 + rand() * 0.14,
          onboardingStatus: rand() < 0.9 ? OnboardingStatus.VERIFIED : OnboardingStatus.PENDING_REVIEW,
        },
      }),
    ),
  );

  console.log("→ hires (active, upcoming, completed)");
  const numHires = 120;
  for (let i = 0; i < numHires; i++) {
    const v = pick(vehicles);
    const c = pick(customers);
    // Mix: 20% completed in last 90d, 25% active now, 15% upcoming, 40% historical
    const r = rand();
    let start: Date, end: Date, status: HireStatus;
    if (r < 0.2) {
      start = daysAgo(between(80, 180));
      end = new Date(start.getTime() + between(30, 90) * 86_400_000);
      status = HireStatus.COMPLETED;
    } else if (r < 0.45) {
      start = daysAgo(between(1, 30));
      end = daysAhead(between(20, 90));
      status = HireStatus.ACTIVE;
    } else if (r < 0.6) {
      start = daysAhead(between(2, 14));
      end = daysAhead(between(35, 120));
      status = HireStatus.AWAITING_SIGNATURE;
    } else {
      start = daysAgo(between(180, 540));
      end = new Date(start.getTime() + between(30, 90) * 86_400_000);
      status = HireStatus.COMPLETED;
    }
    const months = Math.max(1, Math.round((end.getTime() - start.getTime()) / (30 * 86_400_000)));
    const total = v.monthlyRateGbp * months;
    await prisma.hire.create({
      data: {
        customerId: c.id,
        vehicleId: v.id,
        startDate: start,
        endDate: end,
        weeklyRateGbp: Math.floor(v.monthlyRateGbp / 4),
        totalGbp: total,
        status,
        signedAt: status === HireStatus.ACTIVE || status === HireStatus.COMPLETED ? new Date(start.getTime() - 86_400_000) : null,
      },
    });
  }

  // Sync vehicle status to active hires
  console.log("→ syncing vehicle.status to active hires");
  const activeHires = await prisma.hire.findMany({ where: { status: HireStatus.ACTIVE }, distinct: ["vehicleId"], select: { vehicleId: true } });
  await prisma.vehicle.updateMany({
    where: { id: { in: activeHires.map((h) => h.vehicleId) }, status: VehicleStatus.AVAILABLE },
    data: { status: VehicleStatus.RENTED },
  });

  console.log("→ MOT records + service records");
  for (const v of vehicles.slice(0, 30)) {
    await prisma.motRecord.create({
      data: {
        vehicleId: v.id,
        testedAt: daysAgo(between(30, 360)),
        expiresAt: v.motDue ?? daysAhead(60),
        result: pick([MotResult.PASS, MotResult.PASS, MotResult.PASS, MotResult.FAIL]),
        mileage: v.currentMileage - between(500, 5000),
        defects: { dangerous: [], major: [], minor: [], advisory: [] },
        certificateNumber: String(between(100_000_000_000, 999_999_999_999)),
      },
    });
  }

  console.log("→ fines");
  for (let i = 0; i < 18; i++) {
    const v = pick(vehicles);
    const offenceAt = daysAgo(between(1, 90));
    // Find an active hire at offence time on that vehicle
    const hire = await prisma.hire.findFirst({
      where: { vehicleId: v.id, startDate: { lte: offenceAt }, endDate: { gte: offenceAt } },
    });
    await prisma.fine.create({
      data: {
        pcnNumber: `PCN${between(10_000_000, 99_999_999)}${i}`,
        issuingAuthority: pick(COUNCILS),
        vrn: v.vrn,
        vehicleId: v.id,
        hireId: hire?.id,
        customerId: hire?.customerId,
        offenceAt,
        location: `${pick(STREETS)}, ${pick(CITIES)}`,
        amountGbp: pick([6500, 8000, 13_000, 16_000]),
        status: hire ? FineStatus.MATCHED : FineStatus.RECEIVED,
        noticePhotoS3Key: `pcn-photos/seed-${i}.jpg`,
      },
    });
  }

  console.log("→ procurement opportunities");
  for (let i = 0; i < 12; i++) {
    const cat = pick(VEHICLE_CATALOG);
    await prisma.procurementOpportunity.create({
      data: {
        source: pick([ProcurementSource.COPART, ProcurementSource.IAA, ProcurementSource.AUTOTRADER, ProcurementSource.EBAY]),
        externalListingId: `LIST-${between(1_000_000, 9_999_999)}-${i}`,
        url: `https://example.com/listing/${i}`,
        make: cat.make,
        model: cat.model,
        yearOfManufacture: between(2017, 2022),
        mileage: between(20_000, 90_000),
        damageCategory: pick([DamageCategory.CAT_N, DamageCategory.CAT_S, DamageCategory.UNRECORDED]),
        askingPriceGbp: Math.floor(cat.basePrice * (0.4 + rand() * 0.3)),
        recommendedBidGbp: Math.floor(cat.basePrice * (0.35 + rand() * 0.25)),
        matchScore: 0.55 + rand() * 0.4,
        rationale: `Matches strategy: make=${cat.make}, mileage within band, damage cat acceptable.`,
        outcome: ProcurementOutcome.WATCHING,
      },
    });
  }
  await prisma.procurementStrategy.create({
    data: {
      name: "Default executive saloon strategy",
      makes: ["Audi", "BMW", "Mercedes-Benz"],
      models: [],
      maxBidGbp: 1_500_000,
      minYear: 2018,
      maxMileage: 80_000,
      damageCategories: [DamageCategory.CAT_N, DamageCategory.CAT_S],
    },
  });

  console.log("→ agent activity feed");
  const agentSamples: Array<{ agent: AgentName; summary: string; tool: string }> = [
    { agent: "CUSTOMER_ONBOARDING", summary: "Verified new customer — DVLA fields match address", tool: "ocr.parseLicence" },
    { agent: "FINES_AND_PCN", summary: "Matched PCN to active hire and prepared admin-fee invoice", tool: "fines.matchToHire" },
    { agent: "FLEET_MAINTENANCE", summary: "MOT due in 7 days — calendar reminder created", tool: "calendar.createEvent" },
    { agent: "PROCUREMENT", summary: "New Copart listing matches strategy at 78% confidence", tool: "procurement.scanFeed" },
    { agent: "ANALYTICS_AND_DEFLEET", summary: "Refreshed CAP HPI valuations across fleet", tool: "valuations.refresh" },
    { agent: "HIRE_AND_AGREEMENT", summary: "Detected timeline collision on drag-edit; suggested alternate slot", tool: "hires.checkCollision" },
  ];
  for (const s of agentSamples) {
    await prisma.agentActivity.create({
      data: {
        agent: s.agent,
        kind: ActivityKind.TOOL_CALL,
        summary: s.summary,
        toolName: s.tool,
        toolDurationMs: between(80, 1800),
        occurredAt: daysAgo(rand() * 3),
      },
    });
  }

  console.log("→ pending approvals");
  const someHire = await prisma.hire.findFirst({ where: { status: HireStatus.AWAITING_SIGNATURE } });
  const someFine = await prisma.fine.findFirst();
  const someOpp = await prisma.procurementOpportunity.findFirst();
  if (someHire) {
    await prisma.approval.create({
      data: {
        agent: AgentName.HIRE_AND_AGREEMENT,
        kind: ApprovalKind.SEND_HIRE_AGREEMENT,
        title: "Send hire agreement for signature",
        proposedAction: { tool: "adobeSign.sendForSignature", args: { hireId: someHire.id } },
        rationale: "Hire is awaiting signature; customer onboarding is verified and vehicle is available.",
        hireId: someHire.id,
        status: ApprovalStatus.PENDING,
      },
    });
  }
  if (someFine) {
    await prisma.approval.create({
      data: {
        agent: AgentName.FINES_AND_PCN,
        kind: ApprovalKind.SUBMIT_PCN_CHALLENGE,
        title: "Submit Transfer of Liability for PCN",
        proposedAction: { tool: "pcn.openChallengeUrl", args: { fineId: someFine.id } },
        rationale: "Hire agreement matches PCN datetime; ToL pack assembled; ready for operator review.",
        fineId: someFine.id,
        status: ApprovalStatus.PENDING,
      },
    });
  }
  if (someOpp) {
    await prisma.approval.create({
      data: {
        agent: AgentName.PROCUREMENT,
        kind: ApprovalKind.PLACE_PROCUREMENT_BID,
        title: `Bid on ${someOpp.make} ${someOpp.model}`,
        proposedAction: { tool: "procurement.placeBid", args: { opportunityId: someOpp.id, bidGbp: someOpp.recommendedBidGbp } },
        rationale: "Listing matches active strategy; recommended bid is below max threshold.",
        procurementOpportunityId: someOpp.id,
        status: ApprovalStatus.PENDING,
      },
    });
  }

  console.log("✓ seed complete");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
