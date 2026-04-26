"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CalendarDays,
  Car,
  PoundSterling,
  ClipboardList,
  AlertTriangle,
  Users,
  Wrench,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/timeline", label: "Timeline", icon: CalendarDays },
  { href: "/vehicles", label: "Vehicles", icon: Car },
  { href: "/vehicle-pl", label: "Vehicle P&L", icon: PoundSterling },
  { href: "/rentals", label: "Rentals", icon: ClipboardList },
  { href: "/fines", label: "Fines", icon: AlertTriangle },
  { href: "/customers", label: "Customers", icon: Users },
  { href: "/maintenance", label: "Maintenance", icon: Wrench },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside
      aria-label="Primary navigation"
      className="w-60 shrink-0 bg-sidebar text-white flex flex-col"
    >
      <div className="px-5 py-5 flex items-center gap-3">
        <div className="h-9 w-9 rounded-lg bg-brand text-white grid place-items-center font-bold text-sm" aria-hidden>
          F
        </div>
        <div>
          <div className="font-semibold leading-tight">FleetPro</div>
          <div className="text-xs text-sidebar-muted">Rental Management</div>
        </div>
      </div>

      <nav aria-label="Sections" className="flex-1 px-3 py-2 space-y-1">
        {NAV.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-sidebar-active text-white" : "text-white/85 hover:bg-sidebar-hover",
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="px-3 py-4 border-t border-white/10 flex items-center gap-3">
        <div className="h-8 w-8 rounded-full bg-white/10 grid place-items-center text-xs font-semibold" aria-hidden>
          AP
        </div>
        <div className="text-sm leading-tight">
          <div className="font-medium">Abraham P.</div>
          <div className="text-xs text-sidebar-muted">Fleet Manager</div>
        </div>
      </div>
    </aside>
  );
}
