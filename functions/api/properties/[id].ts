/**
 * Property Detail API
 * GET    /api/properties/[id] - Get single property
 * PUT    /api/properties/[id] - Update property
 * DELETE /api/properties/[id] - Delete property
 */

import { Env } from '../../_middleware';

// Helper to get user from session
async function getUserFromRequest(request: Request, env: Env): Promise<any> {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Unauthorized');
  }

  const token = authHeader.substring(7);
  let sessionData = await env.KV.get(`session:${token}`, { type: 'json' });

  if (!sessionData) {
    const session = await env.DB.prepare(
      'SELECT user_data FROM session_cache WHERE session_token = ? AND datetime(expires_at) > datetime("now")'
    )
      .bind(token)
      .first();

    if (session) {
      sessionData = JSON.parse(session.user_data as string);
    }
  }

  if (!sessionData) {
    throw new Error('Session expired');
  }

  return sessionData;
}

// GET /api/properties/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await getUserFromRequest(request, env);
    const propertyId = params.id as string;

    const property = await env.DB.prepare(
      'SELECT * FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(propertyId, user.userId)
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

    return new Response(
      JSON.stringify({
        success: true,
        property,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Property GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch property',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/properties/[id]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await getUserFromRequest(request, env);
    const propertyId = params.id as string;
    const data = await request.json();

    // Verify ownership
    const property = await env.DB.prepare(
      'SELECT id FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(propertyId, user.userId)
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

    // Update property
    await env.DB.prepare(
      `UPDATE property SET
        name = COALESCE(?, name),
        description = COALESCE(?, description),
        property_type = COALESCE(?, property_type),
        city = COALESCE(?, city),
        state = COALESCE(?, state),
        bedrooms = COALESCE(?, bedrooms),
        bathrooms = COALESCE(?, bathrooms),
        updated_at = datetime('now')
       WHERE id = ?`
    )
      .bind(
        data.name || null,
        data.description || null,
        data.property_type || null,
        data.city || null,
        data.state || null,
        data.bedrooms || null,
        data.bathrooms || null,
        propertyId
      )
      .run();

    // Get updated property
    const updated = await env.DB.prepare('SELECT * FROM property WHERE id = ?')
      .bind(propertyId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        property: updated,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Property PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to update property',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/properties/[id]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await getUserFromRequest(request, env);
    const propertyId = params.id as string;

    // Verify ownership
    const property = await env.DB.prepare(
      'SELECT id FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(propertyId, user.userId)
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

    // Delete property
    await env.DB.prepare('DELETE FROM property WHERE id = ?').bind(propertyId).run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Property deleted successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Property DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to delete property',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
