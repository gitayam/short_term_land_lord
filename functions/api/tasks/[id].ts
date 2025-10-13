/**
 * Task Detail API
 * GET    /api/tasks/[id] - Get single task
 * PUT    /api/tasks/[id] - Update task
 * DELETE /api/tasks/[id] - Delete task
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/tasks/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const taskId = params.id as string;

    const task = await env.DB.prepare(
      `SELECT
        t.id, t.title, t.description, t.status, t.priority,
        t.due_date, t.created_at, t.property_id,
        p.name as property_name
      FROM task t
      LEFT JOIN property p ON t.property_id = p.id
      WHERE t.id = ? AND t.creator_id = ?`
    )
      .bind(taskId, user.userId)
      .first();

    if (!task) {
      return new Response(
        JSON.stringify({ error: 'Task not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    return new Response(
      JSON.stringify({
        success: true,
        task,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Task GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch task',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/tasks/[id]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const taskId = params.id as string;
    const data = await request.json();

    // Verify ownership
    const task = await env.DB.prepare(
      'SELECT id FROM task WHERE id = ? AND creator_id = ?'
    )
      .bind(taskId, user.userId)
      .first();

    if (!task) {
      return new Response(
        JSON.stringify({ error: 'Task not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Build update query dynamically
    const updates: string[] = [];
    const params: any[] = [];

    if (data.title !== undefined) {
      updates.push('title = ?');
      params.push(data.title);
    }

    if (data.description !== undefined) {
      updates.push('description = ?');
      params.push(data.description);
    }

    if (data.status !== undefined) {
      updates.push('status = ?');
      params.push(data.status);
    }

    if (data.priority !== undefined) {
      updates.push('priority = ?');
      params.push(data.priority);
    }

    if (data.property_id !== undefined) {
      updates.push('property_id = ?');
      params.push(data.property_id || null);
    }

    if (data.due_date !== undefined) {
      updates.push('due_date = ?');
      params.push(data.due_date || null);
    }

    if (updates.length === 0) {
      return new Response(
        JSON.stringify({ error: 'No fields to update' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    params.push(taskId);

    await env.DB.prepare(
      `UPDATE task SET ${updates.join(', ')} WHERE id = ?`
    )
      .bind(...params)
      .run();

    // Get updated task
    const updated = await env.DB.prepare(
      `SELECT
        t.id, t.title, t.description, t.status, t.priority,
        t.due_date, t.created_at, t.property_id,
        p.name as property_name
      FROM task t
      LEFT JOIN property p ON t.property_id = p.id
      WHERE t.id = ?`
    )
      .bind(taskId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        task: updated,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Task PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to update task',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/tasks/[id]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const taskId = params.id as string;

    // Verify ownership
    const task = await env.DB.prepare(
      'SELECT id FROM task WHERE id = ? AND creator_id = ?'
    )
      .bind(taskId, user.userId)
      .first();

    if (!task) {
      return new Response(
        JSON.stringify({ error: 'Task not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Delete task
    await env.DB.prepare('DELETE FROM task WHERE id = ?').bind(taskId).run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Task deleted successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Task DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to delete task',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
