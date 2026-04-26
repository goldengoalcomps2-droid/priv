"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS: Record<string, string> = {
  EXECUTIVE: "#0D8C7C",
  COMPACT: "#D97706",
  PREMIUM_SUV: "#7C3AED",
  ELECTRIC: "#DC2626",
  SUV: "#15803D",
  VAN: "#1D4ED8",
};

const LABEL: Record<string, string> = {
  EXECUTIVE: "Executive",
  COMPACT: "Compact",
  PREMIUM_SUV: "Premium SUV",
  ELECTRIC: "Electric",
  SUV: "SUV",
  VAN: "Van",
};

export function FleetMixDonut({ data }: { data: { vehicleClass: string; count: number }[] }) {
  const points = data.map((d) => ({ name: LABEL[d.vehicleClass] ?? d.vehicleClass, value: d.count, key: d.vehicleClass }));
  return (
    <ResponsiveContainer width="100%" height={320}>
      <PieChart>
        <Pie data={points} dataKey="value" nameKey="name" innerRadius={70} outerRadius={120} paddingAngle={1}>
          {points.map((p) => (
            <Cell key={p.key} fill={COLORS[p.key] ?? "#94A3B8"} />
          ))}
        </Pie>
        <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #E5E0D6", fontSize: 12 }} />
        <Legend verticalAlign="top" height={32} iconType="square" wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
