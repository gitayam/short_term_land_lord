/**
 * Repair Requests API
 * GET  /api/repair-requests - List repair requests
 * POST /api/repair-requests - Create repair request
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';
import { notifyPropertyWorkers } from '../../utils/notifications';

interface RepairRequestRow {
  id: string;
  property_id: string;
  reported_by_id: string;
  title: string;
  description: string;
  location: string | null;
  severity: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'approved' | 'rejected' | 'converted';
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  converted_task_id: string | null;
  created_at: string;
  updated_at: string;
}

// GET /api/repair-requests
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);
    const propertyId = url.searchParams.get('property_id');
    const status = url.searchParams.get('status');

    let query = `
      SELECT
        rr.*,
        p.name as property_name,
        p.address as property_address,
        u.first_name || ' ' || u.last_name as reported_by_name,
        u.email as reported_by_email,
        rv.first_name || ' ' || rv.last_name as reviewed_by_name
      FROM repair_request rr
      JOIN property p ON rr.property_id = p.id
      JOIN users u ON rr.reported_by_id = u.id
      LEFT JOIN users rv ON rr.reviewed_by_id = rv.id
      WHERE 1=1
    `;

    const bindings: any[] = [];

    // Filter by property if specified
    if (propertyId) {
      query += ' AND rr.property_id = ?';
      bindings.push(propertyId);
    }

    // Filter by status if specified
    if (status) {
      query += ' AND rr.status = ?';
      bindings.push(status);
    }

    // Property owners can only see repair requests for their properties
    if (user.role === 'property_owner') {
      query += ' AND p.owner_id = ?';
      bindings.push(user.userId);
    }

    // Service staff can only see repair requests for their assigned properties
    if (user.role === 'service_staff') {
      query += ` AND rr.property_id IN (
        SELECT property_id FROM property_assignment WHERE worker_id = ?
      )`;
      bindings.push(user.userId);
    }

    query += ' ORDER BY rr.created_at DESC';

    const stmt = env.DB.prepare(query);
    const requests = await (bindings.length > 0
      ? stmt.bind(...bindings)
      : stmt
    ).all<RepairRequestRow>();

    // Get images for all requests
    const requestsWithImages = await Promise.all(
      (requests.results || []).map(async (request) => {
        const images = await env.DB.prepare(
          'SELECT * FROM repair_request_image WHERE repair_request_id = ? ORDER BY uploaded_at ASC'
        )
          .bind(request.id)
          .all();

        return {
          ...request,
          images: images.results || [],
        };
      })
    );

    return new Response(
      JSON.stringify({
        success: true,
        requests: requestsWithImages,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Repair Requests GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch repair requests',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/repair-requests
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();
    const { property_id, title, description, location, severity = 'medium', image_urls } = data;

    if (!property_id || !title || !description) {
      return new Response(
        JSON.stringify({ error: 'property_id, title, and description are required' }),
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

    // Check access: owner, assigned worker, or admin
    const hasAccess =
      user.role === 'admin' ||
      user.role === 'property_manager' ||
      (property as any).owner_id === user.userId;

    if (!hasAccess && user.role === 'service_staff') {
      // Check if worker is assigned to this property
      const assignment = await env.DB.prepare(
        'SELECT id FROM property_assignment WHERE property_id = ? AND worker_id = ?'
      )
        .bind(property_id, user.userId)
        .first();

      if (!assignment) {
        return new Response(
          JSON.stringify({ error: 'Unauthorized - No access to this property' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Create repair request
    await env.DB.prepare(
      `INSERT INTO repair_request (property_id, reported_by_id, title, description, location, severity)
       VALUES (?, ?, ?, ?, ?, ?)`
    )
      .bind(
        property_id,
        user.userId,
        title,
        description,
        location || null,
        severity
      )
      .run();

    // Get the created request
    const created = await env.DB.prepare(
      `SELECT * FROM repair_request
       WHERE property_id = ? AND reported_by_id = ? AND title = ?
       ORDER BY created_at DESC LIMIT 1`
    )
      .bind(property_id, user.userId, title)
      .first<RepairRequestRow>();

    // Add images if provided
    if (image_urls && Array.isArray(image_urls) && image_urls.length > 0) {
      for (const imageUrl of image_urls) {
        await env.DB.prepare(
          'INSERT INTO repair_request_image (repair_request_id, image_url) VALUES (?, ?)'
        )
          .bind(created!.id, imageUrl)
          .run();
      }
    }

    // Send notifications to assigned workers
    await notifyPropertyWorkers(
      env,
      parseInt(property_id),
      'repair_requested',
      'New Repair Request',
      `New ${severity} priority repair: ${title}`,
      `/app/repair-requests/${created!.id}`,
      parseInt(created!.id),
      'repair_request'
    );

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Repair request created successfully',
        request: created,
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Repair Requests POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to create repair request',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
