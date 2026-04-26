import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FleetPro — Customer onboarding",
  description: "Hire a vehicle from FleetPro: licence upload, identity, and consent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-GB">
      <body>
        <a href="#main" className="skip-link">Skip to main content</a>
        <header className="bg-white border-b border-rule px-6 py-4">
          <div className="max-w-2xl mx-auto flex items-center gap-3">
            <div aria-hidden className="h-9 w-9 rounded-lg bg-brand text-white grid place-items-center font-bold">F</div>
            <div>
              <div className="font-semibold leading-tight">FleetPro</div>
              <div className="text-xs text-ink-muted">Customer onboarding</div>
            </div>
          </div>
        </header>
        <main id="main" tabIndex={-1} className="max-w-2xl mx-auto px-6 py-8">
          {children}
        </main>
        <footer className="max-w-2xl mx-auto px-6 py-8 text-xs text-ink-muted">
          We process your data under UK GDPR Article 6(1)(b) (contract performance) and Article 9 only with your explicit consent.
          See our <a href="/privacy" className="text-brand underline">Privacy Notice</a> for retention periods, your rights of access,
          rectification, and erasure, and how to contact our DPO.
        </footer>
      </body>
    </html>
  );
}
