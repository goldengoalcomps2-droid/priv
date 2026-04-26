import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { TopBar } from "@/components/layout/top-bar";

export const metadata: Metadata = {
  title: "FleetPro — Rental Management",
  description: "Multi-agent dashboard for UK salvage vehicle hire operations",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-GB">
      <body className="bg-page text-ink">
        <a href="#main" className="skip-link">Skip to main content</a>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <TopBar />
            <main id="main" tabIndex={-1} className="flex-1 px-8 py-6">
              {children}
            </main>
          </div>
        </div>
        <div id="agent-live" aria-live="polite" aria-atomic="true" className="sr-only" />
      </body>
    </html>
  );
}
