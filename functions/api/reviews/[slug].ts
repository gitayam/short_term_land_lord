/**
 * GET /api/reviews/:slug
 * Returns reviews for a property
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
      SELECT id, slug, name, average_rating, total_reviews
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

    // Get reviews
    const { results: reviews } = await env.DB.prepare(`
      SELECT
        id, guest_name, rating, title, comment,
        cleanliness_rating, communication_rating, accuracy_rating,
        location_rating, value_rating,
        created_at, host_response, host_response_date
      FROM property_reviews
      WHERE property_id = ? AND is_published = 1
      ORDER BY created_at DESC
    `).bind(property.id).all();

    // Calculate category averages
    const categoryAverages: Record<string, number> = {
      cleanliness: 0,
      communication: 0,
      accuracy: 0,
      location: 0,
      value: 0
    };

    let categoryCount = 0;
    (reviews || []).forEach((review: any) => {
      if (review.cleanliness_rating) {
        categoryAverages.cleanliness += review.cleanliness_rating;
        categoryCount++;
      }
      if (review.communication_rating) {
        categoryAverages.communication += review.communication_rating;
      }
      if (review.accuracy_rating) {
        categoryAverages.accuracy += review.accuracy_rating;
      }
      if (review.location_rating) {
        categoryAverages.location += review.location_rating;
      }
      if (review.value_rating) {
        categoryAverages.value += review.value_rating;
      }
    });

    if (categoryCount > 0) {
      Object.keys(categoryAverages).forEach(key => {
        categoryAverages[key] = Number((categoryAverages[key] / categoryCount).toFixed(2));
      });
    }

    // Calculate rating distribution
    const ratingDistribution = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
    (reviews || []).forEach((review: any) => {
      const rating = Math.floor(review.rating);
      if (rating >= 1 && rating <= 5) {
        ratingDistribution[rating as keyof typeof ratingDistribution]++;
      }
    });

    return new Response(
      JSON.stringify({
        property: {
          id: property.id,
          slug: property.slug,
          name: property.name,
          average_rating: property.average_rating,
          total_reviews: property.total_reviews,
        },
        reviews: reviews || [],
        categoryAverages,
        ratingDistribution,
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
    console.error('Error fetching reviews:', err);
    return new Response(
      JSON.stringify({ error: 'Failed to fetch reviews', details: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
