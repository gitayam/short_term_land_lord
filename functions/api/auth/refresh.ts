/**
 * Authentication - Refresh Token Endpoint
 * POST /api/auth/refresh
 * Refreshes an existing session, extending its expiration
 */

import { Env } from '../../_middleware';
import { extractToken, getUserFromToken, createSession } from '../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    // Extract and validate current token
    const token = extractToken(request);
    const sessionData = await getUserFromToken(token, env);

    // Get full user data from database
    const user = await env.DB.prepare(
      'SELECT id, email, first_name, last_name, role, is_active, is_suspended FROM users WHERE id = ?'
    )
      .bind(sessionData.userId)
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

    // Check if account is still active
    if (!user.is_active || user.is_suspended) {
      return new Response(
        JSON.stringify({ error: 'Account is inactive or suspended' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Invalidate old session
    await env.KV.delete(`session:${token}`);
    await env.DB.prepare('DELETE FROM session_cache WHERE session_token = ?')
      .bind(token)
      .run();

    // Create new session
    const newToken = await createSession(user, env);

    return new Response(
      JSON.stringify({
        success: true,
        token: newToken,
        user: {
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          role: user.role,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Refresh Token] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to refresh token',
        message: error.message,
      }),
      {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
