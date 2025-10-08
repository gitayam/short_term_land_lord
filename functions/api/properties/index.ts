/**
 * Properties API - List and Create
 * GET  /api/properties - List all properties for authenticated user
 * POST /api/properties - Create a new property
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/properties
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Get properties for this user
    const properties = await env.DB.prepare(
      `SELECT
        id, name, address, description, property_type, status,
        city, state, zip_code, bedrooms, bathrooms,
        created_at, updated_at
       FROM property
       WHERE owner_id = ?
       ORDER BY created_at DESC`
    )
      .bind(user.userId)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        properties: properties.results || [],
        count: properties.results?.length || 0,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Properties GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch properties',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/properties
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    // Validate required fields
    if (!data.address) {
      return new Response(
        JSON.stringify({ error: 'Address is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Insert new property
    const result = await env.DB.prepare(
      `INSERT INTO property (
        owner_id, name, address, description, property_type,
        street_address, city, state, zip_code, bedrooms, bathrooms
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        user.userId,
        data.name || null,
        data.address,
        data.description || null,
        data.property_type || 'house',
        data.street_address || null,
        data.city || null,
        data.state || null,
        data.zip_code || null,
        data.bedrooms || null,
        data.bathrooms || null
      )
      .run();

    // Get the created property
    const property = await env.DB.prepare(
      'SELECT * FROM property WHERE id = ?'
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        property,
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Properties POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to create property',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
