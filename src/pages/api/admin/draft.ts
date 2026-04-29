import type { APIRoute } from 'astro';
import { marked } from 'marked';
import { put } from '@vercel/blob';
import { v4 as uuidv4 } from 'uuid';
import { getDb } from '../../../lib/db';

function toRawUrl(url: string): string {
  // Convert GitHub blob URL → raw URL
  return url
    .replace('github.com', 'raw.githubusercontent.com')
    .replace('/blob/', '/');
}

function parseRecipients(raw: string): string[] {
  return raw
    .split(/[\s,;]+/)
    .map(s => s.trim())
    .filter(s => s.length > 0 && s.includes('@'));
}

async function ensureSchema(sql: ReturnType<typeof getDb>) {
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
  await sql`ALTER TABLE broadcasts ADD COLUMN IF NOT EXISTS extra_recipients     TEXT[] DEFAULT '{}'`;
  await sql`ALTER TABLE broadcasts ADD COLUMN IF NOT EXISTS attachment_urls      TEXT[] DEFAULT '{}'`;
  await sql`ALTER TABLE broadcasts ADD COLUMN IF NOT EXISTS attachment_filenames TEXT[] DEFAULT '{}'`;
  await sql`ALTER TABLE broadcasts ADD COLUMN IF NOT EXISTS from_name            TEXT`;
  await sql`ALTER TABLE broadcasts ADD COLUMN IF NOT EXISTS from_email           TEXT`;
}

export const POST: APIRoute = async ({ request, cookies }) => {
  if (cookies.get('admin_token')?.value !== import.meta.env.ADMIN_PASSWORD) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  try {
    const contentType = request.headers.get('content-type') ?? '';
    let subject = '';
    let githubUrl = '';
    let extraRecipients: string[] = [];
    let fromName: string | null = null;
    let fromEmail: string | null = null;
    const attachmentUrls: string[] = [];
    const attachmentFilenames: string[] = [];

    if (contentType.includes('multipart/form-data')) {
      const form = await request.formData();
      subject = (form.get('subject') as string ?? '').trim();
      githubUrl = (form.get('githubUrl') as string ?? '').trim();
      extraRecipients = parseRecipients((form.get('extraRecipients') as string) ?? '');
      const rawFromName = ((form.get('fromName') as string) ?? '').trim();
      const rawFromEmail = ((form.get('fromEmail') as string) ?? '').trim();
      fromName = rawFromName || null;
      fromEmail = rawFromEmail || null;

      const files = form.getAll('attachments').filter((f): f is File => f instanceof File && f.size > 0);
      for (const file of files) {
        if (!process.env.BLOB_READ_WRITE_TOKEN) {
          return err('Attachments require BLOB_READ_WRITE_TOKEN to be configured.');
        }
        const id = uuidv4();
        const safeName = file.name.replace(/[^A-Za-z0-9._-]/g, '_');
        const blob = await put(`broadcasts/${id}/${safeName}`, file, {
          access: 'public',
          contentType: file.type || 'application/octet-stream',
        });
        attachmentUrls.push(blob.url);
        attachmentFilenames.push(file.name);
      }
    } else {
      const body = await request.json();
      subject = (body.subject ?? '').trim();
      githubUrl = (body.githubUrl ?? '').trim();
      extraRecipients = parseRecipients(body.extraRecipients ?? '');
      fromName = (body.fromName ?? '').trim() || null;
      fromEmail = (body.fromEmail ?? '').trim() || null;
    }

    if (!subject) return err('Subject is required.');
    if (!githubUrl) return err('GitHub URL is required.');

    const rawUrl = toRawUrl(githubUrl);
    const mdRes = await fetch(rawUrl);
    if (!mdRes.ok) return err(`Could not fetch markdown: ${mdRes.status} from ${rawUrl}`);

    const raw = await mdRes.text();
    // Strip document header — keep only what follows "## Email Body"
    const bodyMarker = raw.indexOf('\n## Email Body');
    const markdown = bodyMarker !== -1 ? raw.slice(bodyMarker + '\n## Email Body'.length).trimStart() : raw;
    const htmlBody = await marked.parse(markdown);

    const sql = getDb();
    await ensureSchema(sql);

    const [row] = await sql`
      INSERT INTO broadcasts (
        subject, github_url, html_body,
        extra_recipients, attachment_urls, attachment_filenames,
        from_name, from_email
      )
      VALUES (
        ${subject}, ${githubUrl}, ${htmlBody},
        ${extraRecipients}, ${attachmentUrls}, ${attachmentFilenames},
        ${fromName}, ${fromEmail}
      )
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
