/**
 * Reorder Property Images API
 * PUT /api/properties/[id]/images/reorder - Bulk update display order
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

// PUT /api/properties/[id]/images/reorder
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const data = await request.json();
    const { image_order } = data; // Array of { id, display_order }

    if (!image_order || !Array.isArray(image_order)) {
      return new Response(
        JSON.stringify({ error: 'image_order array is required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify property ownership
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(propertyId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if ((property as any).owner_id !== user.userId && user.role !== 'admin') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Update display order for each image
    for (const item of image_order) {
      if (item.id && item.display_order !== undefined) {
        await env.DB.prepare(
          'UPDATE property_image SET display_order = ? WHERE id = ? AND property_id = ?'
        )
          .bind(item.display_order, item.id, propertyId)
          .run();
      }
    }

    // Get updated images
    const images = await env.DB.prepare(
      'SELECT * FROM property_image WHERE property_id = ? ORDER BY display_order ASC'
    )
      .bind(propertyId)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Images reordered successfully',
        images: images.results || [],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Images Reorder] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to reorder images' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
