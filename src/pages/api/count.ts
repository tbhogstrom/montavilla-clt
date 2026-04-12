import type { APIRoute } from 'astro';
import { getDb } from '../../lib/db';

export const GET: APIRoute = async () => {
  try {
    const sql = getDb();
    const [signups, pledges] = await Promise.all([
      sql`SELECT COUNT(*)::int AS count FROM signups`,
      sql`SELECT COALESCE(SUM(amount), 0)::int AS total FROM pledges`.catch(() => [{ total: 0 }]),
    ]);
    return new Response(JSON.stringify({
      count:        signups[0]?.count ?? 0,
      pledgeTotal:  pledges[0]?.total ?? 0,
    }), {
      headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    });
  } catch {
    return new Response(JSON.stringify({ count: 0, pledgeTotal: 0 }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
