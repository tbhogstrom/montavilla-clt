import type { APIRoute } from 'astro';
import { put } from '@vercel/blob';
import { v4 as uuidv4 } from 'uuid';
import { getDb } from '../../../lib/db';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/heic', 'image/heif', 'image/webp'];
const ALLOWED_EXT   = ['jpg', 'jpeg', 'png', 'heic', 'heif', 'webp'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const POST_TYPES    = ['discussion', 'update'] as const;

async function ensureTable() {
  const sql = getDb();
  await sql`
    CREATE TABLE IF NOT EXISTS posts (
      id           TEXT PRIMARY KEY,
      type         TEXT NOT NULL DEFAULT 'discussion',
      title        TEXT NOT NULL,
      body         TEXT,
      image_url    TEXT,
      display_name TEXT NOT NULL,
      neighborhood TEXT,
      likes        INTEGER NOT NULL DEFAULT 0,
      created_at   TIMESTAMPTZ DEFAULT NOW(),
      is_deleted   BOOLEAN DEFAULT FALSE
    )
  `;
  // Migration: add likes column if table already existed without it
  await sql`
    ALTER TABLE posts ADD COLUMN IF NOT EXISTS likes INTEGER NOT NULL DEFAULT 0
  `;
}

export const GET: APIRoute = async () => {
  try {
    await ensureTable();
    const sql = getDb();
    const rows = await sql`
      SELECT id, type, title, body, image_url, display_name, neighborhood, likes, created_at
      FROM posts
      WHERE is_deleted = FALSE
      ORDER BY likes DESC, created_at DESC
      LIMIT 100
    `;
    return new Response(JSON.stringify(rows), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('community GET error:', err);
    return new Response(JSON.stringify({ error: 'Server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};

export const POST: APIRoute = async ({ request }) => {
  try {
    await ensureTable();

    const formData = await request.formData();

    // Honeypot
    if (formData.get('website')) {
      return new Response(JSON.stringify({ error: 'Invalid submission' }), { status: 400 });
    }

    const type = (formData.get('type') as string)?.trim();
    if (!POST_TYPES.includes(type as typeof POST_TYPES[number])) {
      return new Response(JSON.stringify({ error: 'Invalid post type' }), { status: 400 });
    }

    const title = (formData.get('title') as string)?.trim();
    if (!title) {
      return new Response(JSON.stringify({ error: 'Title is required' }), { status: 400 });
    }

    const displayName = (formData.get('displayName') as string)?.trim();
    if (!displayName) {
      return new Response(JSON.stringify({ error: 'Name is required' }), { status: 400 });
    }

    const body         = (formData.get('body') as string)?.trim() || null;
    const neighborhood = (formData.get('neighborhood') as string)?.trim() || null;
    const imageFile    = formData.get('image') as File | null;
    const hasImage     = imageFile && imageFile.size > 0;

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
        return new Response(
          JSON.stringify({ error: 'Image too large. Max 10 MB.' }),
          { status: 400 }
        );
      }

      if (process.env.BLOB_READ_WRITE_TOKEN) {
        const id   = uuidv4();
        const blob = await put(`community/${id}/image.${ext}`, imageFile, {
          access: 'public',
          contentType: imageFile.type,
        });
        imageUrl = blob.url;
      } else {
        const buf = Buffer.from(await imageFile.arrayBuffer());
        imageUrl  = `data:${imageFile.type};base64,${buf.toString('base64')}`;
      }
    }

    const id  = uuidv4();
    const sql = getDb();

    await sql`
      INSERT INTO posts (id, type, title, body, image_url, display_name, neighborhood)
      VALUES (${id}, ${type}, ${title}, ${body}, ${imageUrl}, ${displayName}, ${neighborhood})
    `;

    const [post] = await sql`SELECT * FROM posts WHERE id = ${id}`;

    return new Response(JSON.stringify(post), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('community POST error:', err);
    return new Response(JSON.stringify({ error: 'Server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
