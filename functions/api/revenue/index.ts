/**
 * Revenue API - List and Create
 * GET  /api/revenue - List revenue with filters
 * POST /api/revenue - Create a new revenue entry
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// Revenue sources
const REVENUE_SOURCES = [
  'booking',
  'cleaning_fee',
  'pet_fee',
  'damage_deposit',
  'late_fee',
  'additional_services',
  'other',
];

// GET /api/revenue
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    // Query parameters
    const propertyId = url.searchParams.get('property_id');
    const source = url.searchParams.get('source');
    const status = url.searchParams.get('status');
    const startDate = url.searchParams.get('start_date');
    const endDate = url.searchParams.get('end_date');
    const limit = parseInt(url.searchParams.get('limit') || '100');

    // Build query
    let query = `
      SELECT
        r.id, r.property_id, r.source, r.description,
        r.amount, r.revenue_date, r.received_date,
        r.status, r.payment_method, r.booking_id,
        r.created_at, r.updated_at,
        p.name as property_name,
        p.address as property_address
      FROM revenue r
      LEFT JOIN property p ON r.property_id = p.id
      WHERE 1=1
    `;

    const params: any[] = [];

    // Filter by property ownership (admins see all)
    if (user.role !== 'admin') {
      query += ' AND p.owner_id = ?';
      params.push(user.userId);
    }

    // Apply filters
    if (propertyId) {
      query += ' AND r.property_id = ?';
      params.push(propertyId);
    }

    if (source) {
      query += ' AND r.source = ?';
      params.push(source);
    }

    if (status) {
      query += ' AND r.status = ?';
      params.push(status);
    }

    if (startDate) {
      query += ' AND r.revenue_date >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND r.revenue_date <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY r.revenue_date DESC, r.created_at DESC LIMIT ?';
    params.push(limit);

    const revenue = await env.DB.prepare(query).bind(...params).all();

    // Calculate summary statistics
    let totalAmount = 0;
    let receivedAmount = 0;
    let pendingAmount = 0;

    revenue.results?.forEach((rev: any) => {
      totalAmount += rev.amount || 0;
      if (rev.status === 'received') {
        receivedAmount += rev.amount || 0;
      } else if (rev.status === 'pending') {
        pendingAmount += rev.amount || 0;
      }
    });

    return new Response(
      JSON.stringify({
        success: true,
        revenue: revenue.results || [],
        count: revenue.results?.length || 0,
        summary: {
          total_amount: totalAmount,
          received_amount: receivedAmount,
          pending_amount: pendingAmount,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Revenue GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch revenue',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/revenue
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    // Validate required fields
    if (!data.property_id || !data.source || !data.description || !data.amount) {
      return new Response(
        JSON.stringify({
          error: 'Property ID, source, description, and amount are required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate source
    if (!REVENUE_SOURCES.includes(data.source)) {
      return new Response(
        JSON.stringify({
          error: 'Invalid source',
          valid_sources: REVENUE_SOURCES,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate amount
    const amount = parseFloat(data.amount);
    if (isNaN(amount) || amount <= 0) {
      return new Response(
        JSON.stringify({ error: 'Amount must be a positive number' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify property access
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(data.property_id)
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

    if (user.role !== 'admin' && property.owner_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Access denied to this property' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create revenue entry
    const result = await env.DB.prepare(
      `INSERT INTO revenue (
        property_id, source, description, amount,
        revenue_date, received_date, status,
        payment_method, booking_id, created_by_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        data.property_id,
        data.source,
        data.description,
        amount,
        data.revenue_date || new Date().toISOString().split('T')[0],
        data.received_date || null,
        data.status || 'pending',
        data.payment_method || null,
        data.booking_id || null,
        user.userId
      )
      .run();

    // Fetch created revenue
    const revenueEntry = await env.DB.prepare(
      `SELECT
        r.id, r.property_id, r.source, r.description,
        r.amount, r.revenue_date, r.received_date,
        r.status, r.payment_method, r.created_at,
        p.name as property_name
      FROM revenue r
      LEFT JOIN property p ON r.property_id = p.id
      WHERE r.id = ?`
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        revenue: revenueEntry,
        message: 'Revenue entry created successfully',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Revenue POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to create revenue entry',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
