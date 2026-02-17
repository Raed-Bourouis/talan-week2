'use client';

const contracts = [
  { ref: 'CTR-2025-001', title: 'Maintenance IT Capgemini', counterparty: 'Capgemini', type: 'service', amount: 500000, status: 'active', start: '2024-03-01', end: '2026-03-01', daysToExpiry: 30 },
  { ref: 'CTR-2025-002', title: 'Licence ERP SAP', counterparty: 'SAP France', type: 'supply', amount: 320000, status: 'active', start: '2024-01-15', end: '2027-01-15', daysToExpiry: 365 },
  { ref: 'CTR-2025-003', title: 'Consulting Sopra Steria', counterparty: 'Sopra Steria', type: 'consulting', amount: 250000, status: 'active', start: '2025-06-01', end: '2026-06-01', daysToExpiry: 45 },
  { ref: 'CTR-2025-004', title: 'Leasing Flotte Véhicules', counterparty: 'ALD Automotive', type: 'lease', amount: 180000, status: 'active', start: '2023-09-01', end: '2026-09-01', daysToExpiry: 210 },
  { ref: 'CTR-2025-005', title: 'Assurance Responsabilité', counterparty: 'AXA', type: 'service', amount: 95000, status: 'expired', start: '2023-01-01', end: '2025-12-31', daysToExpiry: -48 },
  { ref: 'CTR-2025-006', title: 'Hébergement Cloud AWS', counterparty: 'AWS', type: 'service', amount: 420000, status: 'active', start: '2025-01-01', end: '2028-01-01', daysToExpiry: 720 },
];

function formatCurrency(n: number) {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
}

function statusBadge(status: string) {
  if (status === 'active') return <span className="badge-success">Actif</span>;
  if (status === 'expired') return <span className="badge-danger">Expiré</span>;
  return <span className="badge-warning">{status}</span>;
}

function expiryBadge(days: number) {
  if (days < 0) return <span className="text-xs text-red-600 font-medium">Expiré</span>;
  if (days <= 30) return <span className="text-xs text-red-600 font-medium">⚠ {days}j</span>;
  if (days <= 90) return <span className="text-xs text-yellow-600 font-medium">{days}j</span>;
  return <span className="text-xs text-gray-500">{days}j</span>;
}

export default function ContractsPage() {
  const active = contracts.filter(c => c.status === 'active').length;
  const expiringSoon = contracts.filter(c => c.daysToExpiry > 0 && c.daysToExpiry <= 90).length;
  const totalValue = contracts.reduce((s, c) => s + c.amount, 0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Contrats</h1>
        <p className="text-gray-500 mt-1">Gestion et suivi des contrats fournisseurs</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <p className="text-sm text-gray-500">Total Contrats</p>
          <p className="text-2xl font-bold mt-1">{contracts.length}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Actifs</p>
          <p className="text-2xl font-bold mt-1 text-green-600">{active}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Expirent sous 90j</p>
          <p className="text-2xl font-bold mt-1 text-yellow-600">{expiringSoon}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Valeur Totale</p>
          <p className="text-2xl font-bold mt-1">{formatCurrency(totalValue)}</p>
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="pb-3 text-sm font-medium text-gray-500">Référence</th>
              <th className="pb-3 text-sm font-medium text-gray-500">Titre</th>
              <th className="pb-3 text-sm font-medium text-gray-500">Fournisseur</th>
              <th className="pb-3 text-sm font-medium text-gray-500">Type</th>
              <th className="pb-3 text-sm font-medium text-gray-500 text-right">Montant</th>
              <th className="pb-3 text-sm font-medium text-gray-500">Statut</th>
              <th className="pb-3 text-sm font-medium text-gray-500 text-right">Échéance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {contracts.map((c) => (
              <tr key={c.ref} className="hover:bg-gray-50">
                <td className="py-3 text-sm font-mono text-blue-600">{c.ref}</td>
                <td className="py-3 font-medium">{c.title}</td>
                <td className="py-3 text-gray-600">{c.counterparty}</td>
                <td className="py-3 text-gray-500 capitalize">{c.type}</td>
                <td className="py-3 text-right text-gray-600">{formatCurrency(c.amount)}</td>
                <td className="py-3">{statusBadge(c.status)}</td>
                <td className="py-3 text-right">{expiryBadge(c.daysToExpiry)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
