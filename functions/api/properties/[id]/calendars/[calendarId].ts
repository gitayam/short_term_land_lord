/**
 * Property Calendar Detail API
 * PUT    /api/properties/[id]/calendars/[calendarId] - Update calendar
 * DELETE /api/properties/[id]/calendars/[calendarId] - Delete calendar
 * POST   /api/properties/[id]/calendars/[calendarId]/sync - Manual sync
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

// PUT /api/properties/[id]/calendars/[calendarId]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const calendarId = params.calendarId as string;
    const data = await request.json();

    const { platform_name, ical_url, is_active } = data;

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

    // Verify calendar exists
    const calendar = await env.DB.prepare(
      'SELECT id FROM property_calendar WHERE id = ? AND property_id = ?'
    )
      .bind(calendarId, propertyId)
      .first();

    if (!calendar) {
      return new Response(
        JSON.stringify({ error: 'Calendar not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Validate iCal URL if provided
    if (ical_url) {
      try {
        new URL(ical_url);
      } catch {
        return new Response(
          JSON.stringify({ error: 'Invalid iCal URL format' }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // Update calendar
    await env.DB.prepare(
      `UPDATE property_calendar
       SET platform_name = COALESCE(?, platform_name),
           ical_url = COALESCE(?, ical_url),
           is_active = COALESCE(?, is_active),
           updated_at = datetime('now')
       WHERE id = ?`
    )
      .bind(platform_name || null, ical_url || null, is_active !== undefined ? is_active : null, calendarId)
      .run();

    // Get updated calendar
    const updated = await env.DB.prepare(
      'SELECT * FROM property_calendar WHERE id = ?'
    )
      .bind(calendarId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Calendar updated successfully',
        calendar: updated,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Calendar PUT] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to update calendar' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/properties/[id]/calendars/[calendarId]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const calendarId = params.calendarId as string;

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

    // Verify calendar exists
    const calendar = await env.DB.prepare(
      'SELECT id FROM property_calendar WHERE id = ? AND property_id = ?'
    )
      .bind(calendarId, propertyId)
      .first();

    if (!calendar) {
      return new Response(
        JSON.stringify({ error: 'Calendar not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Delete associated calendar events
    await env.DB.prepare(
      'DELETE FROM calendar_events WHERE property_calendar_id = ?'
    )
      .bind(calendarId)
      .run();

    // Delete calendar
    await env.DB.prepare(
      'DELETE FROM property_calendar WHERE id = ?'
    )
      .bind(calendarId)
      .run();

    // Invalidate cache
    await env.KV.delete(`calendar:events:${propertyId}:all:all`);

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Calendar deleted successfully',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Calendar DELETE] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to delete calendar' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
