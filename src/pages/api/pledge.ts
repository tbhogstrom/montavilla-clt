import type { APIRoute } from 'astro';
import { getDb } from '../../lib/db';

export const POST: APIRoute = async ({ request }) => {
  try {
    const { name, amount } = await request.json();

    if (!name?.trim())
      return err('Please enter your name.');

    const amt = Math.round(Number(amount));
    if (!amt || amt < 1)
      return err('Pledge must be at least $1.');
    if (amt > 999_999)
      return err('Amount too large.');

    const sql = getDb();

    await sql`
      CREATE TABLE IF NOT EXISTS pledges (
        id         SERIAL PRIMARY KEY,
        name       TEXT    NOT NULL,
        amount     INTEGER NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
      )
    `;

    await sql`INSERT INTO pledges (name, amount) VALUES (${name.trim()}, ${amt})`;

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (e) {
    console.error('Pledge error:', e);
    return err('Server error — please try again.');
  }
};

function err(message: string, status = 400) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
