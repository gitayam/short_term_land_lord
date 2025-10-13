/**
 * Public Property Showcase API
 * GET /api/public/properties/[id]?token=xxx - View property details (no auth required)
 *
 * This endpoint allows sharing property information with guests without authentication.
 * Access is controlled via a guest_access_token for privacy.
 */

import { Env } from '../../../_middleware';

interface PropertyWithDetails {
  property: any;
  images: any[];
  rooms: any[];
}

// GET /api/public/properties/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const propertyId = params.id as string;
    const url = new URL(request.url);
    const token = url.searchParams.get('token');

    // Get property data
    const property = await env.DB.prepare(
      'SELECT * FROM property WHERE id = ?'
    )
      .bind(propertyId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify guest access is enabled
    if (!(property as any).guest_access_enabled) {
      return new Response(
        JSON.stringify({ error: 'This property is not available for public viewing' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify token if property has one set
    const storedToken = (property as any).guest_access_token;
    if (storedToken && storedToken !== token) {
      return new Response(
        JSON.stringify({ error: 'Invalid access token' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get property images
    const images = await env.DB.prepare(
      'SELECT * FROM property_image WHERE property_id = ? ORDER BY display_order ASC, uploaded_at ASC'
    )
      .bind(propertyId)
      .all();

    // Get property rooms
    const rooms = await env.DB.prepare(
      'SELECT * FROM property_room WHERE property_id = ? ORDER BY display_order ASC, room_type ASC'
    )
      .bind(propertyId)
      .all();

    // Remove sensitive fields from property data
    const safeProperty = {
      id: (property as any).id,
      name: (property as any).name,
      address: (property as any).address,
      city: (property as any).city,
      state: (property as any).state,
      country: (property as any).country,
      property_type: (property as any).property_type,
      bedrooms: (property as any).bedrooms,
      bathrooms: (property as any).bathrooms,
      square_feet: (property as any).square_feet,
      total_beds: (property as any).total_beds,
      description: (property as any).description,
      checkin_time: (property as any).checkin_time,
      checkout_time: (property as any).checkout_time,
      guest_rules: (property as any).guest_rules,
      guest_checkin_instructions: (property as any).guest_checkin_instructions,
      guest_checkout_instructions: (property as any).guest_checkout_instructions,
      guest_wifi_instructions: (property as any).guest_wifi_instructions,
      local_attractions: (property as any).local_attractions,
      emergency_contact: (property as any).emergency_contact,
      guest_faq: (property as any).guest_faq,
    };

    return new Response(
      JSON.stringify({
        success: true,
        property: safeProperty,
        images: images.results || [],
        rooms: rooms.results || [],
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'public, max-age=300', // Cache for 5 minutes
        },
      }
    );
  } catch (error: any) {
    console.error('[Public Property GET] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to fetch property' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
