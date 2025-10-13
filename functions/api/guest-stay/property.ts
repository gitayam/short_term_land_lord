/**
 * Guest Stay Property Details API
 * GET /api/guest-stay/property
 * Returns enhanced property details for verified guests currently staying
 * Requires session_token from verification
 */

import { Env } from '../../_middleware';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    // Get session token from Authorization header
    const authHeader = request.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return new Response(
        JSON.stringify({ error: 'Missing or invalid authorization token' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const sessionToken = authHeader.substring(7); // Remove 'Bearer '

    // Verify session token and get guest stay info
    const session = await env.DB.prepare(
      `SELECT
        gss.*,
        ce.guest_name,
        ce.guest_email,
        ce.start_date,
        ce.end_date
      FROM guest_stay_session gss
      JOIN calendar_events ce ON gss.calendar_event_id = ce.id
      WHERE gss.session_token = ?
        AND datetime(gss.expires_at) > datetime('now')`
    )
      .bind(sessionToken)
      .first();

    if (!session) {
      return new Response(
        JSON.stringify({
          error: 'Invalid or expired session',
          message: 'Please verify your phone number again to access property details.'
        }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Update session access tracking
    await env.DB.prepare(
      `UPDATE guest_stay_session
       SET last_accessed = datetime('now'),
           access_count = access_count + 1
       WHERE session_token = ?`
    )
      .bind(sessionToken)
      .run();

    // Get comprehensive property details
    const property = await env.DB.prepare(
      `SELECT
        p.id,
        p.name,
        p.address,
        p.street_address,
        p.city,
        p.state,
        p.zip_code,
        p.description,
        p.bedrooms,
        p.bathrooms,
        p.wifi_network,
        p.wifi_password,
        p.checkin_time,
        p.checkout_time,
        p.guest_rules,
        p.guest_checkin_instructions,
        p.guest_checkout_instructions,
        p.guest_wifi_instructions,
        p.local_attractions,
        p.emergency_contact,
        p.guest_faq,
        p.trash_day,
        p.recycling_day,
        p.cleaning_supplies_location,
        p.special_instructions,
        u.first_name as owner_first_name,
        u.last_name as owner_last_name,
        u.email as owner_email,
        u.phone as owner_phone
      FROM property p
      JOIN users u ON p.owner_id = u.id
      WHERE p.id = ?`
    )
      .bind((session as any).property_id)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get property images
    const images = await env.DB.prepare(
      `SELECT image_url, caption, is_primary, display_order
       FROM property_image
       WHERE property_id = ?
       ORDER BY is_primary DESC, display_order ASC`
    )
      .bind((session as any).property_id)
      .all();

    // Get property rooms
    const rooms = await env.DB.prepare(
      `SELECT room_type, name, bed_type, bed_count, has_ensuite, amenities
       FROM property_room
       WHERE property_id = ?
       ORDER BY display_order ASC`
    )
      .bind((session as any).property_id)
      .all();

    // Return enhanced property details
    return new Response(
      JSON.stringify({
        success: true,
        guest_info: {
          name: (session as any).guest_name,
          email: (session as any).guest_email,
          check_in: (session as any).start_date,
          check_out: (session as any).end_date,
        },
        property: {
          ...property,
          images: images.results || [],
          rooms: rooms.results || [],
        },
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Guest Stay Property] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to retrieve property details' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
