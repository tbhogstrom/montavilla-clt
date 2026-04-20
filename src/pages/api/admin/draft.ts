import type { APIRoute } from 'astro';
import { marked } from 'marked';
import { getDb } from '../../../lib/db';

function toRawUrl(url: string): string {
  // Convert GitHub blob URL → raw URL
  return url
    .replace('github.com', 'raw.githubusercontent.com')
    .replace('/blob/', '/');
}

export const POST: APIRoute = async ({ request, cookies }) => {
  if (cookies.get('admin_token')?.value !== import.meta.env.ADMIN_PASSWORD) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  try {
    const { subject, githubUrl } = await request.json();

    if (!subject?.trim()) return err('Subject is required.');
    if (!githubUrl?.trim()) return err('GitHub URL is required.');

    const rawUrl = toRawUrl(githubUrl.trim());
    const mdRes = await fetch(rawUrl);
    if (!mdRes.ok) return err(`Could not fetch markdown: ${mdRes.status} from ${rawUrl}`);

    const raw = await mdRes.text();
    // Strip document header — keep only what follows "## Email Body"
    const bodyMarker = raw.indexOf('\n## Email Body');
    const markdown = bodyMarker !== -1 ? raw.slice(bodyMarker + '\n## Email Body'.length).trimStart() : raw;
    const htmlBody = await marked.parse(markdown);

    const sql = getDb();
    await sql`
      CREATE TABLE IF NOT EXISTS broadcasts (
        id         SERIAL PRIMARY KEY,
        subject    TEXT NOT NULL,
        github_url TEXT,
        html_body  TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        sent_at    TIMESTAMPTZ,
        sent_count INTEGER
      )
    `;

    const [row] = await sql`
      INSERT INTO broadcasts (subject, github_url, html_body)
      VALUES (${subject.trim()}, ${githubUrl.trim()}, ${htmlBody})
      RETURNING id
    `;

    return new Response(JSON.stringify({ id: row.id }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (e) {
    console.error('Draft error:', e);
    return err('Server error.');
  }
};

export const PUT: APIRoute = async ({ request, cookies }) => {
  if (cookies.get('admin_token')?.value !== import.meta.env.ADMIN_PASSWORD) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  try {
    const { id, subject, githubUrl } = await request.json();

    const rawUrl = toRawUrl(githubUrl.trim());
    const mdRes = await fetch(rawUrl);
    if (!mdRes.ok) return err(`Could not fetch markdown: ${mdRes.status}`);

    const raw = await mdRes.text();
    const bodyMarker = raw.indexOf('\n## Email Body');
    const markdown = bodyMarker !== -1 ? raw.slice(bodyMarker + '\n## Email Body'.length).trimStart() : raw;
    const htmlBody = await marked.parse(markdown);

    const sql = getDb();
    await sql`
      UPDATE broadcasts
      SET subject = ${subject.trim()}, github_url = ${githubUrl.trim()}, html_body = ${htmlBody}
      WHERE id = ${id} AND sent_at IS NULL
    `;

    return new Response(JSON.stringify({ id }), { status: 200 });
  } catch (e) {
    console.error('Update error:', e);
    return err('Server error.');
  }
};

function err(message: string) {
  return new Response(JSON.stringify({ error: message }), {
    status: 400,
    headers: { 'Content-Type': 'application/json' },
  });
}
