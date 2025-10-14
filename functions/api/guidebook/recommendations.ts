/**
 * POST/PUT/DELETE /api/guidebook/recommendations
 * Manage local recommendations
 */

interface Env {
  DB: D1Database;
}

// POST - Create new recommendation
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { env, request } = context;

  try {
    const body = await request.json();
    const {
      property_id,
      category,
      name,
      description,
      address,
      phone,
      website,
      distance_miles,
      walking_time_minutes,
      price_level,
      rating,
      hours,
      tags,
      is_featured,
      display_order
    } = body;

    if (!property_id || !category || !name) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields (property_id, category, name)' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Serialize tags array to JSON
    const tagsJson = Array.isArray(tags) ? JSON.stringify(tags) : '[]';

    const result = await env.DB.prepare(`
      INSERT INTO guidebook_recommendations (
        property_id, category, name, description, address, phone, website,
        distance_miles, walking_time_minutes, price_level, rating,
        hours, tags, is_featured, display_order
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      property_id,
      category,
      name,
      description || '',
      address || '',
      phone || '',
      website || '',
      distance_miles || null,
      walking_time_minutes || null,
      price_level || null,
      rating || null,
      hours || '',
      tagsJson,
      is_featured ? 1 : 0,
      display_order || 999
    ).run();

    return new Response(
      JSON.stringify({
        success: true,
        id: result.meta.last_row_id,
        message: 'Recommendation created successfully'
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err: any) {
    console.error('Error creating recommendation:', err);
    return new Response(
      JSON.stringify({ error: 'Failed to create recommendation', details: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};

// PUT - Update recommendation
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { env, request } = context;

  try {
    const body = await request.json();
    const {
      id,
      category,
      name,
      description,
      address,
      phone,
      website,
      distance_miles,
      walking_time_minutes,
      price_level,
      rating,
      hours,
      tags,
      is_featured,
      display_order
    } = body;

    if (!id) {
      return new Response(
        JSON.stringify({ error: 'Recommendation ID required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Serialize tags array to JSON
    const tagsJson = Array.isArray(tags) ? JSON.stringify(tags) : '[]';

    await env.DB.prepare(`
      UPDATE guidebook_recommendations
      SET category = ?,
          name = ?,
          description = ?,
          address = ?,
          phone = ?,
          website = ?,
          distance_miles = ?,
          walking_time_minutes = ?,
          price_level = ?,
          rating = ?,
          hours = ?,
          tags = ?,
          is_featured = ?,
          display_order = ?
      WHERE id = ?
    `).bind(
      category,
      name,
      description,
      address,
      phone,
      website,
      distance_miles,
      walking_time_minutes,
      price_level,
      rating,
      hours,
      tagsJson,
      is_featured ? 1 : 0,
      display_order,
      id
    ).run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Recommendation updated successfully'
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err: any) {
    console.error('Error updating recommendation:', err);
    return new Response(
      JSON.stringify({ error: 'Failed to update recommendation', details: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};

// DELETE - Delete recommendation
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { env, request } = context;
  const url = new URL(request.url);
  const id = url.searchParams.get('id');

  if (!id) {
    return new Response(
      JSON.stringify({ error: 'Recommendation ID required' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  try {
    await env.DB.prepare(`
      DELETE FROM guidebook_recommendations WHERE id = ?
    `).bind(id).run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Recommendation deleted successfully'
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err: any) {
    console.error('Error deleting recommendation:', err);
    return new Response(
      JSON.stringify({ error: 'Failed to delete recommendation', details: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
