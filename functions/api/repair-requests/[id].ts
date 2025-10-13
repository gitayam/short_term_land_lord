/**
 * Repair Request Detail API
 * GET    /api/repair-requests/[id] - Get repair request details
 * PUT    /api/repair-requests/[id] - Review repair request (approve/reject)
 * POST   /api/repair-requests/[id]/convert - Convert to task
 * DELETE /api/repair-requests/[id] - Delete repair request
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/repair-requests/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const requestId = params.id as string;

    const repairRequest = await env.DB.prepare(
      `SELECT
        rr.*,
        p.name as property_name,
        p.address as property_address,
        p.owner_id as property_owner_id,
        u.first_name || ' ' || u.last_name as reported_by_name,
        u.email as reported_by_email,
        rv.first_name || ' ' || rv.last_name as reviewed_by_name
       FROM repair_request rr
       JOIN property p ON rr.property_id = p.id
       JOIN users u ON rr.reported_by_id = u.id
       LEFT JOIN users rv ON rr.reviewed_by_id = rv.id
       WHERE rr.id = ?`
    )
      .bind(requestId)
      .first();

    if (!repairRequest) {
      return new Response(
        JSON.stringify({ error: 'Repair request not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check access
    const propertyOwnerId = (repairRequest as any).property_owner_id;
    const hasAccess =
      user.role === 'admin' ||
      user.role === 'property_manager' ||
      propertyOwnerId === user.userId ||
      (repairRequest as any).reported_by_id === user.userId;

    if (!hasAccess) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get images
    const images = await env.DB.prepare(
      'SELECT * FROM repair_request_image WHERE repair_request_id = ? ORDER BY uploaded_at ASC'
    )
      .bind(requestId)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        request: {
          ...repairRequest,
          images: images.results || [],
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Repair Request GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch repair request',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/repair-requests/[id] - Review (approve/reject)
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const requestId = params.id as string;
    const data = await request.json();
    const { status, review_notes } = data;

    // Only admins and property managers can review
    if (user.role !== 'admin' && user.role !== 'property_manager' && user.role !== 'property_owner') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Only property owners/managers can review requests' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify repair request exists
    const repairRequest = await env.DB.prepare(
      `SELECT rr.*, p.owner_id
       FROM repair_request rr
       JOIN property p ON rr.property_id = p.id
       WHERE rr.id = ?`
    )
      .bind(requestId)
      .first();

    if (!repairRequest) {
      return new Response(
        JSON.stringify({ error: 'Repair request not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Property owners can only review requests for their properties
    if (user.role === 'property_owner' && (repairRequest as any).owner_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Update review
    await env.DB.prepare(
      `UPDATE repair_request SET
        status = ?,
        review_notes = ?,
        reviewed_by_id = ?,
        reviewed_at = datetime('now'),
        updated_at = datetime('now')
       WHERE id = ?`
    )
      .bind(status, review_notes || null, user.userId, requestId)
      .run();

    // Get updated request
    const updated = await env.DB.prepare('SELECT * FROM repair_request WHERE id = ?')
      .bind(requestId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        request: updated,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Repair Request PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to update repair request',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/repair-requests/[id]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const requestId = params.id as string;

    // Verify repair request exists and check ownership
    const repairRequest = await env.DB.prepare(
      `SELECT rr.*, p.owner_id
       FROM repair_request rr
       JOIN property p ON rr.property_id = p.id
       WHERE rr.id = ?`
    )
      .bind(requestId)
      .first();

    if (!repairRequest) {
      return new Response(
        JSON.stringify({ error: 'Repair request not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Only the reporter, property owner, or admin can delete
    const canDelete =
      user.role === 'admin' ||
      user.role === 'property_manager' ||
      (repairRequest as any).reported_by_id === user.userId ||
      (repairRequest as any).owner_id === user.userId;

    if (!canDelete) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Delete repair request (cascades to images)
    await env.DB.prepare('DELETE FROM repair_request WHERE id = ?')
      .bind(requestId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Repair request deleted successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Repair Request DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to delete repair request',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
