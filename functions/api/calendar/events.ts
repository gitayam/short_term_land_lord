/**
 * Calendar Events Endpoint
 * GET /api/calendar/events?property_id=X&start_date=Y&end_date=Z
 * Retrieves calendar events for a property within a date range
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    const propertyId = url.searchParams.get('property_id');
    const startDate = url.searchParams.get('start_date');
    const endDate = url.searchParams.get('end_date');

    if (!propertyId) {
      return new Response(
        JSON.stringify({ error: 'property_id is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify property ownership
    const property = await env.DB.prepare(
      'SELECT id FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(propertyId, user.userId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found or access denied' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Build query
    let query = `
      SELECT
        ce.id, ce.title, ce.start_date, ce.end_date, ce.source,
        ce.guest_name, ce.guest_count, ce.booking_amount, ce.booking_status,
        pc.platform_name
      FROM calendar_events ce
      LEFT JOIN property_calendar pc ON ce.property_calendar_id = pc.id
      WHERE ce.property_id = ?
    `;

    const params: any[] = [propertyId];

    if (startDate) {
      query += ' AND ce.end_date >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND ce.start_date <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY ce.start_date ASC';

    const events = await env.DB.prepare(query).bind(...params).all();

    // Try to get from cache first
    const cacheKey = `calendar:events:${propertyId}:${startDate || 'all'}:${endDate || 'all'}`;
    const cached = await env.KV.get(cacheKey, { type: 'json' });

    if (cached && !startDate && !endDate) {
      // Only use cache for full property queries
      return new Response(
        JSON.stringify({
          success: true,
          events: cached,
          count: (cached as any[]).length,
          cached: true,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Cache the results (5 minutes TTL)
    if (!startDate && !endDate) {
      await env.KV.put(cacheKey, JSON.stringify(events.results), {
        expirationTtl: 300,
      });
    }

    return new Response(
      JSON.stringify({
        success: true,
        events: events.results || [],
        count: events.results?.length || 0,
        cached: false,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Calendar Events] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to fetch calendar events',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
