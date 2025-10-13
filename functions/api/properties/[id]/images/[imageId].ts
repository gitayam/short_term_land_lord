/**
 * Property Image Detail API
 * PUT    /api/properties/[id]/images/[imageId] - Update image
 * DELETE /api/properties/[id]/images/[imageId] - Delete image
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

// PUT /api/properties/[id]/images/[imageId]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const imageId = params.imageId as string;
    const data = await request.json();

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

    // Verify image exists and belongs to property
    const image = await env.DB.prepare(
      'SELECT id FROM property_image WHERE id = ? AND property_id = ?'
    )
      .bind(imageId, propertyId)
      .first();

    if (!image) {
      return new Response(
        JSON.stringify({ error: 'Image not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // If setting as primary, unset other primary images
    if (data.is_primary === 1) {
      await env.DB.prepare(
        'UPDATE property_image SET is_primary = 0 WHERE property_id = ? AND id != ?'
      )
        .bind(propertyId, imageId)
        .run();
    }

    // Update image
    await env.DB.prepare(
      `UPDATE property_image SET
        caption = COALESCE(?, caption),
        display_order = COALESCE(?, display_order),
        is_primary = COALESCE(?, is_primary)
       WHERE id = ?`
    )
      .bind(
        data.caption !== undefined ? data.caption : null,
        data.display_order !== undefined ? data.display_order : null,
        data.is_primary !== undefined ? data.is_primary : null,
        imageId
      )
      .run();

    // Get updated image
    const updated = await env.DB.prepare(
      'SELECT * FROM property_image WHERE id = ?'
    )
      .bind(imageId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        image: updated,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Image PUT] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to update image' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/properties/[id]/images/[imageId]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const imageId = params.imageId as string;

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

    // Verify image exists and belongs to property
    const image = await env.DB.prepare(
      'SELECT id FROM property_image WHERE id = ? AND property_id = ?'
    )
      .bind(imageId, propertyId)
      .first();

    if (!image) {
      return new Response(
        JSON.stringify({ error: 'Image not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Delete image
    await env.DB.prepare('DELETE FROM property_image WHERE id = ?')
      .bind(imageId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Image deleted successfully',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Image DELETE] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to delete image' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
