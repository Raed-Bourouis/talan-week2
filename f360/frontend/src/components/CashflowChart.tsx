'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

// Mock 90-day cashflow projection
const data = Array.from({ length: 90 }, (_, i) => {
  const baseBalance = 500000;
  const trend = i * 3000;
  const noise = Math.sin(i * 0.3) * 40000 + Math.cos(i * 0.7) * 20000;
  const balance = baseBalance + trend + noise;
  const day = new Date();
  day.setDate(day.getDate() + i);

  return {
    date: day.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
    balance: Math.round(balance),
    projected: i > 30,
  };
});

export default function CashflowChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10 }}
          interval={14}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          formatter={(value: number) =>
            `€${value.toLocaleString('fr-FR')}`
          }
        />
        <ReferenceLine
          x={data[30]?.date}
          stroke="#9ca3af"
          strokeDasharray="5 5"
          label={{ value: 'Aujourd\'hui', position: 'top', fontSize: 10 }}
        />
        <Area
          type="monotone"
          dataKey="balance"
          stroke="#3366ff"
          fill="url(#colorBalance)"
          strokeWidth={2}
        />
        <defs>
          <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3366ff" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#3366ff" stopOpacity={0} />
          </linearGradient>
        </defs>
      </AreaChart>
    </ResponsiveContainer>
  );
}
