import { API_CONFIG } from '../config/api';

export async function apiFetch(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_CONFIG.BASE_URL}/${url}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let message = `API error: ${res.status}`;
    try {
      const err = await res.json();
      if (err.detail) message = err.detail;
    } catch {
      // fallback if not JSON
    }
    throw new Error(message);
  }
  return res.json();
}
