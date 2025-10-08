/**
 * Authentication - Logout Endpoint
 * POST /api/auth/logout
 */

import { Env } from '../../_middleware';
import { extractToken, destroySession } from '../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    // Extract token
    const token = extractToken(request);

    // Destroy session
    await destroySession(token, env);

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Logged out successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Logout] Error:', error);

    // Even if there's an error, return success
    // (token might be invalid/expired anyway)
    return new Response(
      JSON.stringify({
        success: true,
        message: 'Logged out successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
