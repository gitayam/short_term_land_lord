/**
 * Property Calendars API
 * GET  /api/properties/[id]/calendars - List all calendars for a property
 * POST /api/properties/[id]/calendars - Add a new calendar
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

// GET /api/properties/[id]/calendars
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;

    // Verify property ownership
    const property = await env.DB.prepare(
      'SELECT id, name FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(propertyId, user.userId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get all calendars for this property
    const calendars = await env.DB.prepare(
      `SELECT
        id, property_id, platform_name, ical_url, is_active,
        last_synced, sync_status, sync_error, created_at, updated_at
       FROM property_calendar
       WHERE property_id = ?
       ORDER BY created_at DESC`
    )
      .bind(propertyId)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        calendars: calendars.results || [],
        count: calendars.results?.length || 0,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Calendars GET] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to fetch calendars' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/properties/[id]/calendars
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const data = await request.json();

    const { platform_name, ical_url } = data;

    if (!platform_name || !ical_url) {
      return new Response(
        JSON.stringify({ error: 'platform_name and ical_url are required' }),
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

    // Validate iCal URL format
    try {
      new URL(ical_url);
    } catch {
      return new Response(
        JSON.stringify({ error: 'Invalid iCal URL format' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check if calendar already exists for this platform
    const existing = await env.DB.prepare(
      'SELECT id FROM property_calendar WHERE property_id = ? AND platform_name = ?'
    )
      .bind(propertyId, platform_name)
      .first();

    if (existing) {
      return new Response(
        JSON.stringify({ error: `Calendar for ${platform_name} already exists` }),
        { status: 409, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Insert new calendar
    await env.DB.prepare(
      `INSERT INTO property_calendar (property_id, platform_name, ical_url, is_active)
       VALUES (?, ?, ?, 1)`
    )
      .bind(propertyId, platform_name, ical_url)
      .run();

    // Get the created calendar
    const created = await env.DB.prepare(
      'SELECT * FROM property_calendar WHERE property_id = ? AND platform_name = ?'
    )
      .bind(propertyId, platform_name)
      .first();

    // Trigger initial sync in background
    try {
      const { fetchICalData, parseICalData, syncCalendarEvents } = await import('../../../../utils/ical');
      const icalString = await fetchICalData(ical_url);
      const events = parseICalData(icalString, platform_name);
      await syncCalendarEvents(env.DB, parseInt(propertyId), (created as any).id, events, platform_name);

      // Update sync status
      await env.DB.prepare(
        `UPDATE property_calendar
         SET last_synced = datetime('now'), sync_status = 'success'
         WHERE id = ?`
      )
        .bind((created as any).id)
        .run();
    } catch (syncError: any) {
      console.error('[Calendar Sync] Initial sync failed:', syncError);
      // Don't fail the calendar creation, just mark sync as failed
      await env.DB.prepare(
        `UPDATE property_calendar
         SET sync_status = 'failed', sync_error = ?
         WHERE id = ?`
      )
        .bind(syncError.message, (created as any).id)
        .run();
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Calendar added successfully',
        calendar: created,
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Calendars POST] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to add calendar' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
