/**
 * Property iCal Feed Generator
 * GET /api/properties/[id]/calendar.ics
 *
 * Generates an iCal feed that can be imported into Airbnb, VRBO, etc.
 * This enables outbound sync (our system -> external platforms)
 */

import { Env } from '../../../_middleware';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, env } = context;

  try {
    const propertyId = params.id as string;

    // Get property details
    const property = await env.DB.prepare(
      'SELECT id, name, address FROM property WHERE id = ?'
    )
      .bind(propertyId)
      .first();

    if (!property) {
      return new Response('Property not found', { status: 404 });
    }

    // Get all calendar events for this property
    const events = await env.DB.prepare(
      `SELECT
        ce.id, ce.title, ce.start_date, ce.end_date,
        ce.guest_name, ce.guest_count, ce.source, ce.external_id,
        pc.platform_name
       FROM calendar_events ce
       LEFT JOIN property_calendar pc ON ce.property_calendar_id = pc.id
       WHERE ce.property_id = ?
       ORDER BY ce.start_date ASC`
    )
      .bind(propertyId)
      .all();

    // Generate iCal content
    const icalContent = generateICalFeed(
      property as any,
      events.results as any[]
    );

    return new Response(icalContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/calendar; charset=utf-8',
        'Content-Disposition': `attachment; filename="property-${propertyId}.ics"`,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    });
  } catch (error: any) {
    console.error('[iCal Feed] Error:', error);
    return new Response(
      `Error generating iCal feed: ${error.message}`,
      { status: 500 }
    );
  }
};

/**
 * Generate iCal feed content
 */
function generateICalFeed(
  property: { id: number; name: string; address: string },
  events: any[]
): string {
  const now = new Date();
  const timestamp = formatICalDate(now);

  let ical = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Short Term Land Lord//Property Calendar//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    `X-WR-CALNAME:${escapeICalText(property.name || 'Property')}`,
    `X-WR-CALDESC:Bookings for ${escapeICalText(property.name || 'Property')}`,
    'X-WR-TIMEZONE:UTC',
  ].join('\r\n');

  // Add events
  for (const event of events) {
    const uid = event.external_id || `event-${event.id}@short-term-landlord.pages.dev`;
    const summary = escapeICalText(event.title || 'Reserved');
    const startDate = formatICalDate(new Date(event.start_date + 'T00:00:00Z'));
    const endDate = formatICalDate(new Date(event.end_date + 'T00:00:00Z'));

    // Build description
    let description = 'Property Blocked';
    if (event.guest_name) {
      description = `Guest: ${event.guest_name}`;
    }
    if (event.guest_count) {
      description += `\nGuests: ${event.guest_count}`;
    }
    if (event.platform_name) {
      description += `\nSource: ${event.platform_name}`;
    }
    description = escapeICalText(description);

    ical += '\r\n' + [
      'BEGIN:VEVENT',
      `UID:${uid}`,
      `DTSTAMP:${timestamp}`,
      `DTSTART;VALUE=DATE:${startDate.split('T')[0].replace(/-/g, '')}`,
      `DTEND;VALUE=DATE:${endDate.split('T')[0].replace(/-/g, '')}`,
      `SUMMARY:${summary}`,
      `DESCRIPTION:${description}`,
      `LOCATION:${escapeICalText(property.address || '')}`,
      'STATUS:CONFIRMED',
      'TRANSP:OPAQUE',
      'END:VEVENT',
    ].join('\r\n');
  }

  ical += '\r\nEND:VCALENDAR\r\n';

  return ical;
}

/**
 * Format date for iCal (YYYYMMDDTHHMMSSZ)
 */
function formatICalDate(date: Date): string {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hours = String(date.getUTCHours()).padStart(2, '0');
  const minutes = String(date.getUTCMinutes()).padStart(2, '0');
  const seconds = String(date.getUTCSeconds()).padStart(2, '0');

  return `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
}

/**
 * Escape special characters for iCal text fields
 */
function escapeICalText(text: string): string {
  return text
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '');
}
