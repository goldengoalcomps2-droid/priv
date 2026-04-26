"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function RevenueBarChart({ data }: { data: { label: string; revenueGbpPence: number }[] }) {
  const points = data.map((d) => ({ label: d.label, revenue: Math.round(d.revenueGbpPence / 100) }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={points} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="#E5E0D6" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" stroke="#7A8B9A" fontSize={12} tickLine={false} axisLine={false} />
        <YAxis
          stroke="#7A8B9A"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          width={70}
          tickFormatter={(v: number) => v.toLocaleString("en-GB")}
        />
        <Tooltip
          cursor={{ fill: "rgba(13,140,124,0.06)" }}
          contentStyle={{ borderRadius: 8, border: "1px solid #E5E0D6", fontSize: 12 }}
          formatter={(v: number) => [`£${v.toLocaleString("en-GB")}`, "Revenue"]}
        />
        <Bar dataKey="revenue" fill="#0D8C7C" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
