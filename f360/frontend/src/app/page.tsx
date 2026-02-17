'use client';

import { useState, useEffect } from 'react';
import KPICard from '@/components/KPICard';
import BudgetChart from '@/components/BudgetChart';
import AlertsPanel from '@/components/AlertsPanel';
import CashflowChart from '@/components/CashflowChart';

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Financial Command Center
        </h1>
        <p className="text-gray-500 mt-1">
          Vue d&apos;ensemble en temps réel de votre santé financière
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Budget Total"
          value="€2,450,000"
          change={-3.2}
          trend="down"
          subtitle="FY 2026"
        />
        <KPICard
          title="Contrats Actifs"
          value="47"
          change={5}
          trend="up"
          subtitle="3 expirent sous 30j"
        />
        <KPICard
          title="Trésorerie J+90"
          value="€1,230,000"
          change={12.5}
          trend="up"
          subtitle="Projection optimiste"
        />
        <KPICard
          title="Alertes"
          value="8"
          change={-2}
          trend="down"
          subtitle="3 critiques"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Exécution Budgétaire</h2>
          <BudgetChart />
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">
            Projection Trésorerie (J+90)
          </h2>
          <CashflowChart />
        </div>
      </div>

      {/* Alerts & Recommendations */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">
          Alertes & Recommandations
        </h2>
        <AlertsPanel />
      </div>
    </div>
  );
}
