/**
 * Service Prices API
 * GET  /api/service-prices - List service prices
 * POST /api/service-prices - Create service price
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

interface ServicePrice {
  id: string;
  service_name: string;
  service_type: string | null;
  unit_price: number;
  unit: string;
  description: string | null;
  is_active: number;
  created_at: string;
  updated_at: string;
}

// GET /api/service-prices
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);
    const active_only = url.searchParams.get('active_only') === 'true';

    let query = 'SELECT * FROM service_price WHERE 1=1';
    const bindings: any[] = [];

    if (active_only) {
      query += ' AND is_active = 1';
    }

    query += ' ORDER BY service_name ASC';

    const stmt = env.DB.prepare(query);
    const prices = await (bindings.length > 0
      ? stmt.bind(...bindings)
      : stmt
    ).all<ServicePrice>();

    return new Response(
      JSON.stringify({
        success: true,
        prices: prices.results || [],
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Service Prices GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch service prices',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/service-prices
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only admins and property_managers can create service prices
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
    const { service_name, service_type, unit_price, unit, description, is_active = 1 } = data;

    if (!service_name || unit_price == null) {
      return new Response(
        JSON.stringify({ error: 'service_name and unit_price are required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create service price
    await env.DB.prepare(
      `INSERT INTO service_price (service_name, service_type, unit_price, unit, description, is_active)
       VALUES (?, ?, ?, ?, ?, ?)`
    )
      .bind(
        service_name,
        service_type || null,
        unit_price,
        unit || 'per service',
        description || null,
        is_active
      )
      .run();

    // Get the created service price
    const created = await env.DB.prepare(
      'SELECT * FROM service_price WHERE service_name = ? ORDER BY created_at DESC LIMIT 1'
    )
      .bind(service_name)
      .first<ServicePrice>();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Service price created successfully',
        price: created,
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Service Prices POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to create service price',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
