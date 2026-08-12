const API_BASE = process.env.ESCALATIONS_API_URL ?? 'http://127.0.0.1:5001';

export async function GET(request: Request) {
  const url = new URL(request.url);
  const status = url.searchParams.get('status');
  const query = status ? `?status=${encodeURIComponent(status)}` : '';

  try {
    const response = await fetch(`${API_BASE}/api/escalations${query}`, {
      cache: 'no-store',
    });
    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch {
    return Response.json({ error: 'Escalation service unavailable' }, { status: 503 });
  }
}
