/**
 * Authentication - Register Endpoint
 * POST /api/auth/register
 */

import { Env } from '../../_middleware';
import { hashPassword, validatePassword, validateEmail, createSession } from '../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const { email, password, first_name, last_name, role } = await request.json();

    // Validate required fields
    if (!email || !password || !first_name || !last_name) {
      return new Response(
        JSON.stringify({
          error: 'Email, password, first name, and last name are required',
        }),
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

    // Check if user already exists
    const existingUser = await env.DB.prepare(
      'SELECT id FROM users WHERE email = ?'
    )
      .bind(email.toLowerCase())
      .first();

    if (existingUser) {
      return new Response(
        JSON.stringify({ error: 'Email already registered' }),
        {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Hash password
    const password_hash = await hashPassword(password);

    // Determine role (default to property_owner if not specified)
    const userRole = role || 'property_owner';

    // Create user
    const result = await env.DB.prepare(
      `INSERT INTO users (
        email, password_hash, first_name, last_name, role,
        is_active, email_verified, created_at
      ) VALUES (?, ?, ?, ?, ?, 1, 0, datetime('now'))`
    )
      .bind(
        email.toLowerCase(),
        password_hash,
        first_name,
        last_name,
        userRole
      )
      .run();

    // Get created user
    const user = await env.DB.prepare(
      'SELECT id, email, first_name, last_name, role FROM users WHERE id = ?'
    )
      .bind(result.meta.last_row_id)
      .first();

    // Create session
    const sessionToken = await createSession(user, env);

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
        message: 'Registration successful. Please check your email to verify your account.',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Register] Error:', error);
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
