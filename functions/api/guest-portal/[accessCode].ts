/**
 * Guest Portal Public Access API
 * GET /api/guest-portal/[accessCode] - Public access to property guidebook
 */

import { Env } from '../../_middleware';

// GET /api/guest-portal/[accessCode] - NO AUTH REQUIRED (public endpoint)
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { env, params } = context;

  try {
    const accessCode = params.accessCode as string;

    // Verify access code
    const access = await env.DB.prepare(
      `SELECT
        gac.id, gac.property_id, gac.guest_name,
        gac.valid_from, gac.valid_until, gac.is_active,
        gac.access_count,
        p.name as property_name,
        p.address as property_address,
        p.image_url as property_image
      FROM guest_access_code gac
      LEFT JOIN property p ON gac.property_id = p.id
      WHERE gac.access_code = ?`
    )
      .bind(accessCode)
      .first();

    if (!access) {
      return new Response(
        JSON.stringify({
          error: 'Invalid access code',
          message: 'The access code you entered is not valid'
        }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check if active
    if (!access.is_active) {
      return new Response(
        JSON.stringify({
          error: 'Access code disabled',
          message: 'This access code has been disabled'
        }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check validity dates
    const now = new Date().toISOString().split('T')[0];
    if (now < access.valid_from) {
      return new Response(
        JSON.stringify({
          error: 'Access not yet valid',
          message: `Access begins on ${new Date(access.valid_from).toLocaleDateString()}`,
          valid_from: access.valid_from
        }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (now > access.valid_until) {
      return new Response(
        JSON.stringify({
          error: 'Access expired',
          message: `Access expired on ${new Date(access.valid_until).toLocaleDateString()}`,
          valid_until: access.valid_until
        }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Fetch guidebook
    const guidebook = await env.DB.prepare(
      `SELECT
        pg.id,
        pg.welcome_message,
        pg.property_image_url,
        pg.checkin_time,
        pg.checkout_time,
        pg.checkin_instructions,
        pg.checkout_instructions,
        pg.wifi_network,
        pg.wifi_password,
        pg.emergency_contact,
        pg.emergency_phone,
        pg.host_phone,
        pg.host_email,
        pg.parking_info,
        pg.parking_instructions,
        pg.house_rules,
        pg.quiet_hours,
        pg.max_guests,
        pg.smoking_allowed,
        pg.pets_allowed,
        pg.parties_allowed
      FROM property_guidebook pg
      WHERE pg.property_id = ? AND pg.is_published = 1`
    )
      .bind(access.property_id)
      .first();

    if (!guidebook) {
      return new Response(
        JSON.stringify({
          error: 'Guidebook not available',
          message: 'The property guidebook is not yet published',
          property: {
            name: access.property_name,
            address: access.property_address,
          }
        }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Fetch sections
    const sections = await env.DB.prepare(
      `SELECT title, content, section_type, icon, display_order
       FROM guidebook_section
       WHERE guidebook_id = ? AND is_visible = 1
       ORDER BY display_order ASC`
    )
      .bind(guidebook.id)
      .all();

    // Fetch recommendations
    const recommendations = await env.DB.prepare(
      `SELECT
        name, category, description, phone, website, address,
        distance_miles, price_range, rating, notes, is_favorite
      FROM local_recommendation
      WHERE property_id = ? AND is_visible = 1
      ORDER BY is_favorite DESC, category ASC, display_order ASC`
    )
      .bind(access.property_id)
      .all();

    // Update access tracking
    const accessCount = (access.access_count as number) || 0;
    await env.DB.prepare(
      `UPDATE guest_access_code
       SET access_count = ?,
           last_accessed = datetime('now'),
           first_accessed = COALESCE(first_accessed, datetime('now'))
       WHERE id = ?`
    )
      .bind(accessCount + 1, access.id)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        guest_name: access.guest_name,
        property: {
          name: access.property_name,
          address: access.property_address,
          image: access.property_image || guidebook.property_image_url,
        },
        guidebook: {
          ...guidebook,
          sections: sections.results || [],
          recommendations: recommendations.results || [],
        },
        access: {
          valid_from: access.valid_from,
          valid_until: access.valid_until,
        },
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store, no-cache, must-revalidate, private',
        },
      }
    );
  } catch (error: any) {
    console.error('[Guest Portal] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to load guest portal',
        message: error.message,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
