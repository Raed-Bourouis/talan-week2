'use client';

import { useState } from 'react';

function formatCurrency(n: number) {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
}

const cashflowData = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() + i);
  const inflow = 80000 + Math.random() * 40000;
  const outflow = 70000 + Math.random() * 50000;
  return {
    date: date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
    inflow: Math.round(inflow),
    outflow: Math.round(outflow),
    net: Math.round(inflow - outflow),
  };
});

export default function CashflowPage() {
  const [horizon] = useState(30);
  const totalIn = cashflowData.reduce((s, d) => s + d.inflow, 0);
  const totalOut = cashflowData.reduce((s, d) => s + d.outflow, 0);
  const balance = 1230000;
  const projected = balance + cashflowData.reduce((s, d) => s + d.net, 0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Trésorerie</h1>
        <p className="text-gray-500 mt-1">Projection de trésorerie à J+{horizon}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <p className="text-sm text-gray-500">Solde Actuel</p>
          <p className="text-2xl font-bold mt-1">{formatCurrency(balance)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Entrées (J+{horizon})</p>
          <p className="text-2xl font-bold mt-1 text-green-600">{formatCurrency(totalIn)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Sorties (J+{horizon})</p>
          <p className="text-2xl font-bold mt-1 text-red-600">{formatCurrency(totalOut)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Solde Projeté</p>
          <p className={`text-2xl font-bold mt-1 ${projected > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(projected)}
          </p>
        </div>
      </div>

      {/* Mini chart bars */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Flux Quotidiens</h2>
        <div className="space-y-2 max-h-[500px] overflow-y-auto">
          {cashflowData.map((d, i) => (
            <div key={i} className="flex items-center gap-4 text-sm">
              <span className="w-16 text-gray-500 shrink-0">{d.date}</span>
              <div className="flex-1 flex items-center gap-2">
                <div className="flex-1 flex gap-1">
                  <div className="bg-green-400 h-4 rounded" style={{ width: `${(d.inflow / 130000) * 100}%` }} />
                </div>
                <div className="flex-1 flex gap-1">
                  <div className="bg-red-400 h-4 rounded" style={{ width: `${(d.outflow / 130000) * 100}%` }} />
                </div>
              </div>
              <span className={`w-24 text-right font-medium ${d.net > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {d.net > 0 ? '+' : ''}{formatCurrency(d.net)}
              </span>
            </div>
          ))}
        </div>
        <div className="flex gap-6 mt-4 text-xs text-gray-500">
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-400 rounded" /> Entrées</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-400 rounded" /> Sorties</span>
        </div>
      </div>
    </div>
  );
}
