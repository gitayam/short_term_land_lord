/**
 * Request Password Reset Endpoint
 * POST /api/auth/request-password-reset
 * Sends password reset email with token
 */

import { Env } from '../../_middleware';
import { validateEmail } from '../../utils/auth';
import { sendEmail, generatePasswordResetEmail } from '../../utils/email';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const { email } = await request.json();

    if (!email) {
      return new Response(
        JSON.stringify({ error: 'Email is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate email format
    if (!validateEmail(email)) {
      return new Response(
        JSON.stringify({ error: 'Invalid email format' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Find user by email
    const user = await env.DB.prepare(
      'SELECT id, email, first_name, is_suspended FROM users WHERE email = ?'
    )
      .bind(email.toLowerCase())
      .first();

    // Always return success even if user doesn't exist (security best practice)
    // This prevents email enumeration attacks
    if (!user) {
      return new Response(
        JSON.stringify({
          success: true,
          message: 'If an account exists with this email, a password reset link has been sent',
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if account is suspended
    if (user.is_suspended === 1) {
      return new Response(
        JSON.stringify({
          success: true,
          message: 'If an account exists with this email, a password reset link has been sent',
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check rate limiting (prevent spam)
    const rateLimitKey = `password-reset-rate:${user.id}`;
    const lastResetRequest = await env.KV.get(rateLimitKey);

    if (lastResetRequest) {
      const lastRequestTime = parseInt(lastResetRequest, 10);
      const timeSinceLastRequest = Date.now() - lastRequestTime;
      const cooldownPeriod = 15 * 60 * 1000; // 15 minutes

      if (timeSinceLastRequest < cooldownPeriod) {
        // Still return success to prevent information disclosure
        return new Response(
          JSON.stringify({
            success: true,
            message: 'If an account exists with this email, a password reset link has been sent',
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Generate password reset token
    const resetToken = crypto.randomUUID();

    // Store token in KV with 1 hour expiration
    const tokenData = {
      userId: user.id,
      email: user.email,
      createdAt: new Date().toISOString(),
    };

    await env.KV.put(`password-reset:${resetToken}`, JSON.stringify(tokenData), {
      expirationTtl: 3600, // 1 hour
    });

    // Update rate limit
    await env.KV.put(rateLimitKey, Date.now().toString(), {
      expirationTtl: 900, // 15 minutes
    });

    // Build reset URL
    const baseUrl = env.FRONTEND_URL || 'https://yourdomain.com';
    const resetUrl = `${baseUrl}/reset-password?token=${resetToken}`;

    // Generate and send email
    const { html, text } = generatePasswordResetEmail(
      resetUrl,
      user.first_name as string | undefined
    );

    await sendEmail(
      {
        to: user.email as string,
        subject: 'Reset Your Password - Short Term Land Lord',
        html,
      },
      env.RESEND_API_KEY
    );

    return new Response(
      JSON.stringify({
        success: true,
        message: 'If an account exists with this email, a password reset link has been sent',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Request Password Reset] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to process password reset request',
        message: error.message,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
