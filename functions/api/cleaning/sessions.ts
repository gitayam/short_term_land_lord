/**
 * Cleaning Sessions Endpoint
 * GET /api/cleaning/sessions - List cleaning sessions
 * POST /api/cleaning/sessions - Start a new cleaning session
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    const propertyId = url.searchParams.get('property_id');
    const status = url.searchParams.get('status');
    const startDate = url.searchParams.get('start_date');
    const endDate = url.searchParams.get('end_date');

    // Build query based on user role
    let query = `
      SELECT
        cs.id, cs.property_id, cs.cleaner_id, cs.start_time, cs.end_time,
        cs.status, cs.notes, cs.created_at, cs.updated_at,
        p.name as property_name, p.address as property_address,
        u.first_name as cleaner_first_name, u.last_name as cleaner_last_name
      FROM cleaning_session cs
      LEFT JOIN property p ON cs.property_id = p.id
      LEFT JOIN users u ON cs.cleaner_id = u.id
      WHERE 1=1
    `;

    const params: any[] = [];

    // Filter based on role
    if (user.role === 'service_staff') {
      // Cleaners only see their own sessions
      query += ' AND cs.cleaner_id = ?';
      params.push(user.userId);
    } else if (user.role === 'property_owner' || user.role === 'property_manager') {
      // Owners/managers see sessions for their properties
      query += ' AND p.owner_id = ?';
      params.push(user.userId);
    } else if (user.role !== 'admin') {
      // Other roles have no access
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Apply filters
    if (propertyId) {
      query += ' AND cs.property_id = ?';
      params.push(propertyId);
    }

    if (status) {
      query += ' AND cs.status = ?';
      params.push(status);
    }

    if (startDate) {
      query += ' AND cs.start_time >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND cs.start_time <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY cs.start_time DESC';

    const sessions = await env.DB.prepare(query).bind(...params).all();

    return new Response(
      JSON.stringify({
        success: true,
        sessions: sessions.results || [],
        count: sessions.results?.length || 0,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Cleaning Sessions] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to fetch cleaning sessions',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const { property_id, notes } = await request.json();

    if (!property_id) {
      return new Response(
        JSON.stringify({ error: 'property_id is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify property exists and user has access
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(property_id)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check permissions
    if (user.role === 'property_owner' || user.role === 'property_manager') {
      if (property.owner_id !== user.userId) {
        return new Response(
          JSON.stringify({ error: 'Access denied to this property' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    } else if (user.role !== 'admin' && user.role !== 'service_staff') {
      return new Response(
        JSON.stringify({ error: 'Insufficient permissions' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if there's already an active session for this property by this cleaner
    const activeSession = await env.DB.prepare(
      `SELECT id FROM cleaning_session
       WHERE property_id = ? AND cleaner_id = ? AND status = 'in_progress'`
    )
      .bind(property_id, user.userId)
      .first();

    if (activeSession) {
      return new Response(
        JSON.stringify({
          error: 'Active cleaning session already exists for this property',
          session_id: activeSession.id,
        }),
        {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create new cleaning session
    const result = await env.DB.prepare(
      `INSERT INTO cleaning_session (property_id, cleaner_id, start_time, notes, status)
       VALUES (?, ?, datetime('now'), ?, 'in_progress')`
    )
      .bind(property_id, user.userId, notes || null)
      .run();

    // Fetch the created session
    const newSession = await env.DB.prepare(
      `SELECT
        cs.id, cs.property_id, cs.cleaner_id, cs.start_time, cs.end_time,
        cs.status, cs.notes, cs.created_at, cs.updated_at,
        p.name as property_name, p.address as property_address
      FROM cleaning_session cs
      LEFT JOIN property p ON cs.property_id = p.id
      WHERE cs.id = ?`
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        session: newSession,
        message: 'Cleaning session started',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Cleaning Sessions] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to start cleaning session',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
