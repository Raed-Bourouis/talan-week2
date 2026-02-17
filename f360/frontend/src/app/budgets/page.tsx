'use client';

import { useState } from 'react';

const budgetData = [
  { category: 'OPEX', planned: 5000000, actual: 5900000, currency: 'EUR' },
  { category: 'CAPEX', planned: 2000000, actual: 3100000, currency: 'EUR' },
  { category: 'HR', planned: 3000000, actual: 2800000, currency: 'EUR' },
  { category: 'IT', planned: 1000000, actual: 600000, currency: 'EUR' },
  { category: 'Marketing', planned: 450000, actual: 520000, currency: 'EUR' },
];

function formatCurrency(n: number) {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
}

function gapPct(planned: number, actual: number) {
  if (planned === 0) return 0;
  return ((actual - planned) / planned) * 100;
}

function severityBadge(pct: number) {
  const abs = Math.abs(pct);
  if (abs < 5) return <span className="badge-success">Nominal</span>;
  if (abs < 15) return <span className="badge-warning">Warning</span>;
  return <span className="badge-danger">Critique</span>;
}

export default function BudgetsPage() {
  const [year] = useState(2025);
  const totalPlanned = budgetData.reduce((s, b) => s + b.planned, 0);
  const totalActual = budgetData.reduce((s, b) => s + b.actual, 0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Budgets</h1>
        <p className="text-gray-500 mt-1">Suivi de l&apos;exécution budgétaire — FY {year}</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <p className="text-sm text-gray-500">Budget Prévu</p>
          <p className="text-2xl font-bold mt-1">{formatCurrency(totalPlanned)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Réalisé</p>
          <p className="text-2xl font-bold mt-1">{formatCurrency(totalActual)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Écart Global</p>
          <p className={`text-2xl font-bold mt-1 ${totalActual > totalPlanned ? 'text-red-600' : 'text-green-600'}`}>
            {gapPct(totalPlanned, totalActual) > 0 ? '+' : ''}{gapPct(totalPlanned, totalActual).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Budget table */}
      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="pb-3 text-sm font-medium text-gray-500">Catégorie</th>
              <th className="pb-3 text-sm font-medium text-gray-500 text-right">Prévu</th>
              <th className="pb-3 text-sm font-medium text-gray-500 text-right">Réalisé</th>
              <th className="pb-3 text-sm font-medium text-gray-500 text-right">Écart</th>
              <th className="pb-3 text-sm font-medium text-gray-500 text-right">Sévérité</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {budgetData.map((b) => {
              const pct = gapPct(b.planned, b.actual);
              return (
                <tr key={b.category} className="hover:bg-gray-50">
                  <td className="py-3 font-medium">{b.category}</td>
                  <td className="py-3 text-right text-gray-600">{formatCurrency(b.planned)}</td>
                  <td className="py-3 text-right text-gray-600">{formatCurrency(b.actual)}</td>
                  <td className={`py-3 text-right font-medium ${pct > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {pct > 0 ? '+' : ''}{pct.toFixed(1)}%
                  </td>
                  <td className="py-3 text-right">{severityBadge(pct)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Visual bars */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Répartition Budgétaire</h2>
        <div className="space-y-4">
          {budgetData.map((b) => {
            const pct = (b.actual / b.planned) * 100;
            const barColor = pct > 115 ? 'bg-red-500' : pct > 105 ? 'bg-yellow-500' : 'bg-blue-500';
            return (
              <div key={b.category}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium">{b.category}</span>
                  <span className="text-gray-500">{pct.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div className={`${barColor} h-3 rounded-full transition-all`} style={{ width: `${Math.min(pct, 100)}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
