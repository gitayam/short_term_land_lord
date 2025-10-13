/**
 * Booking Confirmation API
 * GET /api/bookings/[id]/confirmation - Get booking details for confirmation page
 * Public endpoint - no authentication required
 */

import { Env } from '../../../_middleware';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, env } = context;
  const bookingId = params.id as string;

  try {
    // Find booking by external_id (for guest bookings) or id
    const booking = await env.DB.prepare(
      `SELECT
        ce.*,
        p.id as property_id,
        p.name as property_name,
        p.address as property_address,
        p.city as property_city,
        p.state as property_state,
        p.country as property_country,
        p.checkin_time,
        p.checkout_time,
        p.guest_checkin_instructions,
        p.guest_wifi_instructions,
        p.emergency_contact
       FROM calendar_events ce
       JOIN property p ON ce.property_id = p.id
       WHERE ce.external_id = ? OR ce.id = ?
       LIMIT 1`
    )
      .bind(bookingId, bookingId)
      .first();

    if (!booking) {
      return new Response(
        JSON.stringify({ error: 'Booking not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const b = booking as any;

    // Format response
    const response = {
      booking: {
        id: b.id,
        external_id: b.external_id,
        check_in_date: b.start_date,
        check_out_date: b.end_date,
        guest_name: b.guest_name,
        guest_email: b.guest_email,
        guest_phone: b.guest_phone,
        num_guests: b.guest_count || 1,
        total_paid: 0, // TODO: Get from financial_transactions or booking_request
        booking_status: b.booking_status,
      },
      property: {
        id: b.property_id,
        name: b.property_name,
        address: b.property_address,
        city: b.property_city,
        state: b.property_state,
        country: b.property_country,
        checkin_time: b.checkin_time,
        checkout_time: b.checkout_time,
        guest_checkin_instructions: b.guest_checkin_instructions,
        guest_wifi_instructions: b.guest_wifi_instructions,
        emergency_contact: b.emergency_contact,
      },
    };

    // Try to get total_paid from financial_transactions
    const transaction = await env.DB.prepare(
      `SELECT amount FROM financial_transactions
       WHERE reference_id LIKE ?
       ORDER BY transaction_date DESC
       LIMIT 1`
    )
      .bind(`%${b.external_id}%`)
      .first();

    if (transaction) {
      response.booking.total_paid = (transaction as any).amount || 0;
    }

    return new Response(
      JSON.stringify(response),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Booking Confirmation] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to load booking confirmation' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
