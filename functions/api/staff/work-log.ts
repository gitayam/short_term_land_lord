/**
 * Staff Work Log API
 * GET /api/staff/work-log - List work logs
 * POST /api/staff/work-log - Create work log (clock in/out)
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/staff/work-log
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only staff can access work logs
    if (!['service_staff', 'property_manager', 'admin'].includes(user.role)) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Staff access required' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const url = new URL(request.url);
    const propertyId = url.searchParams.get('property_id');
    const startDate = url.searchParams.get('start_date');
    const endDate = url.searchParams.get('end_date');

    let query = `
      SELECT
        wl.*,
        p.name as property_name,
        p.address as property_address
      FROM staff_work_log wl
      JOIN property p ON wl.property_id = p.id
      WHERE wl.worker_id = ?
    `;

    const bindings: any[] = [user.userId];

    if (propertyId) {
      query += ' AND wl.property_id = ?';
      bindings.push(propertyId);
    }

    if (startDate) {
      query += ' AND date(wl.start_time) >= ?';
      bindings.push(startDate);
    }

    if (endDate) {
      query += ' AND date(wl.start_time) <= ?';
      bindings.push(endDate);
    }

    query += ' ORDER BY wl.start_time DESC LIMIT 100';

    const stmt = env.DB.prepare(query);
    const workLogs = await (bindings.length > 0 ? stmt.bind(...bindings) : stmt).all();

    return new Response(
      JSON.stringify({
        success: true,
        work_logs: workLogs.results || [],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Staff Work Log GET] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to fetch work logs' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/staff/work-log - Create work log
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only staff can create work logs
    if (!['service_staff', 'property_manager', 'admin'].includes(user.role)) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Staff access required' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const data = await request.json();
    const {
      property_id,
      task_id,
      repair_request_id,
      start_time,
      end_time,
      work_type,
      description,
      notes,
      photos,
    } = data;

    if (!property_id || !start_time) {
      return new Response(
        JSON.stringify({ error: 'property_id and start_time are required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify worker is assigned to this property
    const assignment = await env.DB.prepare(
      'SELECT id FROM property_assignment WHERE property_id = ? AND worker_id = ? AND is_active = 1'
    )
      .bind(property_id, user.userId)
      .first();

    if (!assignment && user.role !== 'admin') {
      return new Response(
        JSON.stringify({ error: 'You are not assigned to this property' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Calculate duration if end_time provided
    let durationMinutes = null;
    if (end_time) {
      const start = new Date(start_time);
      const end = new Date(end_time);
      durationMinutes = Math.round((end.getTime() - start.getTime()) / 60000);
    }

    // Create work log
    const result = await env.DB.prepare(
      `INSERT INTO staff_work_log (
        worker_id, property_id, task_id, repair_request_id,
        start_time, end_time, duration_minutes,
        work_type, description, notes, photos
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        user.userId,
        property_id,
        task_id || null,
        repair_request_id || null,
        start_time,
        end_time || null,
        durationMinutes,
        work_type || 'other',
        description || null,
        notes || null,
        photos ? JSON.stringify(photos) : null
      )
      .run();

    // Get created work log
    const created = await env.DB.prepare(
      `SELECT wl.*, p.name as property_name, p.address as property_address
       FROM staff_work_log wl
       JOIN property p ON wl.property_id = p.id
       WHERE wl.id = ?`
    )
      .bind(result.meta.last_row_id)
      .first();

    // Create notification for property owner
    const property = await env.DB.prepare(
      'SELECT owner_id, name FROM property WHERE id = ?'
    )
      .bind(property_id)
      .first();

    if (property) {
      await env.DB.prepare(
        `INSERT INTO notification (user_id, notification_type, title, message, link)
         VALUES (?, 'work_completed', ?, ?, ?)`
      )
        .bind(
          (property as any).owner_id,
          'Work Log Submitted',
          `${user.firstName} ${user.lastName} logged work at ${(property as any).name}`,
          `/app/properties/${property_id}`
        )
        .run();
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Work log created successfully',
        work_log: created,
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Staff Work Log POST] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to create work log' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
