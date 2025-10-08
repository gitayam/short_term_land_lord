/**
 * Calendar Sync Endpoint
 * POST /api/calendar/sync
 * Manually trigger calendar sync for a property
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const { property_id } = await request.json();

    if (!property_id) {
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
      'SELECT id, name FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(property_id, user.userId)
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

    // Get all active calendars for this property
    const calendars = await env.DB.prepare(
      'SELECT id, platform_name, ical_url FROM property_calendar WHERE property_id = ? AND is_active = 1'
    )
      .bind(property_id)
      .all();

    if (!calendars.results || calendars.results.length === 0) {
      return new Response(
        JSON.stringify({
          success: true,
          message: 'No calendars configured for this property',
          synced: 0,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    let syncedCount = 0;
    let totalInserted = 0;
    let totalUpdated = 0;
    let totalDeleted = 0;
    let errors: string[] = [];

    // Sync each calendar
    for (const calendar of calendars.results) {
      try {
        // Skip if no iCal URL configured
        if (!calendar.ical_url) {
          errors.push(`${calendar.platform_name}: No iCal URL configured`);
          await env.DB.prepare(
            `UPDATE property_calendar
             SET sync_status = 'failed', sync_error = ?
             WHERE id = ?`
          )
            .bind('No iCal URL configured', calendar.id)
            .run();
          continue;
        }

        // Fetch and parse iCal data
        const { fetchICalData, parseICalData, syncCalendarEvents } = await import('../../utils/ical');

        const icalString = await fetchICalData(calendar.ical_url as string);
        const events = parseICalData(icalString, calendar.platform_name as string);

        // Sync events to database
        const stats = await syncCalendarEvents(
          env.DB,
          property_id,
          calendar.id as number,
          events,
          calendar.platform_name as string
        );

        totalInserted += stats.inserted;
        totalUpdated += stats.updated;
        totalDeleted += stats.deleted;

        // Update sync status to success
        await env.DB.prepare(
          `UPDATE property_calendar
           SET last_synced = datetime('now'), sync_status = 'success', sync_error = NULL
           WHERE id = ?`
        )
          .bind(calendar.id)
          .run();

        syncedCount++;

        // Invalidate cached calendar events
        await env.KV.delete(`calendar:events:${property_id}:all:all`);
      } catch (error: any) {
        console.error(`[Calendar Sync] Error syncing calendar ${calendar.id}:`, error);
        errors.push(`${calendar.platform_name}: ${error.message}`);

        // Update sync status to failed
        await env.DB.prepare(
          `UPDATE property_calendar
           SET sync_status = 'failed', sync_error = ?
           WHERE id = ?`
        )
          .bind(error.message, calendar.id)
          .run();
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: `Synced ${syncedCount} of ${calendars.results.length} calendars`,
        synced: syncedCount,
        total: calendars.results.length,
        stats: {
          inserted: totalInserted,
          updated: totalUpdated,
          deleted: totalDeleted,
        },
        errors: errors.length > 0 ? errors : undefined,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Calendar Sync] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to sync calendars',
        message: error.message,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
