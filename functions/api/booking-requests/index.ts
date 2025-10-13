/**
 * Booking Requests API
 * POST /api/booking-requests - Create new booking request (public, no auth)
 * GET /api/booking-requests - List booking requests (auth required, owner only)
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';
import { sendEmail, newBookingRequestEmail } from '../../utils/email';

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

// POST /api/booking-requests - Create booking request (PUBLIC)
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const data = await request.json();
    const {
      property_id,
      guest_name,
      guest_email,
      guest_phone,
      check_in_date,
      check_out_date,
      num_guests,
      message,
    } = data;

    // Validate required fields
    if (!property_id || !guest_name || !guest_email || !check_in_date || !check_out_date || !num_guests) {
      return new Response(
        JSON.stringify({
          error: 'Missing required fields: property_id, guest_name, guest_email, check_in_date, check_out_date, num_guests',
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(guest_email)) {
      return new Response(
        JSON.stringify({ error: 'Invalid email address' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Validate dates
    const checkIn = new Date(check_in_date);
    const checkOut = new Date(check_out_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (checkIn < today) {
      return new Response(
        JSON.stringify({ error: 'Check-in date cannot be in the past' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (checkOut <= checkIn) {
      return new Response(
        JSON.stringify({ error: 'Check-out date must be after check-in date' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify property exists and has guest access enabled
    const property = await env.DB.prepare(
      'SELECT id, name, guest_access_enabled, owner_id FROM property WHERE id = ?'
    )
      .bind(property_id)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (!(property as any).guest_access_enabled) {
      return new Response(
        JSON.stringify({ error: 'This property is not accepting booking requests' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Create booking request
    await env.DB.prepare(
      `INSERT INTO booking_request (property_id, guest_name, guest_email, guest_phone, check_in_date, check_out_date, num_guests, message, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')`
    )
      .bind(
        property_id,
        guest_name,
        guest_email,
        guest_phone || null,
        check_in_date,
        check_out_date,
        num_guests,
        message || null
      )
      .run();

    // Get the created booking request
    const created = await env.DB.prepare(
      'SELECT * FROM booking_request WHERE property_id = ? AND guest_email = ? ORDER BY created_at DESC LIMIT 1'
    )
      .bind(property_id, guest_email)
      .first<BookingRequest>();

    // Send email notification to property owner (async, don't wait)
    if (env.RESEND_API_KEY) {
      // Get owner details
      const owner = await env.DB.prepare(
        `SELECT u.email, u.first_name, u.last_name, p.name as property_name
         FROM user u
         JOIN property p ON p.owner_id = u.id
         WHERE p.id = ?`
      )
        .bind(property_id)
        .first();

      if (owner) {
        const ownerEmail = (owner as any).email;
        const ownerName = `${(owner as any).first_name} ${(owner as any).last_name}`;
        const propertyName = (owner as any).property_name;

        const emailTemplate = newBookingRequestEmail({
          ownerName,
          propertyName,
          guestName: guest_name,
          guestEmail: guest_email,
          guestPhone: guest_phone,
          checkInDate: check_in_date,
          checkOutDate: check_out_date,
          numGuests: num_guests,
          message,
          dashboardUrl: `${new URL(request.url).origin}/app/booking-requests`,
        });

        // Send email asynchronously (don't block response)
        context.waitUntil(
          sendEmail(
            {
              to: ownerEmail,
              subject: emailTemplate.subject,
              html: emailTemplate.html,
              replyTo: guest_email,
            },
            env.RESEND_API_KEY
          )
        );
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Booking request submitted successfully',
        booking_request: created,
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Booking Request POST] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to submit booking request' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// GET /api/booking-requests - List booking requests (OWNER)
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Get all booking requests for properties owned by this user
    const requests = await env.DB.prepare(
      `SELECT
        br.*,
        p.name as property_name,
        p.address as property_address
      FROM booking_request br
      JOIN property p ON br.property_id = p.id
      WHERE p.owner_id = ?
      ORDER BY br.created_at DESC`
    )
      .bind(user.userId)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        booking_requests: requests.results || [],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Booking Requests GET] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to fetch booking requests' }),
      {
        status: error.message === 'Unauthorized' || error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
