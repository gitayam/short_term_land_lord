/**
 * GET /api/calendar/availability?year=2025&month=10&property_id=xxx
 * Returns availability for Fayetteville, NC properties for a given month
 * Optional property_id parameter to filter by specific property
 */

interface Env {
  DB: D1Database;
}

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;
  const url = new URL(request.url);
  const year = url.searchParams.get('year');
  const month = url.searchParams.get('month');
  const propertyId = url.searchParams.get('property_id');

  if (!year || !month) {
    return new Response(
      JSON.stringify({ error: 'year and month parameters required' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  const yearNum = parseInt(year);
  const monthNum = parseInt(month);

  // Get first and last day of the month
  const firstDay = new Date(yearNum, monthNum - 1, 1);
  const lastDay = new Date(yearNum, monthNum, 0);

  const startDate = firstDay.toISOString().split('T')[0];
  const endDate = lastDay.toISOString().split('T')[0];

  try {
    // Build query with optional property filter
    let query = `
      SELECT
        ce.id,
        ce.property_id,
        ce.start_date,
        ce.end_date,
        ce.title,
        ce.source,
        ce.booking_status,
        p.name as property_name,
        p.city
      FROM calendar_events ce
      JOIN property p ON ce.property_id = p.id
      WHERE p.city = 'Fayetteville'
        AND p.state = 'NC'
    `;

    const bindings = [];

    // Add property filter if specified
    if (propertyId) {
      query += ` AND ce.property_id = ?`;
      bindings.push(propertyId);
    }

    query += `
        AND (
          (ce.start_date <= ? AND ce.end_date >= ?)
          OR (ce.start_date >= ? AND ce.start_date <= ?)
        )
      ORDER BY ce.start_date ASC
    `;

    bindings.push(endDate, startDate, startDate, endDate);

    // Get all calendar events (bookings, blocks) for this month
    const { results: events } = await env.DB.prepare(query).bind(...bindings).all();

    // Build a map of blocked dates
    const blockedDates: Record<string, boolean> = {};

    events?.forEach((event: any) => {
      const startDate = new Date(event.start_date);
      const endDate = new Date(event.end_date);

      // Mark each day in the booking range as blocked
      // IMPORTANT: Don't block the checkout date (< endDate not <=)
      // This allows same-day turnovers: guest A checks out, guest B checks in
      for (let d = new Date(startDate); d < endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        blockedDates[dateStr] = true;
      }
    });

    // Get all Fayetteville properties with full details
    const { results: properties } = await env.DB.prepare(`
      SELECT
        id, slug, name, address, city, state, bedrooms, bathrooms,
        description, property_type, square_feet,
        street_name, primary_image_url,
        max_guests, min_guests,
        pets_allowed, max_pets, pet_fee, pet_fee_per_pet,
        allow_early_checkin, allow_late_checkout,
        early_checkin_fee, late_checkout_fee,
        average_rating, total_reviews,
        early_checkin_hours, late_checkout_hours,
        nightly_rate, cleaning_fee, security_deposit,
        weekend_rate, min_nights, max_nights,
        display_address, neighborhood,
        approximate_latitude, approximate_longitude,
        amenities
      FROM property
      WHERE city = 'Fayetteville' AND state = 'NC'
      ORDER BY name ASC
    `).all();

    // Fetch images for each property
    const propertiesWithImages = await Promise.all(
      (properties || []).map(async (property: any) => {
        const { results: images } = await env.DB.prepare(`
          SELECT id, image_url, caption, display_order, is_primary
          FROM property_images
          WHERE property_id = ?
          ORDER BY display_order ASC
        `).bind(property.id).all();

        return {
          ...property,
          images: images || [],
          amenities: property.amenities ? JSON.parse(property.amenities) : []
        };
      })
    );

    return new Response(
      JSON.stringify({
        year: yearNum,
        month: monthNum,
        blockedDates,
        events,
        properties: propertiesWithImages,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err: any) {
    console.error('Error fetching availability:', err);
    return new Response(
      JSON.stringify({ error: 'Failed to fetch availability', details: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
