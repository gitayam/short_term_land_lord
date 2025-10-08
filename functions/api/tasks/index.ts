/**
 * Tasks API - List and Create
 * GET  /api/tasks - List all tasks for authenticated user
 * POST /api/tasks - Create a new task
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/tasks
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const propertyId = url.searchParams.get('property_id');

    let query = `
      SELECT
        t.id, t.title, t.description, t.status, t.priority,
        t.due_date, t.created_at, t.property_id,
        p.name as property_name
      FROM task t
      LEFT JOIN property p ON t.property_id = p.id
      WHERE t.creator_id = ?
    `;

    const params: any[] = [user.userId];

    if (status) {
      query += ' AND t.status = ?';
      params.push(status.toUpperCase());
    }

    if (propertyId) {
      query += ' AND t.property_id = ?';
      params.push(propertyId);
    }

    query += ' ORDER BY t.due_date ASC, t.created_at DESC';

    const stmt = env.DB.prepare(query);
    const tasks = await stmt.bind(...params).all();

    return new Response(
      JSON.stringify({
        success: true,
        tasks: tasks.results || [],
        count: tasks.results?.length || 0,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Tasks GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch tasks',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/tasks
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    if (!data.title) {
      return new Response(
        JSON.stringify({ error: 'Title is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Insert new task
    const result = await env.DB.prepare(
      `INSERT INTO task (
        creator_id, title, description, status, priority,
        property_id, due_date
      ) VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        user.userId,
        data.title,
        data.description || null,
        data.status || 'PENDING',
        data.priority || 'MEDIUM',
        data.property_id || null,
        data.due_date || null
      )
      .run();

    // Get the created task
    const task = await env.DB.prepare('SELECT * FROM task WHERE id = ?')
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        task,
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Tasks POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to create task',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
