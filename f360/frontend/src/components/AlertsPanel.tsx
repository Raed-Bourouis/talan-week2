'use client';

const alerts = [
  {
    id: 1,
    severity: 'critical',
    category: 'Budget',
    title: 'Dépassement budget OPEX (+8.2%)',
    description:
      'Le budget OPEX dépasse de €70,000 le montant prévu. Principalement dû aux coûts énergétiques.',
    action: 'Renégocier le contrat fournisseur énergie. Réduire les dépenses non-essentielles.',
    date: '2026-02-15',
  },
  {
    id: 2,
    severity: 'warning',
    category: 'Contrat',
    title: 'Contrat CTR-2024-089 expire dans 28 jours',
    description:
      'Contrat de maintenance IT avec TechServ SAS. Montant annuel: €120,000.',
    action: 'Initier la procédure de renouvellement. Comparer avec 2 fournisseurs alternatifs.',
    date: '2026-02-14',
  },
  {
    id: 3,
    severity: 'warning',
    category: 'Trésorerie',
    title: 'Risque de trésorerie J+45',
    description:
      'La projection cashflow indique un solde < €50,000 autour du 2 avril.',
    action: 'Accélérer le recouvrement des factures impayées. Reporter les investissements CAPEX non-urgents.',
    date: '2026-02-14',
  },
  {
    id: 4,
    severity: 'info',
    category: 'Budget',
    title: 'Sous-exécution Marketing (-11%)',
    description:
      'Le budget Marketing est sous-utilisé de €20,000. Possibilité de réallocation.',
    action: 'Réallouer vers OPEX ou provisionner pour Q3.',
    date: '2026-02-13',
  },
];

const severityStyles: Record<string, string> = {
  critical: 'border-l-red-500 bg-red-50',
  warning: 'border-l-yellow-500 bg-yellow-50',
  info: 'border-l-blue-500 bg-blue-50',
};

const severityBadge: Record<string, string> = {
  critical: 'badge-danger',
  warning: 'badge-warning',
  info: 'badge-info',
};

export default function AlertsPanel() {
  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={`border-l-4 rounded-r-lg p-4 ${severityStyles[alert.severity]}`}
        >
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <span className={severityBadge[alert.severity]}>
                {alert.severity.toUpperCase()}
              </span>
              <span className="text-xs text-gray-500">{alert.category}</span>
            </div>
            <span className="text-xs text-gray-400">{alert.date}</span>
          </div>
          <h3 className="font-semibold text-sm text-gray-900">{alert.title}</h3>
          <p className="text-xs text-gray-600 mt-1">{alert.description}</p>
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs font-medium text-blue-600">
              💡 {alert.action}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
