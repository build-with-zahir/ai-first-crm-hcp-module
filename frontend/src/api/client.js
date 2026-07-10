const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export const api = {
  seedDemoData: () => request("/seed", { method: "POST" }),
  getHcps: () => request("/hcps"),
  getInteractions: (hcpId) => request(`/interactions?hcp_id=${hcpId}`),
  createInteraction: (payload) =>
    request("/interactions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateInteraction: (interactionId, payload) =>
    request(`/interactions/${interactionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  chatAgent: (payload) =>
    request("/agent/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
