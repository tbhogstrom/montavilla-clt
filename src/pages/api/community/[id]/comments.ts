import type { APIRoute } from 'astro';
import { v4 as uuidv4 } from 'uuid';
import { getDb } from '../../../../lib/db';

async function ensureTable() {
  const sql = getDb();
  await sql`
    CREATE TABLE IF NOT EXISTS comments (
      id           TEXT PRIMARY KEY,
      post_id      TEXT NOT NULL REFERENCES posts(id),
      display_name TEXT NOT NULL,
      body         TEXT NOT NULL,
      created_at   TIMESTAMPTZ DEFAULT NOW(),
      is_deleted   BOOLEAN DEFAULT FALSE
    )
  `;
  await sql`CREATE INDEX IF NOT EXISTS comments_post_id_idx ON comments (post_id, created_at)`;
}

export const GET: APIRoute = async ({ params }) => {
  const { id } = params;
  if (!id) return new Response(JSON.stringify({ error: 'Missing post id' }), { status: 400 });

  try {
    await ensureTable();
    const sql = getDb();
    const rows = await sql`
      SELECT id, display_name, body, created_at
      FROM comments
      WHERE post_id = ${id} AND is_deleted = FALSE
      ORDER BY created_at ASC
    `;
    return new Response(JSON.stringify(rows), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('comments GET error:', err);
    return new Response(JSON.stringify({ error: 'Server error' }), { status: 500 });
  }
};

export const POST: APIRoute = async ({ params, request }) => {
  const { id } = params;
  if (!id) return new Response(JSON.stringify({ error: 'Missing post id' }), { status: 400 });

  try {
    await ensureTable();

    const body = await request.json();

    // Honeypot
    if (body.website) {
      return new Response(JSON.stringify({ error: 'Invalid submission' }), { status: 400 });
    }

    const displayName = (body.displayName as string)?.trim();
    if (!displayName) {
      return new Response(JSON.stringify({ error: 'Name is required' }), { status: 400 });
    }

    const text = (body.body as string)?.trim();
    if (!text) {
      return new Response(JSON.stringify({ error: 'Comment cannot be empty' }), { status: 400 });
    }
    if (text.length > 2000) {
      return new Response(JSON.stringify({ error: 'Comment too long (max 2000 characters)' }), { status: 400 });
    }

    const sql = getDb();

    // Verify post exists
    const [post] = await sql`SELECT id FROM posts WHERE id = ${id} AND is_deleted = FALSE`;
    if (!post) {
      return new Response(JSON.stringify({ error: 'Post not found' }), { status: 404 });
    }

    const commentId = uuidv4();
    await sql`
      INSERT INTO comments (id, post_id, display_name, body)
      VALUES (${commentId}, ${id}, ${displayName}, ${text})
    `;

    const [comment] = await sql`SELECT * FROM comments WHERE id = ${commentId}`;
    return new Response(JSON.stringify(comment), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('comments POST error:', err);
    return new Response(JSON.stringify({ error: 'Server error' }), { status: 500 });
  }
};
