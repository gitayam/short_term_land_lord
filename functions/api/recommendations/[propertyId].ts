/**
 * Local Recommendations API
 * GET    /api/recommendations/[propertyId] - List recommendations for property
 * POST   /api/recommendations/[propertyId] - Create recommendation
 * PUT    /api/recommendations/[propertyId]/[id] - Update recommendation
 * DELETE /api/recommendations/[propertyId]/[id] - Delete recommendation
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

const CATEGORIES = [
  'restaurant',
  'attraction',
  'grocery',
  'pharmacy',
  'hospital',
  'shopping',
  'entertainment',
  'transportation',
  'gas_station',
  'bank',
  'other',
];

// GET /api/recommendations/[propertyId]
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

    // Fetch recommendations
    const recommendations = await env.DB.prepare(
      `SELECT * FROM local_recommendation
       WHERE property_id = ?
       ORDER BY is_favorite DESC, category ASC, display_order ASC`
    )
      .bind(propertyId)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        recommendations: recommendations.results || [],
        count: recommendations.results?.length || 0,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Recommendations GET] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to fetch recommendations' }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};

// POST /api/recommendations/[propertyId]
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.propertyId as string;
    const data = await request.json();

    // Validate required fields
    if (!data.name || !data.category) {
      return new Response(
        JSON.stringify({ error: 'Name and category are required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Validate category
    if (!CATEGORIES.includes(data.category)) {
      return new Response(
        JSON.stringify({
          error: 'Invalid category',
          valid_categories: CATEGORIES,
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

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

    // Create recommendation
    const result = await env.DB.prepare(
      `INSERT INTO local_recommendation (
        property_id, name, category, description, phone, website, address,
        distance_miles, price_range, rating, notes,
        is_favorite, is_visible, display_order
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        propertyId,
        data.name,
        data.category,
        data.description || null,
        data.phone || null,
        data.website || null,
        data.address || null,
        data.distance_miles || null,
        data.price_range || null,
        data.rating || null,
        data.notes || null,
        data.is_favorite ? 1 : 0,
        data.is_visible !== undefined ? (data.is_visible ? 1 : 0) : 1,
        data.display_order || 0
      )
      .run();

    // Fetch created recommendation
    const recommendation = await env.DB.prepare(
      'SELECT * FROM local_recommendation WHERE id = ?'
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        recommendation,
        message: 'Recommendation created successfully',
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Recommendations POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to create recommendation',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
