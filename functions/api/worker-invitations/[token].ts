/**
 * Worker Invitation API
 * GET  /api/worker-invitations/[token] - Get invitation details
 * POST /api/worker-invitations/[token] - Accept invitation and create account
 */

import { Env } from '../../_middleware';

interface InvitationRow {
  id: string;
  email: string;
  role: string;
  invitation_token: string;
  expires_at: string;
  accepted_at: string | null;
  invited_by_id: string;
}

// GET /api/worker-invitations/[token]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, env } = context;

  try {
    const token = params.token as string;

    const invitation = await env.DB.prepare(
      `SELECT
        wi.*,
        u.first_name || ' ' || u.last_name as invited_by_name
       FROM worker_invitation wi
       JOIN users u ON wi.invited_by_id = u.id
       WHERE wi.invitation_token = ?`
    )
      .bind(token)
      .first<InvitationRow>();

    if (!invitation) {
      return new Response(
        JSON.stringify({ error: 'Invalid invitation token' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if already accepted
    if (invitation.accepted_at) {
      return new Response(
        JSON.stringify({ error: 'Invitation has already been accepted' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if expired
    const now = new Date();
    const expiresAt = new Date(invitation.expires_at);
    if (now > expiresAt) {
      return new Response(
        JSON.stringify({ error: 'Invitation has expired' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    return new Response(
      JSON.stringify({
        success: true,
        invitation: {
          email: invitation.email,
          role: invitation.role,
          invited_by_name: (invitation as any).invited_by_name,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Worker Invitation GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch invitation',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/worker-invitations/[token]
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const token = params.token as string;
    const data = await request.json();
    const { first_name, last_name, password, phone } = data;

    if (!first_name || !last_name || !password) {
      return new Response(
        JSON.stringify({ error: 'first_name, last_name, and password are required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get invitation
    const invitation = await env.DB.prepare(
      'SELECT * FROM worker_invitation WHERE invitation_token = ?'
    )
      .bind(token)
      .first<InvitationRow>();

    if (!invitation) {
      return new Response(
        JSON.stringify({ error: 'Invalid invitation token' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if already accepted
    if (invitation.accepted_at) {
      return new Response(
        JSON.stringify({ error: 'Invitation has already been accepted' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if expired
    const now = new Date();
    const expiresAt = new Date(invitation.expires_at);
    if (now > expiresAt) {
      return new Response(
        JSON.stringify({ error: 'Invitation has expired' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if user already exists with this email
    const existingUser = await env.DB.prepare(
      'SELECT id FROM users WHERE email = ?'
    )
      .bind(invitation.email)
      .first();

    if (existingUser) {
      return new Response(
        JSON.stringify({ error: 'User with this email already exists' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Hash password (simple hash for now - in production use bcrypt or similar)
    const encoder = new TextEncoder();
    const data_buf = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data_buf);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const password_hash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

    // Create user account
    await env.DB.prepare(
      `INSERT INTO users (email, first_name, last_name, password_hash, role, phone, is_active)
       VALUES (?, ?, ?, ?, ?, ?, 1)`
    )
      .bind(
        invitation.email,
        first_name,
        last_name,
        password_hash,
        invitation.role,
        phone || null
      )
      .run();

    // Mark invitation as accepted
    await env.DB.prepare(
      'UPDATE worker_invitation SET accepted_at = datetime(\'now\') WHERE id = ?'
    )
      .bind(invitation.id)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Account created successfully. You can now log in.',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Worker Invitation POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to accept invitation',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
