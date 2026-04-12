import type { APIRoute } from 'astro';
import { getDb } from '../../lib/db';

export const GET: APIRoute = async () => {
  try {
    const sql = getDb();
    const result = await sql`SELECT COUNT(*)::int AS count FROM signups`;
    return new Response(JSON.stringify({ count: result[0]?.count ?? 0 }), {
      headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    });
  } catch {
    // Table may not exist yet
    return new Response(JSON.stringify({ count: 0 }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
