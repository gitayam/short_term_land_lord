/**
 * Authentication - Login Endpoint
 * POST /api/auth/login
 */

import { Env } from '../../_middleware';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return new Response(
        JSON.stringify({ error: 'Email and password are required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get user from database
    const user = await env.DB.prepare(
      'SELECT id, email, first_name, last_name, role, password_hash, is_active, is_suspended FROM users WHERE email = ?'
    )
      .bind(email.toLowerCase())
      .first();

    if (!user) {
      return new Response(
        JSON.stringify({ error: 'Invalid credentials' }),
        {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if account is active
    if (!user.is_active || user.is_suspended) {
      return new Response(
        JSON.stringify({ error: 'Account is inactive or suspended' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // TODO: Implement password verification with bcrypt
    // For now, this is a placeholder
    // const passwordMatch = await verifyPassword(password, user.password_hash);

    // Generate session token (simple UUID for now)
    const sessionToken = crypto.randomUUID();

    // Store session in KV (expires in 24 hours)
    const sessionData = {
      userId: user.id,
      email: user.email,
      role: user.role,
      firstName: user.first_name,
      lastName: user.last_name,
      createdAt: new Date().toISOString(),
    };

    await env.KV.put(`session:${sessionToken}`, JSON.stringify(sessionData), {
      expirationTtl: 86400, // 24 hours
    });

    // Also store in D1 for persistence
    await env.DB.prepare(
      `INSERT INTO session_cache (session_token, user_id, user_data, expires_at)
       VALUES (?, ?, ?, datetime('now', '+1 day'))`
    )
      .bind(sessionToken, user.id, JSON.stringify(sessionData))
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        token: sessionToken,
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
    console.error('[Login] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        message: error.message,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
