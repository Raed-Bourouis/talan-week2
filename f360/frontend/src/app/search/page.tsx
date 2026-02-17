'use client';

import { useState } from 'react';

interface SearchResult {
  content: string;
  source?: string;
  score?: number;
  metadata?: Record<string, unknown>;
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const res = await fetch('http://localhost:8000/api/v1/ragraph/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query, top_k: 5 }),
      });
      const data = await res.json();

      if (data.results) {
        setResults(data.results);
      } else if (data.answer) {
        setResults([{ content: data.answer, source: 'AI Answer' }]);
      } else {
        setResults([{ content: JSON.stringify(data, null, 2), source: 'Raw Response' }]);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erreur de connexion';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    'Quel est le taux d\'exécution budgétaire du Q1 ?',
    'Quelles clauses contractuelles présentent un risque ?',
    'Résumé de la trésorerie nette sur 30 jours',
    'Quels fournisseurs ont les contrats les plus élevés ?',
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Recherche IA</h1>
        <p className="text-gray-500 mt-1">Posez une question sur vos données financières (RAG + Graph)</p>
      </div>

      {/* Search bar */}
      <div className="card">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Ex: Quel est le budget restant pour le département IT ?"
            className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
          />
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm whitespace-nowrap"
          >
            {loading ? '⏳ Recherche...' : '🔍 Rechercher'}
          </button>
        </div>

        {/* Suggestions */}
        <div className="mt-4 flex flex-wrap gap-2">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => { setQuery(s); }}
              className="text-xs bg-gray-100 text-gray-600 px-3 py-1.5 rounded-full hover:bg-blue-50 hover:text-blue-600 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
          ⚠️ {error}
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Résultats ({results.length})</h2>
          {results.map((r, i) => (
            <div key={i} className="card border-l-4 border-blue-500">
              {r.source && (
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                    {r.source}
                  </span>
                  {r.score !== undefined && (
                    <span className="text-xs text-gray-400">
                      Pertinence: {(r.score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              )}
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{r.content}</p>
            </div>
          ))}
        </div>
      )}

      {!loading && results.length === 0 && !error && (
        <div className="text-center py-16 text-gray-400">
          <span className="text-5xl">🤖</span>
          <p className="mt-4 text-lg">Posez une question pour interroger vos données</p>
          <p className="text-sm mt-1">Le système utilise RAG et Graph Knowledge pour des réponses contextuelles</p>
        </div>
      )}
    </div>
  );
}
