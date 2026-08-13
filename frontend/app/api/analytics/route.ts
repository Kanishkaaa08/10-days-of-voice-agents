const API_BASE = process.env.ESCALATIONS_API_URL ?? 'http://127.0.0.1:5001';

export async function GET() {
  console.log('[FRONTEND API] GET /api/analytics called, proxying to:', `${API_BASE}/api/analytics`);
  try {
    const response = await fetch(`${API_BASE}/api/analytics`, {
      cache: 'no-store',
    });
    console.log('[FRONTEND API] Backend response status:', response.status);
    const data = await response.json();
    console.log('[FRONTEND API] Backend response data:', data);
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error('[FRONTEND API] Error fetching analytics:', error);
    return Response.json({ error: 'Analytics service unavailable' }, { status: 503 });
  }
}
