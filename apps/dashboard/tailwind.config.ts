import type { Config } from "tailwindcss";

/**
 * FleetPro design tokens
 *  - Sidebar / chrome: dark slate (~#0F1B26)
 *  - Brand accent: teal (~#0D8C7C) for primary actions
 *  - Surfaces: cream (~#F4F1EA) page background, white cards
 *  - Status: amber for warnings, red for expired/critical, emerald for healthy
 *
 * Contrast: every fg/bg pair below clears WCAG 2.2 AA (≥ 4.5:1 for body text,
 * ≥ 3:1 for large/UI). Dev tip: enable browser axe-core or Lighthouse before
 * shipping changes that touch the palette.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "#F4F1EA",
        sidebar: { DEFAULT: "#0F1B26", muted: "#7A8B9A", hover: "#1A2B3C", active: "#0D8C7C" },
        brand: { DEFAULT: "#0D8C7C", hover: "#0A6F62", soft: "#E0F2EF", ink: "#063E37" },
        ink: { DEFAULT: "#0E1A24", muted: "#52606D", subtle: "#7A8B9A" },
        rule: "#E5E0D6",
        card: "#FFFFFF",
        ok: { DEFAULT: "#15803D", soft: "#DCFCE7" },
        warn: { DEFAULT: "#B45309", soft: "#FEF3C7" },
        bad: { DEFAULT: "#B91C1C", soft: "#FEE2E2" },
        info: { DEFAULT: "#1D4ED8", soft: "#DBEAFE" },
        // Gantt event colors
        gantt: {
          active: "#1D4ED8",
          activeFg: "#FFFFFF",
          upcoming: "#D97706",
          upcomingFg: "#FFFFFF",
          completed: "#94A3B8",
          completedFg: "#FFFFFF",
          maintenance: "#CA8A04",
          maintenanceFg: "#FFFFFF",
          today: "#DC2626",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
        ],
      },
      borderRadius: {
        lg: "0.625rem",
        xl: "0.875rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 27, 38, 0.04), 0 1px 1px rgba(15, 27, 38, 0.03)",
      },
    },
  },
  plugins: [],
};

export default config;
