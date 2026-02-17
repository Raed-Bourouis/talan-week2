'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const data = [
  { category: 'OPEX', planned: 850000, actual: 920000 },
  { category: 'CAPEX', planned: 500000, actual: 430000 },
  { category: 'HR', planned: 620000, actual: 650000 },
  { category: 'IT', planned: 300000, actual: 340000 },
  { category: 'Marketing', planned: 180000, actual: 160000 },
];

export default function BudgetChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="category" tick={{ fontSize: 12 }} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          formatter={(value: number) =>
            `€${value.toLocaleString('fr-FR')}`
          }
        />
        <Legend />
        <Bar dataKey="planned" name="Prévu" fill="#93c5fd" radius={[4, 4, 0, 0]} />
        <Bar dataKey="actual" name="Réalisé" fill="#3366ff" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
