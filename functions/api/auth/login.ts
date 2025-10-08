/**
 * Authentication - Login Endpoint
 * POST /api/auth/login
 */

import { Env } from '../../_middleware';
import { verifyPassword, createSession, validateEmail } from '../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const { email, password } = await request.json();

    // Validate input
    if (!email || !password) {
      return new Response(
        JSON.stringify({ error: 'Email and password are required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    if (!validateEmail(email)) {
      return new Response(
        JSON.stringify({ error: 'Invalid email format' }),
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

    // Verify password with bcrypt
    const passwordMatch = await verifyPassword(password, user.password_hash as string);

    if (!passwordMatch) {
      return new Response(
        JSON.stringify({ error: 'Invalid credentials' }),
        {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create session
    const sessionToken = await createSession(user, env);

    // Update last login
    await env.DB.prepare(
      'UPDATE users SET last_login = datetime("now") WHERE id = ?'
    )
      .bind(user.id)
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
