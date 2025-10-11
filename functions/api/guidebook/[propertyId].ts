/**
 * Property Guidebook API
 * GET    /api/guidebook/[propertyId] - Get guidebook for property
 * POST   /api/guidebook/[propertyId] - Create guidebook for property
 * PUT    /api/guidebook/[propertyId] - Update guidebook
 * DELETE /api/guidebook/[propertyId] - Delete guidebook
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/guidebook/[propertyId]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.propertyId as string;

    // Verify property access
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(propertyId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (user.role !== 'admin' && property.owner_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Fetch guidebook
    const guidebook = await env.DB.prepare(
      `SELECT * FROM property_guidebook WHERE property_id = ?`
    )
      .bind(propertyId)
      .first();

    if (!guidebook) {
      return new Response(
        JSON.stringify({
          success: true,
          guidebook: null,
          message: 'No guidebook created yet'
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Fetch sections
    const sections = await env.DB.prepare(
      `SELECT * FROM guidebook_section
       WHERE guidebook_id = ?
       ORDER BY display_order ASC`
    )
      .bind(guidebook.id)
      .all();

    // Fetch recommendations
    const recommendations = await env.DB.prepare(
      `SELECT * FROM local_recommendation
       WHERE property_id = ? AND is_visible = 1
       ORDER BY is_favorite DESC, display_order ASC`
    )
      .bind(propertyId)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        guidebook: {
          ...guidebook,
          sections: sections.results || [],
          recommendations: recommendations.results || [],
        },
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Guidebook GET] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to fetch guidebook' }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};

// POST /api/guidebook/[propertyId]
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.propertyId as string;
    const data = await request.json();

    // Verify property access
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(propertyId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (user.role !== 'admin' && property.owner_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check if guidebook already exists
    const existing = await env.DB.prepare(
      'SELECT id FROM property_guidebook WHERE property_id = ?'
    )
      .bind(propertyId)
      .first();

    if (existing) {
      return new Response(
        JSON.stringify({
          error: 'Guidebook already exists for this property',
          suggestion: 'Use PUT to update the guidebook'
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Create guidebook
    const result = await env.DB.prepare(
      `INSERT INTO property_guidebook (
        property_id, welcome_message, checkin_time, checkout_time,
        checkin_instructions, checkout_instructions,
        wifi_network, wifi_password,
        emergency_contact, emergency_phone, host_phone, host_email,
        parking_info, parking_instructions,
        house_rules, quiet_hours, max_guests,
        smoking_allowed, pets_allowed, parties_allowed,
        is_published
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        propertyId,
        data.welcome_message || null,
        data.checkin_time || '3:00 PM',
        data.checkout_time || '11:00 AM',
        data.checkin_instructions || null,
        data.checkout_instructions || null,
        data.wifi_network || null,
        data.wifi_password || null,
        data.emergency_contact || null,
        data.emergency_phone || null,
        data.host_phone || null,
        data.host_email || null,
        data.parking_info || null,
        data.parking_instructions || null,
        data.house_rules || null,
        data.quiet_hours || null,
        data.max_guests || null,
        data.smoking_allowed ? 1 : 0,
        data.pets_allowed ? 1 : 0,
        data.parties_allowed ? 1 : 0,
        data.is_published ? 1 : 0
      )
      .run();

    // Fetch created guidebook
    const guidebook = await env.DB.prepare(
      'SELECT * FROM property_guidebook WHERE id = ?'
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        guidebook,
        message: 'Guidebook created successfully',
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Guidebook POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to create guidebook',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};

// PUT /api/guidebook/[propertyId]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.propertyId as string;
    const data = await request.json();

    // Verify property access
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(propertyId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (user.role !== 'admin' && property.owner_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Build update query dynamically
    const updates: string[] = [];
    const params: any[] = [];

    const fields = [
      'welcome_message', 'checkin_time', 'checkout_time',
      'checkin_instructions', 'checkout_instructions',
      'wifi_network', 'wifi_password',
      'emergency_contact', 'emergency_phone', 'host_phone', 'host_email',
      'parking_info', 'parking_instructions',
      'house_rules', 'quiet_hours', 'max_guests',
    ];

    fields.forEach(field => {
      if (data[field] !== undefined) {
        updates.push(`${field} = ?`);
        params.push(data[field]);
      }
    });

    const boolFields = ['smoking_allowed', 'pets_allowed', 'parties_allowed', 'is_published'];
    boolFields.forEach(field => {
      if (data[field] !== undefined) {
        updates.push(`${field} = ?`);
        params.push(data[field] ? 1 : 0);
      }
    });

    if (updates.length === 0) {
      return new Response(
        JSON.stringify({ error: 'No fields to update' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    updates.push('last_updated = datetime("now")');
    params.push(propertyId);

    await env.DB.prepare(
      `UPDATE property_guidebook SET ${updates.join(', ')} WHERE property_id = ?`
    )
      .bind(...params)
      .run();

    // Fetch updated guidebook
    const guidebook = await env.DB.prepare(
      'SELECT * FROM property_guidebook WHERE property_id = ?'
    )
      .bind(propertyId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        guidebook,
        message: 'Guidebook updated successfully',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Guidebook PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to update guidebook',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};

// DELETE /api/guidebook/[propertyId]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.propertyId as string;

    // Verify property access
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(propertyId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (user.role !== 'admin' && property.owner_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Delete guidebook (cascades to sections)
    await env.DB.prepare('DELETE FROM property_guidebook WHERE property_id = ?')
      .bind(propertyId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Guidebook deleted successfully',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Guidebook DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to delete guidebook',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
