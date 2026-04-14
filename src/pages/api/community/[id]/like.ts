import type { APIRoute } from 'astro';
import { getDb } from '../../../../lib/db';

export const POST: APIRoute = async ({ params }) => {
  const { id } = params;

  if (!id) {
    return new Response(JSON.stringify({ error: 'Missing post id' }), { status: 400 });
  }

  try {
    const sql = getDb();
    const rows = await sql`
      UPDATE posts
      SET likes = likes + 1
      WHERE id = ${id} AND is_deleted = FALSE
      RETURNING likes
    `;

    if (rows.length === 0) {
      return new Response(JSON.stringify({ error: 'Post not found' }), { status: 404 });
    }

    return new Response(JSON.stringify({ likes: rows[0].likes }), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('like error:', err);
    return new Response(JSON.stringify({ error: 'Server error' }), { status: 500 });
  }
};
