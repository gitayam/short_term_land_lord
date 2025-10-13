/**
 * Workers API
 * GET  /api/workers - List all workers
 * POST /api/workers - Invite new worker
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

interface WorkerRow {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  phone: string | null;
  is_active: number;
  created_at: string;
}

// GET /api/workers - List all workers
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only admins and property_managers can view workers
    if (user.role !== 'admin' && user.role !== 'property_manager') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Admin or Property Manager access required' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get all workers (service_staff and property_manager roles)
    const workers = await env.DB.prepare(
      `SELECT id, email, first_name, last_name, role, phone, is_active, created_at
       FROM users
       WHERE role IN ('service_staff', 'property_manager')
       ORDER BY created_at DESC`
    )
      .all<WorkerRow>();

    return new Response(
      JSON.stringify({
        success: true,
        workers: workers.results || [],
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Workers GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch workers',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/workers - Invite new worker
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only admins and property_managers can invite workers
    if (user.role !== 'admin' && user.role !== 'property_manager') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Admin or Property Manager access required' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const data = await request.json();
    const { email, role = 'service_staff' } = data;

    if (!email) {
      return new Response(
        JSON.stringify({ error: 'Email is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate role
    if (!['service_staff', 'property_manager'].includes(role)) {
      return new Response(
        JSON.stringify({ error: 'Invalid role. Must be service_staff or property_manager' }),
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
      .bind(email)
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

    // Generate invitation token
    const token = crypto.randomUUID();

    // Set expiration to 7 days from now
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 7);

    // Create invitation
    await env.DB.prepare(
      `INSERT INTO worker_invitation (email, role, invited_by_id, invitation_token, expires_at)
       VALUES (?, ?, ?, ?, ?)`
    )
      .bind(email, role, user.userId, token, expiresAt.toISOString())
      .run();

    // TODO: Send invitation email with token
    // For now, return the token in the response
    const invitationUrl = `${new URL(request.url).origin}/accept-invitation?token=${token}`;

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Worker invitation created successfully',
        invitation: {
          email,
          role,
          token,
          invitationUrl,
          expiresAt: expiresAt.toISOString(),
        },
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Workers POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to create worker invitation',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
