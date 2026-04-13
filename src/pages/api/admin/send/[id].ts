import type { APIRoute } from 'astro';
import { getDb } from '../../../../lib/db';
import { getResend } from '../../../../lib/email';

export const POST: APIRoute = async ({ params, cookies }) => {
  if (cookies.get('admin_token')?.value !== import.meta.env.ADMIN_PASSWORD) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  const { id } = params;

  try {
    const sql = getDb();
    const [broadcast] = await sql`SELECT * FROM broadcasts WHERE id = ${id!}`;

    if (!broadcast) return err('Broadcast not found.');
    if (broadcast.sent_at) return err('Already sent.');

    const subscribers = await sql`SELECT DISTINCT email FROM signups WHERE email IS NOT NULL AND email != '' ORDER BY email`;
    if (!subscribers.length) return err('No subscribers found.');

    const FROM   = import.meta.env.FROM_EMAIL  ?? 'noreply@montavillalandtrust.org';
    const resend = getResend();
    const previewUrl = `https://montavillalandtrust.org/emails/${id}`;

    const emailHtml = `<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background:#F5EED8;">
  <div style="max-width:600px;margin:0 auto;font-family:Georgia,serif;">

    <div style="background:#1D3A2A;padding:1.75rem 2.5rem;border-bottom:3px solid #C8872A;">
      <p style="margin:0;font-family:Arial,sans-serif;font-weight:700;font-size:1rem;
                letter-spacing:0.08em;color:#F5EED8;">
        MONTAVILLA <span style="color:#E8A832;">LAND TRUST</span>
      </p>
    </div>

    <div style="background:#1D3A2A;padding:2.5rem;color:#7A9E7E;font-size:1.05rem;line-height:1.7;">
      ${broadcast.html_body
        .replace(/<h1>/g, '<h1 style="font-family:Arial,sans-serif;font-weight:900;font-size:2rem;color:#F5EED8;margin:0 0 1rem;line-height:1.1;">')
        .replace(/<h2>/g, '<h2 style="font-family:Arial,sans-serif;font-weight:700;font-size:1.4rem;color:#E8A832;margin:1.5rem 0 0.6rem;">')
        .replace(/<h3>/g, '<h3 style="font-family:Arial,sans-serif;font-weight:700;font-size:1.1rem;color:#F5EED8;margin:1.2rem 0 0.4rem;">')
        .replace(/<p>/g, '<p style="margin:0 0 1rem;color:#7A9E7E;">')
        .replace(/<strong>/g, '<strong style="color:#F5EED8;">')
        .replace(/<a /g, '<a style="color:#E8A832;" ')
        .replace(/<ul>/g, '<ul style="color:#7A9E7E;padding-left:1.5rem;margin:0 0 1rem;">')
        .replace(/<ol>/g, '<ol style="color:#7A9E7E;padding-left:1.5rem;margin:0 0 1rem;">')
        .replace(/<hr>/g, '<hr style="border:none;border-top:1px solid rgba(122,158,126,0.2);margin:1.5rem 0;">')
      }
    </div>

    <div style="background:#0E1F16;padding:1.5rem 2.5rem;border-top:1px solid rgba(122,158,126,0.15);">
      <p style="font-size:0.8rem;color:rgba(122,158,126,0.5);margin:0;line-height:1.8;">
        Montavilla Community Land Trust · <a href="https://montavillalandtrust.org" style="color:#E8A832;text-decoration:none;">montavillalandtrust.org</a><br>
        <a href="mailto:info@montavillalandtrust.org" style="color:#E8A832;text-decoration:none;">info@montavillalandtrust.org</a>
        &nbsp;·&nbsp; Portland, OR 97215<br>
        <a href="${previewUrl}" style="color:rgba(122,158,126,0.4);font-size:0.75rem;">View in browser</a>
        &nbsp;·&nbsp; <span style="font-size:0.75rem;">Reply "unsubscribe" to be removed.</span>
      </p>
    </div>

  </div>
</body>
</html>`;

    const results = await Promise.allSettled(
      subscribers.map(({ email }) =>
        resend.emails.send({
          from:    `Montavilla Land Trust <${FROM}>`,
          to:      email,
          subject: broadcast.subject,
          html:    emailHtml,
        })
      )
    );

    const sent = results.filter(r => r.status === 'fulfilled').length;
    const failed = results.filter(r => r.status === 'rejected').length;

    await sql`
      UPDATE broadcasts
      SET sent_at = NOW(), sent_count = ${sent}
      WHERE id = ${id!}
    `;

    return new Response(JSON.stringify({ sent, failed }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (e) {
    console.error('Send error:', e);
    return err('Server error.');
  }
};

function err(message: string) {
  return new Response(JSON.stringify({ error: message }), {
    status: 400,
    headers: { 'Content-Type': 'application/json' },
  });
}
