/**
 * Reset Password Endpoint
 * POST /api/auth/reset-password
 * Resets user password with valid token
 */

import { Env } from '../../_middleware';
import { hashPassword, validatePassword } from '../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const { token, password } = await request.json();

    if (!token || !password) {
      return new Response(
        JSON.stringify({ error: 'Token and password are required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate password strength
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.valid) {
      return new Response(
        JSON.stringify({
          error: 'Password does not meet requirements',
          details: passwordValidation.errors,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get token data from KV
    const tokenKey = `password-reset:${token}`;
    const tokenDataStr = await env.KV.get(tokenKey);

    if (!tokenDataStr) {
      return new Response(
        JSON.stringify({
          error: 'Invalid or expired reset token',
          expired: true,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const tokenData = JSON.parse(tokenDataStr);

    // Get user from database
    const user = await env.DB.prepare(
      'SELECT id, email, is_suspended FROM users WHERE id = ?'
    )
      .bind(tokenData.userId)
      .first();

    if (!user) {
      return new Response(
        JSON.stringify({ error: 'User not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if account is suspended
    if (user.is_suspended === 1) {
      return new Response(
        JSON.stringify({ error: 'Account is suspended' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Hash new password
    const passwordHash = await hashPassword(password);

    // Update password and clear lockout fields
    await env.DB.prepare(
      `UPDATE users
       SET password_hash = ?,
           last_password_change = datetime('now'),
           failed_login_attempts = 0,
           locked_until = NULL,
           updated_at = datetime('now')
       WHERE id = ?`
    )
      .bind(passwordHash, user.id)
      .run();

    // Delete the reset token from KV
    await env.KV.delete(tokenKey);

    // Invalidate all existing sessions for this user (force re-login)
    // First get all sessions from D1
    const sessions = await env.DB.prepare(
      'SELECT session_token FROM session_cache WHERE user_id = ?'
    )
      .bind(user.id)
      .all();

    // Delete from KV
    if (sessions.results && sessions.results.length > 0) {
      for (const session of sessions.results) {
        await env.KV.delete(`session:${(session as any).session_token}`);
      }
    }

    // Delete from D1
    await env.DB.prepare('DELETE FROM session_cache WHERE user_id = ?')
      .bind(user.id)
      .run();

    // Clear rate limit
    await env.KV.delete(`password-reset-rate:${user.id}`);

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Password reset successfully',
        email: user.email,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Reset Password] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to reset password',
        message: error.message,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
