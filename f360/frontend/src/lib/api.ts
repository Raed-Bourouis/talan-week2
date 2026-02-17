const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface FetchOptions extends RequestInit {
  token?: string;
}

async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ── Auth ──
export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, full_name?: string) =>
    apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    }),
  me: (token: string) => apiFetch('/auth/me', { token }),
};

// ── Budget ──
export const budgetApi = {
  overview: (companyId: string, year: number, token: string) =>
    apiFetch(`/budget/overview?company_id=${companyId}&fiscal_year=${year}`, { token }),
};

// ── Contracts ──
export const contractsApi = {
  list: (companyId: string, token: string) =>
    apiFetch(`/contracts/?company_id=${companyId}`, { token }),
  alerts: (companyId: string, token: string) =>
    apiFetch(`/contracts/alerts?company_id=${companyId}`, { token }),
};

// ── Cashflow ──
export const cashflowApi = {
  forecast: (companyId: string, days: number, token: string) =>
    apiFetch(`/cashflow/forecast?company_id=${companyId}&days=${days}`, { token }),
};

// ── Simulation ──
export const simulationApi = {
  run: (type: string, parameters: Record<string, unknown>, token: string) =>
    apiFetch('/simulate/', {
      method: 'POST',
      body: JSON.stringify({ simulation_type: type, parameters }),
      token,
    }),
};

// ── Recommendations ──
export const recommendationsApi = {
  list: (companyId: string, token: string) =>
    apiFetch(`/recommendations/?company_id=${companyId}`, { token }),
  generate: (companyId: string, token: string) =>
    apiFetch(`/recommendations/generate?company_id=${companyId}`, {
      method: 'POST',
      token,
    }),
};

// ── RAG ──
export const ragApi = {
  query: (question: string, token: string, companyId?: string) =>
    apiFetch('/ragraph/query', {
      method: 'POST',
      body: JSON.stringify({ question, company_id: companyId, top_k: 5 }),
      token,
    }),
};
