import { Resend } from 'resend';

export function getResend() {
  return new Resend(import.meta.env.RESEND_API_KEY);
}

export function confirmationEmail(firstName: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background:#F5EED8;">
  <div style="max-width:560px;margin:0 auto;font-family:Georgia,serif;">

    <div style="background:#1D3A2A;padding:1.75rem 2.5rem;border-bottom:3px solid #C8872A;">
      <p style="margin:0;font-family:Arial,sans-serif;font-weight:700;font-size:1rem;
                letter-spacing:0.08em;color:#F5EED8;">
        MONTAVILLA <span style="color:#E8A832;">LAND TRUST</span>
      </p>
    </div>

    <div style="background:#1D3A2A;padding:2.5rem;">
      <h1 style="font-family:Arial,sans-serif;font-weight:900;font-size:2.8rem;
                 color:#F5EED8;margin:0 0 0.25rem;line-height:1;letter-spacing:-0.02em;">
        YOU'RE IN${firstName ? `, ${firstName.toUpperCase()}` : ''}.
      </h1>

      <p style="font-size:1.15rem;color:#7A9E7E;line-height:1.65;margin:1.5rem 0 1rem;">
        Thank you for signing the Montavilla Community Land Trust petition.
        You're now on our founding member list — and that matters more than you might think.
      </p>

      <p style="font-size:1.1rem;color:#7A9E7E;line-height:1.65;margin:0 0 1rem;">
        Every name tells the city, the sellers, and our grant partners that Montavilla
        is organized and serious about owning this land — together.
      </p>

      <div style="border-left:4px solid #C8872A;padding:1rem 1.5rem;margin:2rem 0;
                  background:rgba(255,255,255,0.04);">
        <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;
                  color:#E8A832;margin:0 0 0.5rem;font-family:Arial,sans-serif;">
          What Happens Next
        </p>
        <p style="font-size:1.05rem;color:#7A9E7E;line-height:1.65;margin:0;">
          We're forming a steering committee and planning our first community meeting.
          We'll be in touch with the date, location, and ways to get more deeply involved.
        </p>
      </div>

      <p style="font-size:1.05rem;color:#7A9E7E;line-height:1.65;margin:0 0 0.75rem;">
        In the meantime, the single most powerful thing you can do is
        <strong style="color:#F5EED8;">tell your neighbors</strong>.
        Every conversation builds the coalition.
      </p>

      <p style="font-size:1.05rem;color:#7A9E7E;line-height:1.65;margin:0;">
        Follow <strong style="color:#E8A832;">#MontavillaLandTrust</strong> for updates.
      </p>
    </div>

    <div style="background:#0E1F16;padding:1.5rem 2.5rem;border-top:1px solid rgba(122,158,126,0.15);">
      <p style="font-size:0.8rem;color:rgba(122,158,126,0.6);margin:0;line-height:1.8;">
        Montavilla Community Land Trust · montavillalandtrust.org<br>
        Montavilla, Portland OR 97215 ·
        <a href="mailto:info@montavillalandtrust.org"
           style="color:#E8A832;text-decoration:none;">info@montavillalandtrust.org</a>
      </p>
      <p style="font-size:0.72rem;color:rgba(122,158,126,0.35);margin:0.6rem 0 0;line-height:1.6;">
        You signed the MCLT founding petition. To unsubscribe, reply with "unsubscribe".
      </p>
    </div>

  </div>
</body>
</html>`;
}

export function adminNotificationEmail(data: {
  firstName: string;
  lastName: string;
  email: string;
  neighborhood: string;
  howCanHelp: string;
  message: string;
}): string {
  const row = (label: string, value: string) =>
    value
      ? `<tr>
           <td style="padding:0.5rem 0.75rem;font-family:Arial,sans-serif;font-size:0.8rem;
                      font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                      color:#7A9E7E;white-space:nowrap;vertical-align:top;">${label}</td>
           <td style="padding:0.5rem 0.75rem;font-size:1rem;color:#F5EED8;line-height:1.5;">${value}</td>
         </tr>`
      : '';

  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0E1F16;">
  <div style="max-width:520px;margin:0 auto;font-family:Georgia,serif;">

    <div style="background:#1D3A2A;padding:1.25rem 2rem;border-bottom:3px solid #C8872A;">
      <p style="margin:0;font-family:Arial,sans-serif;font-size:0.75rem;font-weight:700;
                letter-spacing:0.15em;text-transform:uppercase;color:#E8A832;">
        New MCLT Petition Signature
      </p>
    </div>

    <div style="background:#1D3A2A;padding:2rem;">
      <table style="width:100%;border-collapse:collapse;border:1px solid rgba(122,158,126,0.2);">
        ${row('Name',          `${data.firstName} ${data.lastName}`.trim())}
        ${row('Email',         `<a href="mailto:${data.email}" style="color:#E8A832;">${data.email}</a>`)}
        ${row('Neighborhood',  data.neighborhood)}
        ${row('How can help',  data.howCanHelp)}
        ${row('Message',       data.message)}
      </table>
    </div>

    <div style="background:#0E1F16;padding:1rem 2rem;">
      <p style="font-size:0.75rem;color:rgba(122,158,126,0.4);margin:0;">
        montavillalandtrust.org · MCLT admin notification
      </p>
    </div>

  </div>
</body>
</html>`;
}
