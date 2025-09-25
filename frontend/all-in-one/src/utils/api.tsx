// whenever you want to hit a protected endpoint that requires the JWT.
export async function apiFetch(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem("access_token");

  const headers = {
    ...options.headers,
    Authorization: token ? `Bearer ${token}` : "",
  };

  const res = await fetch(`http://localhost:8000${url}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}
