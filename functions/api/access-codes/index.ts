/**
 * Guest Access Codes API
 * GET  /api/access-codes - List access codes
 * POST /api/access-codes - Create new access code
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// Generate random access code
function generateAccessCode(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // Removed similar looking chars
  let code = '';
  for (let i = 0; i < 8; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
    if (i === 3) code += '-'; // Format: XXXX-XXXX
  }
  return code;
}

// GET /api/access-codes
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    const propertyId = url.searchParams.get('property_id');
    const status = url.searchParams.get('status'); // active, expired, future, disabled

    let query = `
      SELECT
        gac.id, gac.access_code, gac.guest_name, gac.guest_email,
        gac.property_id, gac.booking_id,
        gac.valid_from, gac.valid_until,
        gac.access_count, gac.last_accessed, gac.is_active,
        gac.created_at,
        p.name as property_name,
        p.address as property_address
      FROM guest_access_code gac
      LEFT JOIN property p ON gac.property_id = p.id
      WHERE 1=1
    `;

    const params: any[] = [];

    // Filter by property ownership
    if (user.role !== 'admin') {
      query += ' AND p.owner_id = ?';
      params.push(user.userId);
    }

    if (propertyId) {
      query += ' AND gac.property_id = ?';
      params.push(propertyId);
    }

    // Status filter
    const now = new Date().toISOString().split('T')[0];
    if (status === 'active') {
      query += ` AND gac.is_active = 1 AND gac.valid_from <= ? AND gac.valid_until >= ?`;
      params.push(now, now);
    } else if (status === 'expired') {
      query += ` AND gac.valid_until < ?`;
      params.push(now);
    } else if (status === 'future') {
      query += ` AND gac.valid_from > ?`;
      params.push(now);
    } else if (status === 'disabled') {
      query += ' AND gac.is_active = 0';
    }

    query += ' ORDER BY gac.valid_from DESC';

    const codes = await env.DB.prepare(query).bind(...params).all();

    return new Response(
      JSON.stringify({
        success: true,
        codes: codes.results || [],
        count: codes.results?.length || 0,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Access Codes GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch access codes',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/access-codes
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    // Validate required fields
    if (!data.property_id || !data.guest_name || !data.valid_from || !data.valid_until) {
      return new Response(
        JSON.stringify({
          error: 'Property ID, guest name, valid_from, and valid_until are required',
        }),
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

    // Generate unique access code
    let accessCode = data.access_code || generateAccessCode();
    let attempts = 0;
    while (attempts < 10) {
      const existing = await env.DB.prepare(
        'SELECT id FROM guest_access_code WHERE access_code = ?'
      )
        .bind(accessCode)
        .first();

      if (!existing) break;
      accessCode = generateAccessCode();
      attempts++;
    }

    if (attempts === 10) {
      return new Response(
        JSON.stringify({ error: 'Failed to generate unique access code' }),
        {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create access code
    const result = await env.DB.prepare(
      `INSERT INTO guest_access_code (
        property_id, booking_id, access_code, guest_name, guest_email, guest_phone,
        valid_from, valid_until, is_active, notes, created_by_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        data.property_id,
        data.booking_id || null,
        accessCode,
        data.guest_name,
        data.guest_email || null,
        data.guest_phone || null,
        data.valid_from,
        data.valid_until,
        data.is_active !== undefined ? (data.is_active ? 1 : 0) : 1,
        data.notes || null,
        user.userId
      )
      .run();

    // Fetch created code
    const code = await env.DB.prepare(
      `SELECT
        gac.id, gac.access_code, gac.guest_name, gac.guest_email,
        gac.property_id, gac.valid_from, gac.valid_until,
        gac.is_active, gac.created_at,
        p.name as property_name
      FROM guest_access_code gac
      LEFT JOIN property p ON gac.property_id = p.id
      WHERE gac.id = ?`
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        code,
        message: 'Access code created successfully',
        portal_url: `${env.FRONTEND_URL || 'https://short-term-landlord.pages.dev'}/guest/${accessCode}`,
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Access Codes POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to create access code',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
