/**
 * Property Detail API
 * GET    /api/properties/[id] - Get single property
 * PUT    /api/properties/[id] - Update property
 * DELETE /api/properties/[id] - Delete property
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/properties/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;

    const property = await env.DB.prepare(
      'SELECT * FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(propertyId, user.userId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    return new Response(
      JSON.stringify({
        success: true,
        property,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Property GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch property',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/properties/[id]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const data = await request.json();

    // Verify ownership
    const property = await env.DB.prepare(
      'SELECT id FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(propertyId, user.userId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Update property with ALL fields
    await env.DB.prepare(
      `UPDATE property SET
        name = COALESCE(?, name),
        address = COALESCE(?, address),
        street_address = COALESCE(?, street_address),
        city = COALESCE(?, city),
        state = COALESCE(?, state),
        zip_code = COALESCE(?, zip_code),
        country = COALESCE(?, country),
        description = COALESCE(?, description),
        property_type = COALESCE(?, property_type),
        bedrooms = COALESCE(?, bedrooms),
        bathrooms = COALESCE(?, bathrooms),
        square_feet = COALESCE(?, square_feet),
        year_built = COALESCE(?, year_built),
        total_beds = COALESCE(?, total_beds),
        bed_sizes = COALESCE(?, bed_sizes),
        number_of_showers = COALESCE(?, number_of_showers),
        number_of_tubs = COALESCE(?, number_of_tubs),
        number_of_tvs = COALESCE(?, number_of_tvs),
        wifi_network = COALESCE(?, wifi_network),
        wifi_password = COALESCE(?, wifi_password),
        trash_day = COALESCE(?, trash_day),
        trash_schedule_type = COALESCE(?, trash_schedule_type),
        trash_schedule_details = COALESCE(?, trash_schedule_details),
        recycling_day = COALESCE(?, recycling_day),
        recycling_schedule_type = COALESCE(?, recycling_schedule_type),
        recycling_schedule_details = COALESCE(?, recycling_schedule_details),
        recycling_notes = COALESCE(?, recycling_notes),
        internet_provider = COALESCE(?, internet_provider),
        internet_account = COALESCE(?, internet_account),
        internet_contact = COALESCE(?, internet_contact),
        electric_provider = COALESCE(?, electric_provider),
        electric_account = COALESCE(?, electric_account),
        electric_contact = COALESCE(?, electric_contact),
        water_provider = COALESCE(?, water_provider),
        water_account = COALESCE(?, water_account),
        water_contact = COALESCE(?, water_contact),
        trash_provider = COALESCE(?, trash_provider),
        trash_account = COALESCE(?, trash_account),
        trash_contact = COALESCE(?, trash_contact),
        cleaning_supplies_location = COALESCE(?, cleaning_supplies_location),
        entry_instructions = COALESCE(?, entry_instructions),
        special_instructions = COALESCE(?, special_instructions),
        checkin_time = COALESCE(?, checkin_time),
        checkout_time = COALESCE(?, checkout_time),
        guest_access_enabled = COALESCE(?, guest_access_enabled),
        guest_access_token = COALESCE(?, guest_access_token),
        guest_rules = COALESCE(?, guest_rules),
        guest_checkin_instructions = COALESCE(?, guest_checkin_instructions),
        guest_checkout_instructions = COALESCE(?, guest_checkout_instructions),
        guest_wifi_instructions = COALESCE(?, guest_wifi_instructions),
        local_attractions = COALESCE(?, local_attractions),
        emergency_contact = COALESCE(?, emergency_contact),
        guest_faq = COALESCE(?, guest_faq),
        ical_url = COALESCE(?, ical_url),
        color = COALESCE(?, color),
        updated_at = datetime('now')
       WHERE id = ?`
    )
      .bind(
        data.name || null,
        data.address || null,
        data.street_address || null,
        data.city || null,
        data.state || null,
        data.zip_code || null,
        data.country || null,
        data.description || null,
        data.property_type || null,
        data.bedrooms || null,
        data.bathrooms || null,
        data.square_feet || null,
        data.year_built || null,
        data.total_beds || null,
        data.bed_sizes || null,
        data.number_of_showers || null,
        data.number_of_tubs || null,
        data.number_of_tvs || null,
        data.wifi_network || null,
        data.wifi_password || null,
        data.trash_day || null,
        data.trash_schedule_type || null,
        data.trash_schedule_details || null,
        data.recycling_day || null,
        data.recycling_schedule_type || null,
        data.recycling_schedule_details || null,
        data.recycling_notes || null,
        data.internet_provider || null,
        data.internet_account || null,
        data.internet_contact || null,
        data.electric_provider || null,
        data.electric_account || null,
        data.electric_contact || null,
        data.water_provider || null,
        data.water_account || null,
        data.water_contact || null,
        data.trash_provider || null,
        data.trash_account || null,
        data.trash_contact || null,
        data.cleaning_supplies_location || null,
        data.entry_instructions || null,
        data.special_instructions || null,
        data.checkin_time || null,
        data.checkout_time || null,
        data.guest_access_enabled || null,
        data.guest_access_token || null,
        data.guest_rules || null,
        data.guest_checkin_instructions || null,
        data.guest_checkout_instructions || null,
        data.guest_wifi_instructions || null,
        data.local_attractions || null,
        data.emergency_contact || null,
        data.guest_faq || null,
        data.ical_url || null,
        data.color || null,
        propertyId
      )
      .run();

    // Get updated property
    const updated = await env.DB.prepare('SELECT * FROM property WHERE id = ?')
      .bind(propertyId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        property: updated,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Property PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to update property',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/properties/[id]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;

    // Verify ownership
    const property = await env.DB.prepare(
      'SELECT id FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(propertyId, user.userId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Delete all related records first (for tables without CASCADE DELETE)
    // Note: Tables with ON DELETE CASCADE will be handled automatically

    // Delete property images
    await env.DB.prepare('DELETE FROM property_image WHERE property_id = ?')
      .bind(propertyId)
      .run();

    // Delete property calendars and their events
    await env.DB.prepare('DELETE FROM calendar_events WHERE property_id = ?')
      .bind(propertyId)
      .run();

    await env.DB.prepare('DELETE FROM property_calendar WHERE property_id = ?')
      .bind(propertyId)
      .run();

    // Delete tasks linked to this property
    await env.DB.prepare('DELETE FROM task WHERE property_id = ?')
      .bind(propertyId)
      .run();

    // Delete cleaning sessions
    await env.DB.prepare('DELETE FROM cleaning_session WHERE property_id = ?')
      .bind(propertyId)
      .run();

    // Delete inventory items
    await env.DB.prepare('DELETE FROM inventory_item WHERE property_id = ?')
      .bind(propertyId)
      .run();

    // Delete guest invitations
    await env.DB.prepare('DELETE FROM guest_invitation WHERE property_id = ?')
      .bind(propertyId)
      .run();

    // Delete rooms if table exists
    await env.DB.prepare('DELETE FROM room WHERE property_id = ?')
      .bind(propertyId)
      .run()
      .catch(() => {}); // Ignore if table doesn't exist

    // Finally, delete the property itself
    await env.DB.prepare('DELETE FROM property WHERE id = ?')
      .bind(propertyId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Property deleted successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Property DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to delete property',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
