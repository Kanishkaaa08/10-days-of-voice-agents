const API_BASE = process.env.ESCALATIONS_API_URL ?? 'http://127.0.0.1:5001';

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const body = await request.json();
    const response = await fetch(`${API_BASE}/api/escalations/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch {
    return Response.json({ error: 'Escalation service unavailable' }, { status: 503 });
  }
}
