const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON, keep default detail
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  me: () => request("/auth/me"),
  logout: () => request("/auth/logout", { method: "POST" }),
  githubLoginUrl: () => `${API_URL}/auth/github/login`,

  availableRepos: () => request("/api/repos/available"),
  connectedRepos: () => request("/api/repos"),
  connectRepo: (full_name) => request("/api/repos", { method: "POST", body: JSON.stringify({ full_name }) }),
  disconnectRepo: (id) => request(`/api/repos/${id}`, { method: "DELETE" }),

  listRules: () => request("/api/rules"),
  createRule: (rule) => request("/api/rules", { method: "POST", body: JSON.stringify(rule) }),
  updateRule: (id, rule) => request(`/api/rules/${id}`, { method: "PUT", body: JSON.stringify(rule) }),
  deleteRule: (id) => request(`/api/rules/${id}`, { method: "DELETE" }),

  listEvents: () => request("/api/events"),
  retryEvent: (id) => request(`/api/events/${id}/retry`, { method: "POST" }),
};

export { ApiError, API_URL };
