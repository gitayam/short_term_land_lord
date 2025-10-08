/**
 * Verify Email Endpoint
 * POST /api/auth/verify-email
 * Verifies user email with token
 */

import { Env } from '../../_middleware';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const { token } = await request.json();

    if (!token) {
      return new Response(
        JSON.stringify({ error: 'Verification token is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Find user by verification token
    const user = await env.DB.prepare(
      'SELECT id, email, email_verified, email_verification_sent_at FROM users WHERE email_verification_token = ?'
    )
      .bind(token)
      .first();

    if (!user) {
      return new Response(
        JSON.stringify({ error: 'Invalid verification token' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if already verified
    if (user.email_verified === 1) {
      return new Response(
        JSON.stringify({
          success: true,
          message: 'Email already verified',
          email_verified: true,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check token expiration (24 hours)
    const sentAt = new Date(user.email_verification_sent_at as string);
    const expirationTime = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
    const isExpired = Date.now() - sentAt.getTime() > expirationTime;

    if (isExpired) {
      return new Response(
        JSON.stringify({
          error: 'Verification token has expired',
          expired: true,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify the email
    await env.DB.prepare(
      `UPDATE users
       SET email_verified = 1,
           email_verification_token = NULL,
           updated_at = datetime('now')
       WHERE id = ?`
    )
      .bind(user.id)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Email verified successfully',
        email: user.email,
        email_verified: true,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Verify Email] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to verify email',
        message: error.message,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
