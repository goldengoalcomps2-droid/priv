import { Search } from "lucide-react";
import { prisma } from "@fleetpro/db";
import { NewRentalDialog } from "@/components/new-rental/dialog";

export async function TopBar() {
  const [customers, vehicles] = await Promise.all([
    prisma.customer.findMany({
      where: { onboardingStatus: "VERIFIED", blacklisted: false },
      orderBy: { createdAt: "desc" },
      select: { id: true, fullName: true, email: true, postcode: true },
      take: 50,
    }),
    prisma.vehicle.findMany({
      where: { status: "AVAILABLE" },
      orderBy: [{ make: "asc" }, { model: "asc" }],
      select: { id: true, make: true, model: true, trim: true, vrn: true },
    }),
  ]);

  return (
    <header className="bg-page border-b border-rule px-8 py-4 flex items-center gap-4">
      <div className="flex-1" />
      <label className="relative">
        <span className="sr-only">Search vehicles, customers</span>
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-subtle" aria-hidden />
        <input
          type="search"
          placeholder="Search vehicles, customers..."
          className="w-80 rounded-lg border border-rule bg-card pl-9 pr-3 py-2 text-sm placeholder:text-ink-subtle"
        />
      </label>
      <NewRentalDialog customers={customers} availableVehicles={vehicles} />
    </header>
  );
}
