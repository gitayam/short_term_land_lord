/**
 * Booking Request Management API
 * PUT /api/booking-requests/[id] - Update booking request status (owner only)
 * DELETE /api/booking-requests/[id] - Cancel/delete booking request
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';
import { sendEmail, bookingApprovedEmail, bookingRejectedEmail } from '../../utils/email';
import { createStripePaymentLink } from '../../utils/stripe';

interface BookingRequest {
  id: string;
  property_id: string;
  guest_name: string;
  guest_email: string;
  guest_phone: string | null;
  check_in_date: string;
  check_out_date: string;
  num_guests: number;
  message: string | null;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  owner_response: string | null;
  created_at: string;
  updated_at: string;
}

// PUT /api/booking-requests/[id] - Update booking request
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const requestId = params.id as string;

    // Get booking request and verify ownership
    const bookingRequest = await env.DB.prepare(
      `SELECT br.*, p.owner_id
       FROM booking_request br
       JOIN property p ON br.property_id = p.id
       WHERE br.id = ?`
    )
      .bind(requestId)
      .first();

    if (!bookingRequest) {
      return new Response(
        JSON.stringify({ error: 'Booking request not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify user owns the property
    if ((bookingRequest as any).owner_id !== user.userId && user.role !== 'admin') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - you do not own this property' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const data = await request.json();
    const { status, owner_response } = data;

    // Validate status
    const validStatuses = ['pending', 'approved', 'rejected', 'cancelled'];
    if (status && !validStatuses.includes(status)) {
      return new Response(
        JSON.stringify({
          error: `Invalid status. Must be one of: ${validStatuses.join(', ')}`,
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // If approving, check for calendar conflicts
    // IMPORTANT: Allow same-day checkout/checkin (turnover)
    // Conflict only if: new_checkin < existing_checkout AND new_checkout > existing_checkin
    if (status === 'approved') {
      const existingEvents = await env.DB.prepare(
        `SELECT id, start_date, end_date FROM calendar_events
         WHERE property_id = ?
           AND booking_status IN ('confirmed', 'blocked')
           AND start_date < ?
           AND end_date > ?`
      )
        .bind(
          bookingRequest.property_id,
          bookingRequest.check_out_date,  // existing must start before new checkout
          bookingRequest.check_in_date     // existing must end after new checkin
        )
        .all();

      if (existingEvents && existingEvents.results && existingEvents.results.length > 0) {
        return new Response(
          JSON.stringify({
            error: 'Cannot approve: dates conflict with existing booking',
            conflicting_events: existingEvents.results,
          }),
          { status: 409, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // Update booking request
    await env.DB.prepare(
      `UPDATE booking_request
       SET status = COALESCE(?, status),
           owner_response = COALESCE(?, owner_response),
           updated_at = datetime('now')
       WHERE id = ?`
    )
      .bind(
        status || null,
        owner_response !== undefined ? owner_response : null,
        requestId
      )
      .run();

    // If approved, create calendar event
    if (status === 'approved') {
      // Get or create property_calendar entry
      let propertyCalendar = await env.DB.prepare(
        'SELECT id FROM property_calendar WHERE property_id = ? LIMIT 1'
      )
        .bind(bookingRequest.property_id)
        .first();

      let calendarId: number;

      if (!propertyCalendar) {
        // Create property_calendar entry
        const result = await env.DB.prepare(
          `INSERT INTO property_calendar (property_id, sync_enabled, last_sync)
           VALUES (?, 0, datetime('now'))`
        )
          .bind(bookingRequest.property_id)
          .run();

        calendarId = result.meta.last_row_id as number;
      } else {
        calendarId = (propertyCalendar as any).id;
      }

      // Create calendar event with guest contact info for stay access
      await env.DB.prepare(
        `INSERT INTO calendar_events (
          property_calendar_id, property_id, title, start_date, end_date,
          source, guest_name, guest_count, guest_email, guest_phone, booking_status
        )
        VALUES (?, ?, ?, ?, ?, 'direct', ?, ?, ?, ?, 'confirmed')`
      )
        .bind(
          calendarId,
          bookingRequest.property_id,
          `${bookingRequest.guest_name} - Direct Booking`,
          bookingRequest.check_in_date,
          bookingRequest.check_out_date,
          bookingRequest.guest_name,
          bookingRequest.num_guests,
          bookingRequest.guest_email,
          bookingRequest.guest_phone
        )
        .run();

      // Handle payment based on whether booking has payment intent
      let paymentLink: string | undefined;
      const paymentIntentId = bookingRequest.stripe_payment_intent_id as string | undefined;

      if (env.STRIPE_SECRET_KEY) {
        if (paymentIntentId) {
          // NEW FLOW: Capture pre-validated payment intent
          console.log('[Booking Approval] Capturing payment for intent:', paymentIntentId);

          try {
            const captureResponse = await fetch(
              `https://api.stripe.com/v1/payment_intents/${paymentIntentId}/capture`,
              {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${env.STRIPE_SECRET_KEY}`,
                  'Content-Type': 'application/x-www-form-urlencoded',
                },
              }
            );

            if (!captureResponse.ok) {
              const error = await captureResponse.json();
              console.error('[Booking Approval] Failed to capture payment:', error);
            } else {
              const capturedIntent = await captureResponse.json();
              console.log('[Booking Approval] Payment captured successfully:', capturedIntent.id);

              // Update payment status and create transaction record
              await env.DB.prepare(
                `UPDATE booking_request
                 SET payment_status = 'paid',
                     updated_at = datetime('now')
                 WHERE id = ?`
              )
                .bind(requestId)
                .run();

              await env.DB.prepare(
                `INSERT INTO payment_transactions
                 (property_id, booking_request_id, transaction_type, amount, currency, status, stripe_payment_intent_id, description, payment_date)
                 SELECT
                   property_id,
                   id,
                   'booking_payment',
                   estimated_total,
                   'usd',
                   'succeeded',
                   stripe_payment_intent_id,
                   'Booking payment for ' || guest_name,
                   datetime('now')
                 FROM booking_request
                 WHERE id = ?`
              )
                .bind(requestId)
                .run();
            }
          } catch (error: any) {
            console.error('[Booking Approval] Payment capture error:', error);
          }
        } else {
          // OLD FLOW: Generate payment link for bookings without payment intent
          console.log('[Booking Approval] No payment intent, generating payment link');

          const property = await env.DB.prepare(
            'SELECT nightly_rate, cleaning_fee, name FROM property WHERE id = ?'
          )
            .bind(bookingRequest.property_id)
            .first();

          if (property) {
            const prop = property as any;
            const checkIn = new Date(bookingRequest.check_in_date as string);
            const checkOut = new Date(bookingRequest.check_out_date as string);
            const nights = Math.ceil((checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24));

            const nightlyTotal = (prop.nightly_rate || 100) * nights;
            const cleaningFee = prop.cleaning_fee || 0;
            const totalAmount = nightlyTotal + cleaningFee;

            const paymentResult = await createStripePaymentLink(
              {
                amount: totalAmount,
                currency: 'usd',
                description: `Booking: ${prop.name} (${bookingRequest.check_in_date} to ${bookingRequest.check_out_date})`,
                customerEmail: bookingRequest.guest_email as string,
                customerName: bookingRequest.guest_name as string,
                metadata: {
                  booking_request_id: requestId,
                  property_id: bookingRequest.property_id as string,
                  check_in: bookingRequest.check_in_date as string,
                  check_out: bookingRequest.check_out_date as string,
                },
                successUrl: `${new URL(request.url).origin}/booking-success`,
              },
              { apiKey: env.STRIPE_SECRET_KEY }
            );

            if (paymentResult.success && paymentResult.paymentLink) {
              paymentLink = paymentResult.paymentLink;

              await env.DB.prepare(
                `UPDATE booking_request
                 SET stripe_payment_link = ?,
                     estimated_total = ?,
                     payment_status = 'pending',
                     updated_at = datetime('now')
                 WHERE id = ?`
              )
                .bind(paymentLink, totalAmount, requestId)
                .run();
            }
          }
        }
      }

      // Invalidate calendar cache for this property
      await env.KV.delete(`calendar:events:${bookingRequest.property_id}:all:all`);
    }

    // If rejected or cancelled, remove calendar event if exists
    if (status === 'rejected' || status === 'cancelled') {
      await env.DB.prepare(
        `DELETE FROM calendar_events
         WHERE property_id = ?
           AND start_date = ?
           AND end_date = ?
           AND source = 'direct'
           AND guest_name = ?`
      )
        .bind(
          bookingRequest.property_id,
          bookingRequest.check_in_date,
          bookingRequest.check_out_date,
          bookingRequest.guest_name
        )
        .run();

      // Invalidate calendar cache for this property
      await env.KV.delete(`calendar:events:${bookingRequest.property_id}:all:all`);
    }

    // Get updated booking request with property details
    const updated = await env.DB.prepare(
      `SELECT br.*, p.name as property_name, p.address as property_address
       FROM booking_request br
       JOIN property p ON br.property_id = p.id
       WHERE br.id = ?`
    )
      .bind(requestId)
      .first();

    // Send email notification to guest
    if (env.AWS_ACCESS_KEY_ID && env.AWS_SECRET_ACCESS_KEY && updated && (status === 'approved' || status === 'rejected')) {
      const br = updated as any;

      const awsCredentials = {
        accessKeyId: env.AWS_ACCESS_KEY_ID,
        secretAccessKey: env.AWS_SECRET_ACCESS_KEY,
        region: env.AWS_REGION || 'us-east-1',
      };

      const fromEmail = env.AWS_SES_FROM_EMAIL || 'noreply@example.com';

      if (status === 'approved') {
        const emailTemplate = bookingApprovedEmail({
          guestName: br.guest_name,
          propertyName: br.property_name,
          propertyAddress: br.property_address,
          checkInDate: br.check_in_date,
          checkOutDate: br.check_out_date,
          numGuests: br.num_guests,
          ownerResponse: owner_response,
          propertyUrl: `${new URL(request.url).origin}/p/${br.property_id}`,
          paymentLink: br.stripe_payment_link || undefined,
          totalAmount: br.estimated_total || undefined,
        });

        // Send email asynchronously
        context.waitUntil(
          sendEmail(
            {
              to: br.guest_email,
              subject: emailTemplate.subject,
              html: emailTemplate.html,
            },
            awsCredentials,
            fromEmail
          )
        );
      } else if (status === 'rejected') {
        const emailTemplate = bookingRejectedEmail({
          guestName: br.guest_name,
          propertyName: br.property_name,
          checkInDate: br.check_in_date,
          checkOutDate: br.check_out_date,
          ownerResponse: owner_response,
          searchUrl: new URL(request.url).origin,
        });

        // Send email asynchronously
        context.waitUntil(
          sendEmail(
            {
              to: br.guest_email,
              subject: emailTemplate.subject,
              html: emailTemplate.html,
            },
            awsCredentials,
            fromEmail
          )
        );
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: status === 'approved'
          ? 'Booking approved and calendar updated'
          : 'Booking request updated successfully',
        booking_request: updated,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Booking Request PUT] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to update booking request' }),
      {
        status: error.message === 'Unauthorized' || error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/booking-requests/[id] - Cancel/delete booking request
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const requestId = params.id as string;

    // Get booking request and verify ownership
    const bookingRequest = await env.DB.prepare(
      `SELECT br.*, p.owner_id
       FROM booking_request br
       JOIN property p ON br.property_id = p.id
       WHERE br.id = ?`
    )
      .bind(requestId)
      .first();

    if (!bookingRequest) {
      return new Response(
        JSON.stringify({ error: 'Booking request not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify user owns the property or is admin
    if ((bookingRequest as any).owner_id !== user.userId && user.role !== 'admin') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - you do not own this property' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Delete booking request
    await env.DB.prepare('DELETE FROM booking_request WHERE id = ?')
      .bind(requestId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Booking request deleted successfully',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Booking Request DELETE] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to delete booking request' }),
      {
        status: error.message === 'Unauthorized' || error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
