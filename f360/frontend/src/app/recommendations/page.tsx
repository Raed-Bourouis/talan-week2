'use client';

const recommendations = [
  {
    severity: 'critical',
    title: 'Dépassement CAPEX +55%',
    description: 'Le budget CAPEX dépasse la prévision de 55%. Risque de déséquilibre financier sur FY2025.',
    action: 'Geler les nouveaux investissements et revoir la roadmap CAPEX avec la direction.',
    category: 'budget',
    date: '2026-02-17',
  },
  {
    severity: 'warning',
    title: 'Contrat Capgemini expire dans 30 jours',
    description: 'Le contrat de maintenance IT avec Capgemini (500k€/an) expire le 01/03/2026.',
    action: 'Initier la renégociation ou lancer un appel d\'offres pour continuité de service.',
    category: 'contract',
    date: '2026-02-15',
  },
  {
    severity: 'warning',
    title: 'Trésorerie sous seuil critique dans 45 jours',
    description: 'La projection Monte Carlo indique une probabilité de 35% que la trésorerie passe sous 200k€.',
    action: 'Accélérer le recouvrement des factures clients et différer les paiements non urgents.',
    category: 'cashflow',
    date: '2026-02-16',
  },
  {
    severity: 'critical',
    title: 'Sous-exécution IT -40%',
    description: 'Le budget IT n\'est exécuté qu\'à 60%. Risque de report massif et perte de budget.',
    action: 'Examiner les projets IT en attente et accélérer l\'engagement des dépenses planifiées.',
    category: 'budget',
    date: '2026-02-14',
  },
  {
    severity: 'info',
    title: 'Économie HR identifiée',
    description: 'Le budget HR est sous-exécuté de 6.7%, offrant une marge de manœuvre.',
    action: 'Réallouer l\'excédent HR vers les postes CAPEX ou IT déficitaires.',
    category: 'budget',
    date: '2026-02-13',
  },
  {
    severity: 'warning',
    title: 'Signal faible ESG : Budget Vert défavorable',
    description: 'Plusieurs missions du PLF présentent une cotation environnementale défavorable.',
    action: 'Intégrer les critères ESG dans la prochaine revue budgétaire trimestrielle.',
    category: 'risk',
    date: '2026-02-12',
  },
];

function severityIcon(s: string) {
  if (s === 'critical') return '🔴';
  if (s === 'warning') return '🟡';
  return '🔵';
}

function severityBadge(s: string) {
  if (s === 'critical') return <span className="badge-danger">Critique</span>;
  if (s === 'warning') return <span className="badge-warning">Warning</span>;
  return <span className="badge-success">Info</span>;
}

function categoryBadge(c: string) {
  const colors: Record<string, string> = {
    budget: 'bg-blue-100 text-blue-800',
    contract: 'bg-purple-100 text-purple-800',
    cashflow: 'bg-green-100 text-green-800',
    risk: 'bg-orange-100 text-orange-800',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[c] || 'bg-gray-100 text-gray-800'}`}>
      {c}
    </span>
  );
}

export default function RecommendationsPage() {
  const critical = recommendations.filter(r => r.severity === 'critical').length;
  const warnings = recommendations.filter(r => r.severity === 'warning').length;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Recommandations</h1>
        <p className="text-gray-500 mt-1">Recommandations IA générées par l&apos;analyse des 7 couches</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <p className="text-sm text-gray-500">Total</p>
          <p className="text-2xl font-bold mt-1">{recommendations.length}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Critiques</p>
          <p className="text-2xl font-bold mt-1 text-red-600">{critical}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Warnings</p>
          <p className="text-2xl font-bold mt-1 text-yellow-600">{warnings}</p>
        </div>
      </div>

      <div className="space-y-4">
        {recommendations.map((r, i) => (
          <div key={i} className="card hover:shadow-md transition-shadow">
            <div className="flex items-start gap-4">
              <span className="text-2xl mt-1">{severityIcon(r.severity)}</span>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="font-semibold text-gray-900">{r.title}</h3>
                  {severityBadge(r.severity)}
                  {categoryBadge(r.category)}
                </div>
                <p className="text-sm text-gray-600 mt-1">{r.description}</p>
                <div className="mt-3 bg-blue-50 border border-blue-100 rounded-lg p-3">
                  <p className="text-sm font-medium text-blue-800">💡 Action suggérée</p>
                  <p className="text-sm text-blue-700 mt-1">{r.action}</p>
                </div>
                <p className="text-xs text-gray-400 mt-2">{r.date}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
