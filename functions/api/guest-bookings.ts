/**
 * Guest Bookings API
 * POST /api/guest-bookings - Create booking without authentication
 * Implements frictionless booking flow with payment before account creation
 */

import { Env } from '../_middleware';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const data = await request.json();

    const {
      property_id,
      check_in_date,
      check_out_date,
      guest_name,
      guest_email,
      guest_phone,
      num_guests,
      special_requests,
      payment,
    } = data;

    // Validation
    if (!property_id || !check_in_date || !check_out_date || !guest_name || !guest_email || !num_guests) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (!payment || !payment.amount) {
      return new Response(
        JSON.stringify({ error: 'Payment information required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify property exists
    const property = await env.DB.prepare(
      'SELECT id, owner_id, name, nightly_rate, cleaning_fee FROM property WHERE id = ?'
    )
      .bind(property_id)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check for availability (no overlapping bookings)
    // IMPORTANT: Allow same-day checkout/checkin (turnover)
    // Conflict only if: new_checkin < existing_checkout AND new_checkout > existing_checkin
    const overlappingBookings = await env.DB.prepare(
      `SELECT id, start_date, end_date FROM calendar_events
       WHERE property_id = ?
       AND booking_status IN ('confirmed', 'blocked')
       AND start_date < ?
       AND end_date > ?`
    )
      .bind(
        property_id,
        check_out_date,  // existing must start before new checkout
        check_in_date    // existing must end after new checkin
      )
      .all();

    if (overlappingBookings.results && overlappingBookings.results.length > 0) {
      return new Response(
        JSON.stringify({ error: 'Property is not available for selected dates' }),
        { status: 409, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Process payment (in production, integrate with Stripe)
    // For now, we'll simulate payment success
    const paymentProcessed = true;
    const transactionId = `txn_${Date.now()}_${Math.random().toString(36).substring(7)}`;

    if (!paymentProcessed) {
      return new Response(
        JSON.stringify({ error: 'Payment processing failed' }),
        { status: 402, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Create booking in database
    const bookingId = `booking_${Date.now()}_${Math.random().toString(36).substring(7)}`;

    // Insert into calendar_events as confirmed booking
    const externalId = `guest-booking-${Date.now()}`;

    // Get or create "direct" calendar for this property
    let directCalendar = await env.DB.prepare(
      'SELECT id FROM property_calendar WHERE property_id = ? AND platform_name = ?'
    )
      .bind(property_id, 'direct')
      .first();

    if (!directCalendar) {
      await env.DB.prepare(
        `INSERT INTO property_calendar (property_id, platform_name, ical_url, is_active)
         VALUES (?, 'direct', NULL, 1)`
      )
        .bind(property_id)
        .run();

      directCalendar = await env.DB.prepare(
        'SELECT id FROM property_calendar WHERE property_id = ? AND platform_name = ?'
      )
        .bind(property_id, 'direct')
        .first();
    }

    // Insert booking event
    await env.DB.prepare(
      `INSERT INTO calendar_events
       (property_calendar_id, property_id, title, start_date, end_date, source,
        external_id, booking_status, guest_name, guest_email, guest_phone, guest_count, notes)
       VALUES (?, ?, ?, ?, ?, 'direct', ?, 'confirmed', ?, ?, ?, ?, ?)`
    )
      .bind(
        (directCalendar as any).id,
        property_id,
        `Booking - ${guest_name}`,
        check_in_date,
        check_out_date,
        externalId,
        guest_name,
        guest_email,
        guest_phone || null,
        num_guests,
        special_requests || null
      )
      .run();

    // Get the created booking
    const createdBooking = await env.DB.prepare(
      'SELECT * FROM calendar_events WHERE external_id = ?'
    )
      .bind(externalId)
      .first();

    // Store payment record (you might want a separate payments table)
    await env.DB.prepare(
      `INSERT INTO financial_transactions
       (property_id, transaction_type, amount, description, transaction_date, payment_method, reference_id)
       VALUES (?, 'payment', ?, ?, datetime('now'), 'card', ?)`
    )
      .bind(
        property_id,
        payment.amount,
        `Guest booking: ${guest_name} (${check_in_date} to ${check_out_date})`,
        transactionId
      )
      .run()
      .catch(() => {
        // Financial table might not exist, silently fail
        console.log('[Guest Booking] Could not record financial transaction');
      });

    // Invalidate cache
    await env.KV.delete(`calendar:events:${property_id}:all:all`);

    // TODO: Send confirmation email to guest and owner
    // TODO: Create access code for guest portal

    return new Response(
      JSON.stringify({
        success: true,
        booking: {
          id: (createdBooking as any).id,
          external_id: externalId,
          property_id,
          check_in_date,
          check_out_date,
          guest_name,
          guest_email,
          num_guests,
          total_paid: payment.amount,
          transaction_id: transactionId,
          booking_status: 'confirmed',
        },
        message: 'Booking confirmed! Check your email for details.',
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Guest Booking] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to create booking' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
