/**
 * Convert Repair Request to Task
 * POST /api/repair-requests/[id]/convert
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const requestId = params.id as string;
    const data = await request.json();
    const { assigned_to_id, due_date, priority } = data;

    // Only admins and property managers can convert
    if (user.role !== 'admin' && user.role !== 'property_manager' && user.role !== 'property_owner') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Only property owners/managers can convert requests' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get repair request
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

    // Property owners can only convert requests for their properties
    if (user.role === 'property_owner' && (repairRequest as any).owner_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if already converted
    if ((repairRequest as any).status === 'converted') {
      return new Response(
        JSON.stringify({ error: 'Repair request has already been converted to a task' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Map severity to priority
    const priorityMap: Record<string, string> = {
      low: 'LOW',
      medium: 'MEDIUM',
      high: 'HIGH',
      urgent: 'URGENT',
    };
    const taskPriority = priority || priorityMap[(repairRequest as any).severity] || 'MEDIUM';

    // Create task from repair request
    await env.DB.prepare(
      `INSERT INTO task (
        title,
        description,
        status,
        priority,
        due_date,
        creator_id,
        property_id,
        assigned_to_id,
        location,
        severity
      ) VALUES (?, ?, 'PENDING', ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        (repairRequest as any).title,
        (repairRequest as any).description,
        taskPriority,
        due_date || null,
        user.userId,
        (repairRequest as any).property_id,
        assigned_to_id || null,
        (repairRequest as any).location || null,
        (repairRequest as any).severity
      )
      .run();

    // Get the created task
    const task = await env.DB.prepare(
      `SELECT * FROM task
       WHERE title = ? AND property_id = ?
       ORDER BY created_at DESC LIMIT 1`
    )
      .bind((repairRequest as any).title, (repairRequest as any).property_id)
      .first();

    // Update repair request status to converted
    await env.DB.prepare(
      `UPDATE repair_request SET
        status = 'converted',
        converted_task_id = ?,
        reviewed_by_id = ?,
        reviewed_at = datetime('now'),
        updated_at = datetime('now')
       WHERE id = ?`
    )
      .bind((task as any).id, user.userId, requestId)
      .run();

    // Copy images to task_media
    const images = await env.DB.prepare(
      'SELECT image_url FROM repair_request_image WHERE repair_request_id = ?'
    )
      .bind(requestId)
      .all();

    for (const image of images.results || []) {
      await env.DB.prepare(
        `INSERT INTO task_media (task_id, media_type, media_url, uploaded_by_id)
         VALUES (?, 'photo', ?, ?)`
      )
        .bind((task as any).id, (image as any).image_url, user.userId)
        .run();
    }

    // TODO: Send notification to assigned worker

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Repair request converted to task successfully',
        task,
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Repair Request Convert] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to convert repair request',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
