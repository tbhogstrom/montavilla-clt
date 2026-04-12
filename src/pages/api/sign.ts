import type { APIRoute } from 'astro';
import { getDb } from '../../lib/db';
import { getResend, confirmationEmail, adminNotificationEmail } from '../../lib/email';

export const POST: APIRoute = async ({ request }) => {
  try {
    const { firstName, lastName, email, neighborhood, howCanHelp, message } =
      await request.json();

    if (!email?.includes('@')) {
      return new Response(JSON.stringify({ error: 'Valid email required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // ── DB insert ────────────────────────────────────────────────
    const sql = getDb();

    await sql`
      CREATE TABLE IF NOT EXISTS signups (
        id           SERIAL PRIMARY KEY,
        first_name   TEXT NOT NULL DEFAULT '',
        last_name    TEXT NOT NULL DEFAULT '',
        email        TEXT NOT NULL,
        neighborhood TEXT,
        how_can_help TEXT,
        message      TEXT,
        created_at   TIMESTAMPTZ DEFAULT NOW()
      )
    `;

    await sql`
      INSERT INTO signups (first_name, last_name, email, neighborhood, how_can_help, message)
      VALUES (
        ${firstName  ?? ''},
        ${lastName   ?? ''},
        ${email},
        ${neighborhood ?? null},
        ${howCanHelp   ?? null},
        ${message      ?? null}
      )
    `;

    // ── Email ────────────────────────────────────────────────────
    // Fire-and-forget — a failed email never blocks a successful signup
    const resend  = getResend();
    const FROM    = import.meta.env.FROM_EMAIL   ?? 'noreply@montavillalandtrust.org';
    const ADMIN   = import.meta.env.ADMIN_EMAIL  ?? 'info@montavillalandtrust.org';
    const name    = [firstName, lastName].filter(Boolean).join(' ') || 'there';

    const [confirmation, notification] = await Promise.allSettled([
      // Confirmation to signer
      resend.emails.send({
        from:    `Montavilla Land Trust <${FROM}>`,
        to:      email,
        subject: `You're signed — welcome to MCLT`,
        html:    confirmationEmail(firstName ?? ''),
      }),
      // Notification to admin
      resend.emails.send({
        from:    `MCLT Signups <${FROM}>`,
        to:      ADMIN,
        subject: `New MCLT signature: ${name}`,
        html:    adminNotificationEmail({ firstName, lastName, email, neighborhood, howCanHelp, message }),
      }),
    ]);

    if (confirmation.status === 'rejected')
      console.error('Confirmation email failed:', confirmation.reason);
    else if (confirmation.value.error)
      console.error('Confirmation email error:', confirmation.value.error);

    if (notification.status === 'rejected')
      console.error('Admin notification failed:', notification.reason);
    else if (notification.value.error)
      console.error('Admin notification error:', notification.value.error);

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('Signup error:', err);
    return new Response(JSON.stringify({ error: 'Server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
