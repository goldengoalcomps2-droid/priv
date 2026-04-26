import { prisma, HireStatus, VehicleStatus, FineStatus } from "@fleetpro/db";
import { startOfMonth, endOfMonth, subMonths } from "date-fns";

/**
 * Centralised read-only queries the dashboard pages consume.
 * Every aggregate is computed live from the database — the dashboard
 * never hardcodes a number, so it works for any operator regardless of
 * fleet size.
 */

export async function fleetSummary() {
  const now = new Date();
  const [fleetSize, active, available, maintenance, returningToday, upcoming, motExpired, motDueSoon, taxExpired, hireableCount] =
    await Promise.all([
      prisma.vehicle.count({ where: { status: { not: VehicleStatus.SOLD } } }),
      prisma.hire.count({ where: { status: HireStatus.ACTIVE } }),
      prisma.vehicle.count({ where: { status: VehicleStatus.AVAILABLE } }),
      prisma.vehicle.count({ where: { status: VehicleStatus.MAINTENANCE } }),
      prisma.hire.count({
        where: {
          status: HireStatus.ACTIVE,
          endDate: { gte: new Date(now.toDateString()), lt: new Date(new Date(now.toDateString()).getTime() + 86_400_000) },
        },
      }),
      prisma.hire.count({
        where: { status: { in: [HireStatus.AWAITING_SIGNATURE, HireStatus.DRAFT] }, startDate: { gte: now, lte: new Date(now.getTime() + 14 * 86_400_000) } },
      }),
      prisma.vehicle.count({ where: { motDue: { lt: now }, status: { not: VehicleStatus.SOLD } } }),
      prisma.vehicle.count({ where: { motDue: { gte: now, lte: new Date(now.getTime() + 14 * 86_400_000) } } }),
      prisma.vehicle.count({ where: { taxDue: { lt: now }, status: { not: VehicleStatus.SOLD } } }),
      prisma.vehicle.count({ where: { status: { in: [VehicleStatus.AVAILABLE, VehicleStatus.RENTED] } } }),
    ]);
  return { fleetSize, active, available, maintenance, returningToday, upcoming, motExpired, motDueSoon, taxExpired, hireableCount };
}

export async function revenueThisMonth(): Promise<{ thisMonthGbpPence: number; lastMonthGbpPence: number; pctChange: number; monthLabel: string }> {
  const now = new Date();
  const thisFrom = startOfMonth(now);
  const thisTo = endOfMonth(now);
  const lastFrom = startOfMonth(subMonths(now, 1));
  const lastTo = endOfMonth(subMonths(now, 1));

  const sumOverWindow = async (from: Date, to: Date) => {
    const hires = await prisma.hire.findMany({
      where: { startDate: { lte: to }, endDate: { gte: from }, status: { in: [HireStatus.ACTIVE, HireStatus.COMPLETED] } },
      select: { startDate: true, endDate: true, totalGbp: true },
    });
    let total = 0;
    for (const h of hires) {
      const overlapStart = h.startDate > from ? h.startDate : from;
      const overlapEnd = h.endDate < to ? h.endDate : to;
      const overlap = Math.max(0, overlapEnd.getTime() - overlapStart.getTime());
      const span = Math.max(1, h.endDate.getTime() - h.startDate.getTime());
      total += Math.round(h.totalGbp * (overlap / span));
    }
    return total;
  };

  const [thisMonth, lastMonth] = await Promise.all([sumOverWindow(thisFrom, thisTo), sumOverWindow(lastFrom, lastTo)]);
  const pctChange = lastMonth === 0 ? 0 : (thisMonth - lastMonth) / lastMonth;
  return {
    thisMonthGbpPence: thisMonth,
    lastMonthGbpPence: lastMonth,
    pctChange,
    monthLabel: now.toLocaleDateString("en-GB", { month: "short" }),
  };
}

export async function revenueLastSixMonths() {
  const now = new Date();
  const months = Array.from({ length: 6 }, (_, i) => subMonths(now, 5 - i));
  const out: { label: string; revenueGbpPence: number }[] = [];
  for (const m of months) {
    const from = startOfMonth(m);
    const to = endOfMonth(m);
    const hires = await prisma.hire.findMany({
      where: { startDate: { lte: to }, endDate: { gte: from }, status: { in: [HireStatus.ACTIVE, HireStatus.COMPLETED] } },
      select: { startDate: true, endDate: true, totalGbp: true },
    });
    let total = 0;
    for (const h of hires) {
      const overlapStart = h.startDate > from ? h.startDate : from;
      const overlapEnd = h.endDate < to ? h.endDate : to;
      const overlap = Math.max(0, overlapEnd.getTime() - overlapStart.getTime());
      const span = Math.max(1, h.endDate.getTime() - h.startDate.getTime());
      total += Math.round(h.totalGbp * (overlap / span));
    }
    out.push({ label: m.toLocaleDateString("en-GB", { month: "short" }), revenueGbpPence: total });
  }
  return out;
}

export async function fleetMixByClass() {
  const groups = await prisma.vehicle.groupBy({
    by: ["vehicleClass"],
    _count: { _all: true },
    where: { status: { not: VehicleStatus.SOLD } },
  });
  return groups.map((g) => ({ vehicleClass: g.vehicleClass, count: g._count._all }));
}

export async function currentRentals(limit = 5) {
  return prisma.hire.findMany({
    where: { status: HireStatus.ACTIVE },
    orderBy: { startDate: "desc" },
    take: limit,
    include: {
      customer: { select: { fullName: true } },
      vehicle: { select: { make: true, model: true, trim: true, vrn: true } },
    },
  });
}

export async function alertsList(limit = 8) {
  const now = new Date();
  const soon = new Date(now.getTime() + 14 * 86_400_000);
  const motExpired = await prisma.vehicle.findMany({
    where: { motDue: { lt: now }, status: { not: VehicleStatus.SOLD } },
    orderBy: { motDue: "asc" },
    select: { id: true, make: true, model: true, trim: true, vrn: true, motDue: true },
    take: limit,
  });
  const motSoon = await prisma.vehicle.findMany({
    where: { motDue: { gte: now, lte: soon } },
    orderBy: { motDue: "asc" },
    select: { id: true, make: true, model: true, trim: true, vrn: true, motDue: true },
    take: limit,
  });
  return [
    ...motSoon.map((v) => ({ kind: "MOT_DUE_SOON" as const, ...v })),
    ...motExpired.map((v) => ({ kind: "MOT_EXPIRED" as const, ...v })),
  ].slice(0, limit);
}

export async function vehicleList() {
  return prisma.vehicle.findMany({
    orderBy: { createdAt: "asc" },
    include: {
      hires: {
        where: { status: HireStatus.ACTIVE },
        include: { customer: { select: { fullName: true } } },
        take: 1,
      },
    },
  });
}

export async function vehiclePnL() {
  const vehicles = await prisma.vehicle.findMany({
    include: { repairInvoices: { select: { totalGbp: true } }, hires: { select: { totalGbp: true, startDate: true, endDate: true, status: true } } },
  });
  const totals = vehicles.reduce(
    (acc, v) => {
      const repairs = v.repairInvoices.reduce((s, r) => s + r.totalGbp, 0);
      const cost = v.purchasePriceGbp + repairs;
      const hireRev = v.hires.reduce((s, h) => s + h.totalGbp, 0);
      const market = v.marketValueGbp ?? 0;
      const netSoFar = hireRev - cost + (v.salePriceGbp ?? 0);
      return {
        invested: acc.invested + cost,
        revenue: acc.revenue + hireRev,
        sold: acc.sold + (v.salePriceGbp ? 1 : 0),
        market: acc.market + market,
        salvage: acc.salvage + (v.salvageAdjustedGbp ?? 0),
        netSoFar: acc.netSoFar + netSoFar,
      };
    },
    { invested: 0, revenue: 0, sold: 0, market: 0, salvage: 0, netSoFar: 0 },
  );
  // Projected profit if we sold all remaining at current market
  const projected = totals.netSoFar + (totals.market - totals.salvage); // illustrative
  return { vehicles, totals: { ...totals, projected } };
}

export async function fleetUtilisation() {
  const [activeHires, hireable] = await Promise.all([
    prisma.hire.count({ where: { status: HireStatus.ACTIVE } }),
    prisma.vehicle.count({ where: { status: { in: [VehicleStatus.AVAILABLE, VehicleStatus.RENTED] } } }),
  ]);
  return { activeHires, hireable, utilisation: hireable === 0 ? 0 : activeHires / hireable };
}

export async function analyticsTotals() {
  const [totalRev, totalHires, totalDur] = await Promise.all([
    prisma.hire.aggregate({ _sum: { totalGbp: true }, where: { status: { in: [HireStatus.ACTIVE, HireStatus.COMPLETED] } } }),
    prisma.hire.count({ where: { status: { in: [HireStatus.ACTIVE, HireStatus.COMPLETED] } } }),
    prisma.hire.findMany({ where: { status: { in: [HireStatus.ACTIVE, HireStatus.COMPLETED] } }, select: { startDate: true, endDate: true } }),
  ]);
  const totalDays = totalDur.reduce((s, h) => s + Math.round((h.endDate.getTime() - h.startDate.getTime()) / 86_400_000), 0);
  return {
    totalRevenueGbpPence: totalRev._sum.totalGbp ?? 0,
    totalHires,
    avgRentalGbpPence: totalHires === 0 ? 0 : Math.round((totalRev._sum.totalGbp ?? 0) / totalHires),
    avgDurationDays: totalHires === 0 ? 0 : Math.round(totalDays / totalHires),
  };
}

export async function recentAgentActivity(limit = 12) {
  return prisma.agentActivity.findMany({ orderBy: { occurredAt: "desc" }, take: limit });
}

export async function pendingApprovals() {
  return prisma.approval.findMany({ where: { status: "PENDING" }, orderBy: { createdAt: "desc" }, take: 12 });
}

export async function activeFinesSummary() {
  const [unmatched, matched, charged, challengeReady] = await Promise.all([
    prisma.fine.count({ where: { status: FineStatus.RECEIVED } }),
    prisma.fine.count({ where: { status: FineStatus.MATCHED } }),
    prisma.fine.count({ where: { status: FineStatus.CHARGED_TO_CUSTOMER } }),
    prisma.fine.count({ where: { status: FineStatus.CHALLENGE_PREPARED } }),
  ]);
  return { unmatched, matched, charged, challengeReady };
}
