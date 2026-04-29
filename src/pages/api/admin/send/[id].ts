import type { APIRoute } from 'astro';
import { getDb } from '../../../../lib/db';
import { getResend } from '../../../../lib/email';

const BATCH_SIZE = 10;

function chunk<T>(arr: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

export const POST: APIRoute = async ({ params, cookies, request }) => {
  if (cookies.get('admin_token')?.value !== import.meta.env.ADMIN_PASSWORD) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  const { id } = params;
  const url = new URL(request.url);
  const force = url.searchParams.get('force') === 'true';
  const testEmail = url.searchParams.get('test')?.trim() || '';
  const isTest = testEmail.includes('@');

  try {
    const sql = getDb();
    const [broadcast] = await sql`SELECT * FROM broadcasts WHERE id = ${id!}`;

    if (!broadcast) return err('Broadcast not found.');
    if (broadcast.sent_at && !force && !isTest) return err('Already sent. Add ?force=true to resend.');

    const FROM       = import.meta.env.FROM_EMAIL ?? 'noreply@montavillalandtrust.org';
    const resend     = getResend();
    const previewUrl = `https://montavillalandtrust.org/emails/${id}`;

    // Public-comment broadcasts default to a hardcoded extra recipient + Tyler's
    // From header. Newer broadcasts can also override these explicitly via the
    // extra_recipients / from_name / from_email columns set at draft time.
    const isPublicComment = (broadcast.subject as string).startsWith('Public Comment');
    const extraRecipients: string[] = broadcast.extra_recipients ?? [];

    let recipients: string[];
    if (isTest) {
      recipients = [testEmail];
    } else {
      const petitionEmails = await sql`SELECT DISTINCT email FROM signups WHERE email IS NOT NULL AND email != ''`;
      const allEmails = petitionEmails.map((r: { email: string }) => r.email);
      recipients = Array.from(new Set([
        ...allEmails,
        ...(isPublicComment ? ['CleanEnergyFund@portlandoregon.gov'] : []),
        ...extraRecipients,
      ]));
    }

    if (!recipients.length) return err('No recipients found.');

    const fromName  = (broadcast.from_name  as string | null) ?? null;
    const fromEmail = (broadcast.from_email as string | null) ?? null;
    const fromHeader = (fromName && fromEmail)
      ? `${fromName} <${fromEmail}>`
      : isPublicComment
        ? 'Tyler Falcon <info@montavillalandtrust.org>'
        : `Montavilla Land Trust <${FROM}>`;

    const attachmentUrls:      string[] = broadcast.attachment_urls      ?? [];
    const attachmentFilenames: string[] = broadcast.attachment_filenames ?? [];
    console.log(`[send ${id}] attachment_urls count=${attachmentUrls.length}`, attachmentUrls);

    // Fetch attachments ourselves and inline as base64 — Resend's batch endpoint
    // does not reliably fetch attachments by URL.
    const attachments = await Promise.all(
      attachmentUrls.map(async (attachmentUrl, i) => {
        const res = await fetch(attachmentUrl);
        if (!res.ok) {
          throw new Error(`Failed to fetch attachment ${attachmentUrl}: ${res.status}`);
        }
        const buf = Buffer.from(await res.arrayBuffer());
        return {
          filename: attachmentFilenames[i] ?? `attachment-${i + 1}`,
          content: buf.toString('base64'),
        };
      })
    );
    console.log(`[send ${id}] attachments resolved count=${attachments.length}`);

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

    const batches = chunk(recipients, BATCH_SIZE);
    let sent = 0;
    let failed = 0;

    for (const batch of batches) {
      const results = await resend.batch.send(
        batch.map(email => ({
          from:    fromHeader,
          to:      email,
          subject: broadcast.subject,
          html:    emailHtml,
          ...(attachments.length ? { attachments } : {}),
        }))
      );

      // resend.batch.send returns { data: [...] | null, error }
      if (results.error) {
        console.error('Batch error:', results.error);
        failed += batch.length;
      } else {
        sent += results.data?.length ?? batch.length;
      }
    }

    if (!isTest) {
      await sql`
        UPDATE broadcasts
        SET sent_at = NOW(), sent_count = ${sent}
        WHERE id = ${id!}
      `;
    }

    return new Response(JSON.stringify({ sent, failed, total: recipients.length, test: isTest }), {
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
