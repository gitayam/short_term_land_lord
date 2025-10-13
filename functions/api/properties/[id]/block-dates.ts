/**
 * Block Dates API
 * POST /api/properties/[id]/block-dates - Block dates on property calendar
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const data = await request.json();

    const { start_date, end_date, reason } = data;

    if (!start_date || !end_date) {
      return new Response(
        JSON.stringify({ error: 'start_date and end_date are required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
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
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Create a "direct" calendar entry for blocked dates
    // First, ensure we have a "direct" calendar for this property
    let directCalendar = await env.DB.prepare(
      'SELECT id FROM property_calendar WHERE property_id = ? AND platform_name = ?'
    )
      .bind(propertyId, 'direct')
      .first();

    if (!directCalendar) {
      // Create direct calendar
      await env.DB.prepare(
        `INSERT INTO property_calendar (property_id, platform_name, ical_url, is_active)
         VALUES (?, 'direct', NULL, 1)`
      )
        .bind(propertyId)
        .run();

      directCalendar = await env.DB.prepare(
        'SELECT id FROM property_calendar WHERE property_id = ? AND platform_name = ?'
      )
        .bind(propertyId, 'direct')
        .first();
    }

    // Insert blocked event
    const title = reason || 'Blocked';
    const externalId = `blocked-${Date.now()}-${Math.random().toString(36).substring(7)}`;

    await env.DB.prepare(
      `INSERT INTO calendar_events
       (property_calendar_id, property_id, title, start_date, end_date, source, external_id, booking_status)
       VALUES (?, ?, ?, ?, ?, 'direct', ?, 'blocked')`
    )
      .bind(
        (directCalendar as any).id,
        propertyId,
        title,
        start_date,
        end_date,
        externalId
      )
      .run();

    // Get the created event
    const created = await env.DB.prepare(
      'SELECT * FROM calendar_events WHERE external_id = ?'
    )
      .bind(externalId)
      .first();

    // Invalidate cache
    await env.KV.delete(`calendar:events:${propertyId}:all:all`);

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Dates blocked successfully',
        event: created,
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Block Dates] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to block dates' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
