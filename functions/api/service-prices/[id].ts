/**
 * Service Price Detail API
 * GET    /api/service-prices/[id] - Get service price
 * PUT    /api/service-prices/[id] - Update service price
 * DELETE /api/service-prices/[id] - Deactivate service price
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/service-prices/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const priceId = params.id as string;

    const price = await env.DB.prepare('SELECT * FROM service_price WHERE id = ?')
      .bind(priceId)
      .first();

    if (!price) {
      return new Response(
        JSON.stringify({ error: 'Service price not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    return new Response(
      JSON.stringify({
        success: true,
        price,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Service Price GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch service price',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/service-prices/[id]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const priceId = params.id as string;
    const data = await request.json();

    // Only admins and property_managers can update
    if (user.role !== 'admin' && user.role !== 'property_manager') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Admin or Property Manager access required' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify service price exists
    const price = await env.DB.prepare('SELECT id FROM service_price WHERE id = ?')
      .bind(priceId)
      .first();

    if (!price) {
      return new Response(
        JSON.stringify({ error: 'Service price not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Update service price
    await env.DB.prepare(
      `UPDATE service_price SET
        service_name = COALESCE(?, service_name),
        service_type = COALESCE(?, service_type),
        unit_price = COALESCE(?, unit_price),
        unit = COALESCE(?, unit),
        description = COALESCE(?, description),
        is_active = COALESCE(?, is_active),
        updated_at = datetime('now')
       WHERE id = ?`
    )
      .bind(
        data.service_name || null,
        data.service_type || null,
        data.unit_price != null ? data.unit_price : null,
        data.unit || null,
        data.description || null,
        data.is_active !== undefined ? data.is_active : null,
        priceId
      )
      .run();

    // Get updated price
    const updated = await env.DB.prepare('SELECT * FROM service_price WHERE id = ?')
      .bind(priceId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        price: updated,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Service Price PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to update service price',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/service-prices/[id] - Soft delete (deactivate)
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const priceId = params.id as string;

    // Only admins and property_managers can delete
    if (user.role !== 'admin' && user.role !== 'property_manager') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Admin or Property Manager access required' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify service price exists
    const price = await env.DB.prepare('SELECT id FROM service_price WHERE id = ?')
      .bind(priceId)
      .first();

    if (!price) {
      return new Response(
        JSON.stringify({ error: 'Service price not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Deactivate instead of delete (soft delete)
    await env.DB.prepare(
      'UPDATE service_price SET is_active = 0, updated_at = datetime(\'now\') WHERE id = ?'
    )
      .bind(priceId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Service price deactivated successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Service Price DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to deactivate service price',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
