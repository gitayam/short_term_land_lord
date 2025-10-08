/**
 * Send Email Verification Endpoint
 * POST /api/auth/send-verification
 * Sends or resends email verification link
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';
import { sendEmail, generateVerificationEmail } from '../../utils/email';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Check if already verified
    if (user.email_verified) {
      return new Response(
        JSON.stringify({
          error: 'Email already verified',
          email_verified: true,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get user from database to ensure we have latest data
    const dbUser = await env.DB.prepare(
      'SELECT id, email, first_name, email_verification_token, email_verification_sent_at FROM users WHERE id = ?'
    )
      .bind(user.userId)
      .first();

    if (!dbUser) {
      return new Response(
        JSON.stringify({ error: 'User not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if verification was sent recently (rate limiting)
    const lastSent = dbUser.email_verification_sent_at
      ? new Date(dbUser.email_verification_sent_at as string)
      : null;

    if (lastSent) {
      const timeSinceLastSent = Date.now() - lastSent.getTime();
      const cooldownPeriod = 5 * 60 * 1000; // 5 minutes

      if (timeSinceLastSent < cooldownPeriod) {
        const waitMinutes = Math.ceil((cooldownPeriod - timeSinceLastSent) / 1000 / 60);
        return new Response(
          JSON.stringify({
            error: `Please wait ${waitMinutes} minute(s) before requesting another verification email`,
          }),
          {
            status: 429,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Generate or reuse verification token
    let verificationToken = dbUser.email_verification_token as string;

    if (!verificationToken) {
      verificationToken = crypto.randomUUID();

      await env.DB.prepare(
        `UPDATE users
         SET email_verification_token = ?, email_verification_sent_at = datetime('now')
         WHERE id = ?`
      )
        .bind(verificationToken, user.userId)
        .run();
    } else {
      // Just update sent timestamp
      await env.DB.prepare(
        `UPDATE users
         SET email_verification_sent_at = datetime('now')
         WHERE id = ?`
      )
        .bind(user.userId)
        .run();
    }

    // Build verification URL
    const baseUrl = env.FRONTEND_URL || 'https://yourdomain.com';
    const verificationUrl = `${baseUrl}/verify-email?token=${verificationToken}`;

    // Generate and send email
    const { html, text } = generateVerificationEmail(
      verificationUrl,
      dbUser.first_name as string | undefined
    );

    await sendEmail(env, {
      to: dbUser.email as string,
      subject: 'Verify Your Email Address - Short Term Land Lord',
      html,
      text,
    });

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Verification email sent',
        email: dbUser.email,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Send Verification] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to send verification email',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
