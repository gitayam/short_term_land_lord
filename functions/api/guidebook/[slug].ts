/**
 * GET /api/guidebook/:slug
 * Returns guidebook sections and recommendations for a property
 */

interface Env {
  DB: D1Database;
}

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { env, params } = context;
  const slug = params.slug as string;

  if (!slug) {
    return new Response(
      JSON.stringify({ error: 'Property slug required' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  try {
    // Get property by slug (or fallback to ID for backwards compatibility)
    const { results: properties } = await env.DB.prepare(`
      SELECT id, slug, name, address, city, state
      FROM property
      WHERE slug = ? OR CAST(id AS TEXT) = ?
      LIMIT 1
    `).bind(slug, slug).all();

    const property = properties?.[0];
    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get guidebook sections
    const { results: sections } = await env.DB.prepare(`
      SELECT id, section_type, title, content, display_order, icon, is_published
      FROM guidebook_sections
      WHERE property_id = ? AND is_published = 1
      ORDER BY display_order ASC
    `).bind(property.id).all();

    // Get recommendations
    const { results: recommendations } = await env.DB.prepare(`
      SELECT
        id, category, name, description, address, phone, website,
        distance_miles, walking_time_minutes, price_level, rating,
        hours, tags, image_url, is_featured, display_order
      FROM guidebook_recommendations
      WHERE property_id = ?
      ORDER BY is_featured DESC, display_order ASC, category ASC
    `).bind(property.id).all();

    // Group recommendations by category
    const recommendationsByCategory: Record<string, any[]> = {};
    (recommendations || []).forEach((rec: any) => {
      const category = rec.category || 'other';
      if (!recommendationsByCategory[category]) {
        recommendationsByCategory[category] = [];
      }
      // Parse tags JSON
      if (rec.tags) {
        try {
          rec.tags = JSON.parse(rec.tags);
        } catch (e) {
          rec.tags = [];
        }
      }
      recommendationsByCategory[category].push(rec);
    });

    return new Response(
      JSON.stringify({
        property: {
          id: property.id,
          slug: property.slug,
          name: property.name,
          address: property.address,
          city: property.city,
          state: property.state,
        },
        sections: sections || [],
        recommendations: recommendationsByCategory,
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'public, max-age=300', // Cache for 5 minutes
        }
      }
    );
  } catch (err: any) {
    console.error('Error fetching guidebook:', err);
    return new Response(
      JSON.stringify({ error: 'Failed to fetch guidebook', details: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
