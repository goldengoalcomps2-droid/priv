import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "#F4F1EA",
        brand: { DEFAULT: "#0D8C7C", hover: "#0A6F62", soft: "#E0F2EF", ink: "#063E37" },
        ink: { DEFAULT: "#0E1A24", muted: "#52606D", subtle: "#7A8B9A" },
        rule: "#E5E0D6",
        card: "#FFFFFF",
        bad: { DEFAULT: "#B91C1C", soft: "#FEE2E2" },
      },
    },
  },
  plugins: [],
};

export default config;
