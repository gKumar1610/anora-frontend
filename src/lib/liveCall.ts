export interface LiveCallCredentials {
  server_url: string;
  participant_token: string;
}

const API_BASE = (import.meta.env.VITE_LIVE_CALL_API ?? 'http://localhost:8000').replace(/\/$/, '');

export async function requestLiveCallToken(): Promise<LiveCallCredentials> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ participant_name: 'Landing page visitor' }),
    });
  } catch {
    throw new Error("Can't reach the Nami Voice agent right now. Try again in a moment.");
  }

  if (!response.ok) {
    const detail = await response.text();
    let message = detail || response.statusText;
    try {
      const parsed = JSON.parse(detail);
      message = parsed.detail || message;
    } catch {
      // Non-JSON error body — keep the raw text.
    }
    throw new Error(message);
  }

  return response.json() as Promise<LiveCallCredentials>;
}
