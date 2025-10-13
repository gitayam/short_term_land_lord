/**
 * Worker Detail API
 * GET    /api/workers/[id] - Get single worker
 * PUT    /api/workers/[id] - Update worker
 * DELETE /api/workers/[id] - Deactivate worker
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/workers/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const workerId = params.id as string;

    // Workers can view their own info, admins/managers can view any worker
    if (
      user.userId !== workerId &&
      user.role !== 'admin' &&
      user.role !== 'property_manager'
    ) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const worker = await env.DB.prepare(
      `SELECT id, email, first_name, last_name, role, phone, is_active, created_at, last_login
       FROM users WHERE id = ? AND role IN ('service_staff', 'property_manager', 'admin')`
    )
      .bind(workerId)
      .first();

    if (!worker) {
      return new Response(
        JSON.stringify({ error: 'Worker not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get assigned properties if worker
    const assignments = await env.DB.prepare(
      `SELECT pa.*, p.name as property_name, p.address
       FROM property_assignment pa
       JOIN property p ON pa.property_id = p.id
       WHERE pa.worker_id = ?
       ORDER BY pa.assigned_at DESC`
    )
      .bind(workerId)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        worker,
        assignments: assignments.results || [],
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Worker GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch worker',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/workers/[id]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const workerId = params.id as string;
    const data = await request.json();

    // Only admins and property_managers can update workers
    // Workers can update their own limited fields
    const isSelfUpdate = user.userId === workerId;
    const isAdmin = user.role === 'admin' || user.role === 'property_manager';

    if (!isSelfUpdate && !isAdmin) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify worker exists
    const worker = await env.DB.prepare(
      'SELECT id FROM users WHERE id = ? AND role IN (\'service_staff\', \'property_manager\')'
    )
      .bind(workerId)
      .first();

    if (!worker) {
      return new Response(
        JSON.stringify({ error: 'Worker not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Build update query based on permissions
    if (isSelfUpdate && !isAdmin) {
      // Workers can only update their own contact info
      await env.DB.prepare(
        `UPDATE users SET
          first_name = COALESCE(?, first_name),
          last_name = COALESCE(?, last_name),
          phone = COALESCE(?, phone),
          updated_at = datetime('now')
         WHERE id = ?`
      )
        .bind(
          data.first_name || null,
          data.last_name || null,
          data.phone || null,
          workerId
        )
        .run();
    } else {
      // Admins can update everything including role and active status
      await env.DB.prepare(
        `UPDATE users SET
          first_name = COALESCE(?, first_name),
          last_name = COALESCE(?, last_name),
          phone = COALESCE(?, phone),
          role = COALESCE(?, role),
          is_active = COALESCE(?, is_active),
          updated_at = datetime('now')
         WHERE id = ?`
      )
        .bind(
          data.first_name || null,
          data.last_name || null,
          data.phone || null,
          data.role || null,
          data.is_active !== undefined ? data.is_active : null,
          workerId
        )
        .run();
    }

    // Get updated worker
    const updated = await env.DB.prepare(
      'SELECT id, email, first_name, last_name, role, phone, is_active, created_at FROM users WHERE id = ?'
    )
      .bind(workerId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        worker: updated,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Worker PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to update worker',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/workers/[id] - Deactivate worker
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const workerId = params.id as string;

    // Only admins and property_managers can deactivate workers
    if (user.role !== 'admin' && user.role !== 'property_manager') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify worker exists
    const worker = await env.DB.prepare(
      'SELECT id FROM users WHERE id = ? AND role IN (\'service_staff\', \'property_manager\')'
    )
      .bind(workerId)
      .first();

    if (!worker) {
      return new Response(
        JSON.stringify({ error: 'Worker not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Deactivate instead of delete (soft delete)
    await env.DB.prepare(
      'UPDATE users SET is_active = 0, updated_at = datetime(\'now\') WHERE id = ?'
    )
      .bind(workerId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Worker deactivated successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Worker DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to deactivate worker',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
