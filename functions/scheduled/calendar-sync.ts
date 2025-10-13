/**
 * Scheduled Calendar Sync
 * Automatically syncs all active property calendars every 2 hours
 * Triggered by Cloudflare Cron
 */

import { Env } from '../_middleware';

export const onRequest: PagesFunction<Env> = async (context) => {
  const { env } = context;

  try {
    console.log('[Calendar Sync] Starting scheduled sync...');

    // Get all active calendars
    const calendars = await env.DB.prepare(
      `SELECT pc.id, pc.property_id, pc.platform_name, pc.ical_url, p.name as property_name
       FROM property_calendar pc
       JOIN property p ON pc.property_id = p.id
       WHERE pc.is_active = 1 AND pc.ical_url IS NOT NULL`
    ).all();

    if (!calendars.results || calendars.results.length === 0) {
      console.log('[Calendar Sync] No active calendars to sync');
      return new Response(
        JSON.stringify({ success: true, message: 'No calendars to sync', synced: 0 }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }

    let syncedCount = 0;
    let totalInserted = 0;
    let totalUpdated = 0;
    let totalDeleted = 0;
    const errors: string[] = [];

    // Sync each calendar
    for (const calendar of calendars.results) {
      try {
        console.log(`[Calendar Sync] Syncing calendar ${calendar.id} (${calendar.platform_name} for ${calendar.property_name})`);

        // Fetch and parse iCal data
        const { fetchICalData, parseICalData, syncCalendarEvents } = await import('../utils/ical');

        const icalString = await fetchICalData(calendar.ical_url as string);
        const events = parseICalData(icalString, calendar.platform_name as string);

        // Sync events to database
        const stats = await syncCalendarEvents(
          env.DB,
          calendar.property_id as number,
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

        // Invalidate cached calendar events
        await env.KV.delete(`calendar:events:${calendar.property_id}:all:all`);

        syncedCount++;
        console.log(`[Calendar Sync] Successfully synced calendar ${calendar.id}: +${stats.inserted} ~${stats.updated} -${stats.deleted}`);
      } catch (error: any) {
        console.error(`[Calendar Sync] Error syncing calendar ${calendar.id}:`, error);
        errors.push(`${calendar.platform_name} (${calendar.property_name}): ${error.message}`);

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

    const result = {
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
      timestamp: new Date().toISOString(),
    };

    console.log('[Calendar Sync] Completed:', result);

    return new Response(
      JSON.stringify(result),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Calendar Sync] Fatal error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: 'Failed to sync calendars',
        message: error.message,
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
