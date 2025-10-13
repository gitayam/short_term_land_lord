/**
 * Property Assignments API
 * GET  /api/property-assignments - List all assignments
 * POST /api/property-assignments - Assign property to worker
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/property-assignments
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    const url = new URL(request.url);
    const propertyId = url.searchParams.get('property_id');
    const workerId = url.searchParams.get('worker_id');

    let query = `
      SELECT
        pa.*,
        p.name as property_name,
        p.address as property_address,
        w.first_name || ' ' || w.last_name as worker_name,
        w.email as worker_email,
        w.role as worker_role,
        ab.first_name || ' ' || ab.last_name as assigned_by_name
      FROM property_assignment pa
      JOIN property p ON pa.property_id = p.id
      JOIN users w ON pa.worker_id = w.id
      JOIN users ab ON pa.assigned_by_id = ab.id
      WHERE 1=1
    `;

    const bindings: any[] = [];

    // Filter by property if specified
    if (propertyId) {
      query += ' AND pa.property_id = ?';
      bindings.push(propertyId);
    }

    // Filter by worker if specified
    if (workerId) {
      query += ' AND pa.worker_id = ?';
      bindings.push(workerId);
    }

    // Non-admin workers can only see their own assignments
    if (user.role === 'service_staff') {
      query += ' AND pa.worker_id = ?';
      bindings.push(user.userId);
    }

    // Property owners can only see assignments for their properties
    if (user.role === 'property_owner') {
      query += ' AND p.owner_id = ?';
      bindings.push(user.userId);
    }

    query += ' ORDER BY pa.assigned_at DESC';

    const stmt = env.DB.prepare(query);
    const assignments = await (bindings.length > 0
      ? stmt.bind(...bindings)
      : stmt
    ).all();

    return new Response(
      JSON.stringify({
        success: true,
        assignments: assignments.results || [],
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Property Assignments GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch property assignments',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/property-assignments
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only admins and property_managers can create assignments
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
    const { property_id, worker_id, notes } = data;

    if (!property_id || !worker_id) {
      return new Response(
        JSON.stringify({ error: 'property_id and worker_id are required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify property exists
    const property = await env.DB.prepare(
      'SELECT id FROM property WHERE id = ?'
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

    // Verify worker exists and has appropriate role
    const worker = await env.DB.prepare(
      'SELECT id FROM users WHERE id = ? AND role IN (\'service_staff\', \'property_manager\') AND is_active = 1'
    )
      .bind(worker_id)
      .first();

    if (!worker) {
      return new Response(
        JSON.stringify({ error: 'Worker not found or not active' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if assignment already exists
    const existing = await env.DB.prepare(
      'SELECT id FROM property_assignment WHERE property_id = ? AND worker_id = ?'
    )
      .bind(property_id, worker_id)
      .first();

    if (existing) {
      return new Response(
        JSON.stringify({ error: 'Worker is already assigned to this property' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create assignment
    const result = await env.DB.prepare(
      `INSERT INTO property_assignment (property_id, worker_id, assigned_by_id, notes)
       VALUES (?, ?, ?, ?)`
    )
      .bind(property_id, worker_id, user.userId, notes || null)
      .run();

    // Get the created assignment with details
    const assignment = await env.DB.prepare(
      `SELECT
        pa.*,
        p.name as property_name,
        p.address as property_address,
        w.first_name || ' ' || w.last_name as worker_name,
        w.email as worker_email,
        ab.first_name || ' ' || ab.last_name as assigned_by_name
       FROM property_assignment pa
       JOIN property p ON pa.property_id = p.id
       JOIN users w ON pa.worker_id = w.id
       JOIN users ab ON pa.assigned_by_id = ab.id
       WHERE pa.property_id = ? AND pa.worker_id = ?`
    )
      .bind(property_id, worker_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Property assigned successfully',
        assignment,
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Property Assignments POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to create property assignment',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
