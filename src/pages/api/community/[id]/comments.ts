import type { APIRoute } from 'astro';
import { put } from '@vercel/blob';
import { v4 as uuidv4 } from 'uuid';
import sharp from 'sharp';
import { getDb } from '../../../../lib/db';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/heic', 'image/heif', 'image/webp'];
const ALLOWED_EXT   = ['jpg', 'jpeg', 'png', 'heic', 'heif', 'webp'];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

async function ensureTable() {
  const sql = getDb();
  await sql`
    CREATE TABLE IF NOT EXISTS comments (
      id           TEXT PRIMARY KEY,
      post_id      TEXT NOT NULL REFERENCES posts(id),
      display_name TEXT NOT NULL,
      body         TEXT NOT NULL,
      image_url    TEXT,
      created_at   TIMESTAMPTZ DEFAULT NOW(),
      is_deleted   BOOLEAN DEFAULT FALSE
    )
  `;
  await sql`CREATE INDEX IF NOT EXISTS comments_post_id_idx ON comments (post_id, created_at)`;
  await sql`ALTER TABLE comments ADD COLUMN IF NOT EXISTS image_url TEXT`;
}

export const GET: APIRoute = async ({ params }) => {
  const { id } = params;
  if (!id) return new Response(JSON.stringify({ error: 'Missing post id' }), { status: 400 });

  try {
    await ensureTable();
    const sql = getDb();
    const rows = await sql`
      SELECT id, display_name, body, image_url, created_at
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

    const formData = await request.formData();

    // Honeypot
    if (formData.get('website')) {
      return new Response(JSON.stringify({ error: 'Invalid submission' }), { status: 400 });
    }

    const displayName = (formData.get('displayName') as string)?.trim();
    if (!displayName) {
      return new Response(JSON.stringify({ error: 'Name is required' }), { status: 400 });
    }

    const text = (formData.get('body') as string)?.trim();
    if (!text) {
      return new Response(JSON.stringify({ error: 'Comment cannot be empty' }), { status: 400 });
    }
    if (text.length > 2000) {
      return new Response(JSON.stringify({ error: 'Comment too long (max 2000 characters)' }), { status: 400 });
    }

    const sql = getDb();
    const [post] = await sql`SELECT id FROM posts WHERE id = ${id} AND is_deleted = FALSE`;
    if (!post) {
      return new Response(JSON.stringify({ error: 'Post not found' }), { status: 404 });
    }

    // ── Image upload ────────────────────────────────────────────────────────
    const imageFile = formData.get('image') as File | null;
    const hasImage  = imageFile && imageFile.size > 0;
    let imageUrl: string | null = null;

    if (hasImage) {
      const ext = imageFile.name.split('.').pop()?.toLowerCase() ?? '';
      if (!ALLOWED_TYPES.includes(imageFile.type) && !ALLOWED_EXT.includes(ext)) {
        return new Response(
          JSON.stringify({ error: 'Invalid file type. Upload a JPEG, PNG, WebP, or HEIC.' }),
          { status: 400 }
        );
      }
      if (imageFile.size > MAX_FILE_SIZE) {
        return new Response(JSON.stringify({ error: 'Image too large. Max 10 MB.' }), { status: 400 });
      }

      const inputBuffer = Buffer.from(await imageFile.arrayBuffer());
      const webpBuffer  = await sharp(inputBuffer).webp().toBuffer();

      const commentId = uuidv4();

      if (process.env.BLOB_READ_WRITE_TOKEN) {
        const blob = await put(`community/comments/${commentId}.webp`, webpBuffer, {
          access:      'public',
          contentType: 'image/webp',
        });
        imageUrl = blob.url;
      } else {
        imageUrl = `data:image/webp;base64,${webpBuffer.toString('base64')}`;
      }

      await sql`
        INSERT INTO comments (id, post_id, display_name, body, image_url)
        VALUES (${commentId}, ${id}, ${displayName}, ${text}, ${imageUrl})
      `;

      const [comment] = await sql`SELECT * FROM comments WHERE id = ${commentId}`;
      return new Response(JSON.stringify(comment), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // ── Text-only comment ───────────────────────────────────────────────────
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
