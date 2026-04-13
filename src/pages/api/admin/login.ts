import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request, cookies, redirect }) => {
  const form = await request.formData();
  const password = form.get('password');

  if (password === import.meta.env.ADMIN_PASSWORD) {
    cookies.set('admin_token', import.meta.env.ADMIN_PASSWORD, {
      path: '/',
      httpOnly: true,
      maxAge: 60 * 60 * 24 * 7, // 7 days
      sameSite: 'strict',
    });
    return redirect('/admin');
  }

  return redirect('/admin/login?error=1');
};
