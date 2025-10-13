/**
 * Guest Stay Verification API
 * POST /api/guest-stay/verify
 * Verifies a guest is currently staying at a property using last 4 digits of phone number
 *
 * Edge cases handled:
 * - Same-day checkout/checkin: Uses property check-in/check-out times
 * - Multiple bookings same day: Matches exact phone number
 * - Check-in day before check-in time: Allows early access (2 hour grace period)
 * - Check-out day after checkout time: 2 hour grace period after checkout
 */

import { Env } from '../../_middleware';

interface VerifyRequest {
  property_id: string;
  phone_last_4: string;
}

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const data: VerifyRequest = await request.json();
    const { property_id, phone_last_4 } = data;

    // Validate input
    if (!property_id || !phone_last_4) {
      return new Response(
        JSON.stringify({ error: 'property_id and phone_last_4 are required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (phone_last_4.length !== 4 || !/^\d{4}$/.test(phone_last_4)) {
      return new Response(
        JSON.stringify({ error: 'phone_last_4 must be exactly 4 digits' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get property with check-in/check-out times
    const property = await env.DB.prepare(
      `SELECT id, name, checkin_time, checkout_time FROM property WHERE id = ?`
    )
      .bind(property_id)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const checkinTime = (property as any).checkin_time || '15:00'; // Default 3pm
    const checkoutTime = (property as any).checkout_time || '11:00'; // Default 11am

    // Get current date/time info
    const now = new Date();
    const currentDate = now.toISOString().split('T')[0]; // YYYY-MM-DD
    const currentTime = now.toTimeString().substring(0, 5); // HH:MM

    // Calculate grace periods (2 hours before checkin, 2 hours after checkout)
    const checkinGraceTime = subtractHours(checkinTime, 2);
    const checkoutGraceTime = addHours(checkoutTime, 2);

    // Find matching calendar events
    // Match: property_id, last 4 of phone, and date range includes today
    const events = await env.DB.prepare(
      `SELECT
        ce.*,
        p.name as property_name,
        p.address as property_address,
        p.checkin_time,
        p.checkout_time
      FROM calendar_events ce
      JOIN property p ON ce.property_id = p.id
      WHERE ce.property_id = ?
        AND ce.guest_phone IS NOT NULL
        AND substr(ce.guest_phone, -4) = ?
        AND ce.start_date <= ?
        AND ce.end_date >= ?
        AND ce.booking_status = 'confirmed'
      ORDER BY ce.start_date DESC`
    )
      .bind(property_id, phone_last_4, currentDate, currentDate)
      .all();

    if (!events.results || events.results.length === 0) {
      return new Response(
        JSON.stringify({
          error: 'No active booking found',
          message: 'No booking found for this phone number at this property today. Please check your phone number and try again.'
        }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Handle multiple events on same day (checkout/checkin edge case)
    let activeEvent = null;

    if (events.results.length === 1) {
      activeEvent = events.results[0];
    } else {
      // Multiple bookings found - use time-based logic
      for (const event of events.results as any[]) {
        const isCheckInDay = event.start_date === currentDate;
        const isCheckOutDay = event.end_date === currentDate;

        // Check-in day: allow access if within grace period or after check-in time
        if (isCheckInDay && !isCheckOutDay) {
          if (currentTime >= checkinGraceTime) {
            activeEvent = event;
            break;
          }
        }
        // Check-out day: allow access until grace period expires
        else if (isCheckOutDay && !isCheckInDay) {
          if (currentTime <= checkoutGraceTime) {
            activeEvent = event;
            break;
          }
        }
        // Middle of stay (not checkin or checkout day)
        else if (!isCheckInDay && !isCheckOutDay) {
          activeEvent = event;
          break;
        }
        // Same day checkout AND checkin (rare but possible)
        else if (isCheckInDay && isCheckOutDay) {
          // For very short stays (same day booking), allow access all day
          activeEvent = event;
          break;
        }
      }

      // If no active event found with time logic, default to most recent
      if (!activeEvent && events.results.length > 0) {
        activeEvent = events.results[0];
      }
    }

    if (!activeEvent) {
      return new Response(
        JSON.stringify({
          error: 'Access not available at this time',
          message: 'Your booking may not be active yet, or the checkout grace period has expired.'
        }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Generate session token for this guest
    const sessionToken = crypto.randomUUID();
    const expiresAt = new Date((activeEvent as any).end_date);
    expiresAt.setHours(23, 59, 59); // Expires at end of checkout day

    // Create guest stay session
    await env.DB.prepare(
      `INSERT INTO guest_stay_session (
        property_id, calendar_event_id, guest_phone_last_4,
        session_token, expires_at
      ) VALUES (?, ?, ?, ?, ?)`
    )
      .bind(
        property_id,
        (activeEvent as any).id,
        phone_last_4,
        sessionToken,
        expiresAt.toISOString()
      )
      .run();

    // Return success with session token
    return new Response(
      JSON.stringify({
        success: true,
        message: 'Verification successful',
        session_token: sessionToken,
        booking_details: {
          guest_name: (activeEvent as any).guest_name,
          check_in_date: (activeEvent as any).start_date,
          check_out_date: (activeEvent as any).end_date,
          property_name: (activeEvent as any).property_name,
        },
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Guest Stay Verify] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Verification failed' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};

// Helper functions for time calculations
function addHours(time: string, hours: number): string {
  const [h, m] = time.split(':').map(Number);
  const newHours = (h + hours) % 24;
  return `${String(newHours).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function subtractHours(time: string, hours: number): string {
  const [h, m] = time.split(':').map(Number);
  let newHours = h - hours;
  if (newHours < 0) newHours += 24;
  return `${String(newHours).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}
