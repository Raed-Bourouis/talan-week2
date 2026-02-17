'use client';

import { useState } from 'react';

function formatCurrency(n: number) {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
}

type SimType = 'budget_variation' | 'cashflow_projection' | 'monte_carlo' | 'renegotiation';

const simTypes: { key: SimType; label: string; icon: string; desc: string }[] = [
  { key: 'budget_variation', label: 'Variation Budgétaire', icon: '📊', desc: 'Simuler l\'impact de coupes/augmentations budgétaires' },
  { key: 'cashflow_projection', label: 'Projection Trésorerie', icon: '💹', desc: 'Projeter le cashflow à J+90 avec volatilité' },
  { key: 'monte_carlo', label: 'Monte Carlo', icon: '🎲', desc: 'Analyse probabiliste avec 10 000 itérations' },
  { key: 'renegotiation', label: 'Renégociation Contrat', icon: '📝', desc: 'Évaluer les gains d\'une renégociation' },
];

export default function SimulationsPage() {
  const [selected, setSelected] = useState<SimType>('budget_variation');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const runSimulation = async () => {
    setRunning(true);
    setResult(null);
    try {
      const res = await fetch('http://localhost:8000/api/v1/simulate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          simulation_type: selected,
          parameters: getParams(selected),
        }),
      });
      const data = await res.json();
      setResult(data.results || data);
    } catch {
      setResult({ error: 'Erreur lors de la simulation' });
    }
    setRunning(false);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Simulations</h1>
        <p className="text-gray-500 mt-1">Moteur de simulation financière multi-scénarios</p>
      </div>

      {/* Simulation type selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {simTypes.map((s) => (
          <button
            key={s.key}
            onClick={() => { setSelected(s.key); setResult(null); }}
            className={`card text-left transition-all ${selected === s.key ? 'ring-2 ring-blue-500 border-blue-200' : 'hover:border-gray-300'}`}
          >
            <span className="text-2xl">{s.icon}</span>
            <p className="font-semibold mt-2">{s.label}</p>
            <p className="text-xs text-gray-500 mt-1">{s.desc}</p>
          </button>
        ))}
      </div>

      {/* Run button */}
      <div className="flex items-center gap-4">
        <button
          onClick={runSimulation}
          disabled={running}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {running ? '⏳ Simulation en cours...' : '▶ Lancer la Simulation'}
        </button>
        <span className="text-sm text-gray-500">Type: {simTypes.find(s => s.key === selected)?.label}</span>
      </div>

      {/* Results */}
      {result && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Résultats</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {Object.entries(result).filter(([, v]) => typeof v === 'number').slice(0, 6).map(([k, v]) => (
              <div key={k} className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs text-gray-500 uppercase">{k.replace(/_/g, ' ')}</p>
                <p className="text-xl font-bold mt-1">
                  {typeof v === 'number' && Math.abs(v as number) > 100
                    ? formatCurrency(v as number)
                    : typeof v === 'number' && Math.abs(v as number) < 1
                    ? `${((v as number) * 100).toFixed(1)}%`
                    : String(v)}
                </p>
              </div>
            ))}
          </div>
          <details className="text-sm">
            <summary className="cursor-pointer text-blue-600 hover:underline">Voir le JSON complet</summary>
            <pre className="mt-2 bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto max-h-96 text-xs">
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}

function getParams(type: SimType): Record<string, unknown> {
  switch (type) {
    case 'budget_variation':
      return { base_budget: 11450000, variation_pct: [-15, -10, -5, 0, 5, 10, 15], categories: ['OPEX', 'CAPEX', 'HR', 'IT', 'Marketing'] };
    case 'cashflow_projection':
      return { initial_balance: 1230000, daily_inflow_mean: 95000, daily_outflow_mean: 88000, volatility: 0.15, horizon_days: 90 };
    case 'monte_carlo':
      return { base_value: 5000000, mean_return: 0.06, volatility: 0.20, horizon_years: 1, iterations: 10000 };
    case 'renegotiation':
      return { current_annual_cost: 500000, contract_duration_years: 3, proposed_discount_pct: 10, inflation_rate: 0.03, exit_penalty: 15000 };
  }
}
