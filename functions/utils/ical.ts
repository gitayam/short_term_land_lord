/**
 * iCal Utilities
 * Fetch and parse iCalendar feeds from booking platforms
 */

import ICAL from 'ical.js';

export interface CalendarEvent {
  external_id: string;
  title: string;
  start_date: string; // ISO 8601 date
  end_date: string; // ISO 8601 date
  guest_name?: string;
  guest_count?: number;
  booking_amount?: number;
  booking_status?: string;
}

/**
 * Fetch iCal data from URL
 */
export async function fetchICalData(url: string): Promise<string> {
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Short-Term-Landlord/1.0',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch iCal data: ${response.status} ${response.statusText}`);
  }

  return await response.text();
}

/**
 * Parse iCal string into calendar events
 */
export function parseICalData(icalString: string, source: string): CalendarEvent[] {
  try {
    const jcalData = ICAL.parse(icalString);
    const comp = new ICAL.Component(jcalData);
    const vevents = comp.getAllSubcomponents('vevent');

    const events: CalendarEvent[] = [];

    for (const vevent of vevents) {
      const event = new ICAL.Event(vevent);

      // Extract basic event details
      const externalId = event.uid;
      const title = event.summary || 'Reserved';

      // Convert dates to ISO 8601 format (YYYY-MM-DD)
      const startDate = event.startDate.toJSDate();
      const endDate = event.endDate.toJSDate();

      // Extract guest info from description or summary
      const description = event.description || '';
      const guestName = extractGuestName(title, description, source);
      const guestCount = extractGuestCount(description);

      events.push({
        external_id: externalId,
        title,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        guest_name: guestName,
        guest_count: guestCount,
        booking_status: 'confirmed',
      });
    }

    return events;
  } catch (error: any) {
    throw new Error(`Failed to parse iCal data: ${error.message}`);
  }
}

/**
 * Extract guest name from event data
 */
function extractGuestName(title: string, description: string, source: string): string | undefined {
  // Different platforms format guest names differently

  // Airbnb typically includes name in title
  if (source === 'airbnb') {
    // Format: "Reserved - John Doe" or "John Doe"
    const match = title.match(/(?:Reserved - |^)([A-Z][a-z]+(?: [A-Z][a-z]+)*)/);
    if (match) {
      return match[1];
    }
  }

  // VRBO often includes guest name in description
  if (source === 'vrbo') {
    const nameMatch = description.match(/Guest:?\s*([^\n]+)/i);
    if (nameMatch) {
      return nameMatch[1].trim();
    }
  }

  // Booking.com format
  if (source === 'booking') {
    const nameMatch = description.match(/Name:?\s*([^\n]+)/i);
    if (nameMatch) {
      return nameMatch[1].trim();
    }
  }

  // Generic fallback - try to extract from title if it's not just "Reserved" or "Blocked"
  if (title && title !== 'Reserved' && title !== 'Blocked' && title !== 'Not available') {
    return title;
  }

  return undefined;
}

/**
 * Extract guest count from description
 */
function extractGuestCount(description: string): number | undefined {
  // Look for patterns like "2 guests", "Adults: 2", "Guests: 3"
  const patterns = [
    /(\d+)\s+guests?/i,
    /guests?:?\s*(\d+)/i,
    /adults?:?\s*(\d+)/i,
    /people:?\s*(\d+)/i,
  ];

  for (const pattern of patterns) {
    const match = description.match(pattern);
    if (match) {
      return parseInt(match[1], 10);
    }
  }

  return undefined;
}

/**
 * Sync iCal events to database
 */
export async function syncCalendarEvents(
  db: D1Database,
  propertyId: number,
  calendarId: number,
  events: CalendarEvent[],
  source: string
): Promise<{ inserted: number; updated: number; deleted: number }> {
  let inserted = 0;
  let updated = 0;
  let deleted = 0;

  // Get existing events for this calendar
  const existingEvents = await db
    .prepare(
      'SELECT id, external_id FROM calendar_events WHERE property_calendar_id = ?'
    )
    .bind(calendarId)
    .all();

  const existingIds = new Set(
    (existingEvents.results || []).map((e: any) => e.external_id)
  );
  const currentIds = new Set(events.map((e) => e.external_id));

  // Insert or update events
  for (const event of events) {
    if (existingIds.has(event.external_id)) {
      // Update existing event
      await db
        .prepare(
          `UPDATE calendar_events
           SET title = ?, start_date = ?, end_date = ?,
               guest_name = ?, guest_count = ?, booking_status = ?,
               updated_at = datetime('now')
           WHERE property_calendar_id = ? AND external_id = ?`
        )
        .bind(
          event.title,
          event.start_date,
          event.end_date,
          event.guest_name || null,
          event.guest_count || null,
          event.booking_status || 'confirmed',
          calendarId,
          event.external_id
        )
        .run();
      updated++;
    } else {
      // Insert new event
      await db
        .prepare(
          `INSERT INTO calendar_events
           (property_calendar_id, property_id, title, start_date, end_date,
            source, external_id, guest_name, guest_count, booking_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          calendarId,
          propertyId,
          event.title,
          event.start_date,
          event.end_date,
          source,
          event.external_id,
          event.guest_name || null,
          event.guest_count || null,
          event.booking_status || 'confirmed'
        )
        .run();
      inserted++;
    }
  }

  // Delete events that no longer exist in iCal feed
  for (const existing of existingEvents.results || []) {
    if (!currentIds.has((existing as any).external_id)) {
      await db
        .prepare('DELETE FROM calendar_events WHERE id = ?')
        .bind((existing as any).id)
        .run();
      deleted++;
    }
  }

  return { inserted, updated, deleted };
}
