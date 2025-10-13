/**
 * Property Images API
 * GET  /api/properties/[id]/images - List all images for property
 * POST /api/properties/[id]/images - Upload new image
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

interface PropertyImage {
  id: string;
  property_id: string;
  image_url: string;
  caption: string | null;
  display_order: number;
  is_primary: number;
  uploaded_at: string;
}

// GET /api/properties/[id]/images
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;

    // Verify property access
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

    // Check access
    const hasAccess =
      (property as any).owner_id === user.userId ||
      user.role === 'admin' ||
      user.role === 'property_manager';

    if (!hasAccess) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get all images for property
    const images = await env.DB.prepare(
      'SELECT * FROM property_image WHERE property_id = ? ORDER BY display_order ASC, uploaded_at ASC'
    )
      .bind(propertyId)
      .all<PropertyImage>();

    return new Response(
      JSON.stringify({
        success: true,
        images: images.results || [],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Images GET] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to fetch images' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/properties/[id]/images
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const data = await request.json();
    const { image_url, caption, is_primary = 0 } = data;

    if (!image_url) {
      return new Response(
        JSON.stringify({ error: 'image_url is required' }),
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

    // Get current max display_order
    const maxOrder = await env.DB.prepare(
      'SELECT MAX(display_order) as max_order FROM property_image WHERE property_id = ?'
    )
      .bind(propertyId)
      .first();

    const displayOrder = ((maxOrder as any)?.max_order || 0) + 1;

    // If is_primary, unset other primary images
    if (is_primary === 1) {
      await env.DB.prepare(
        'UPDATE property_image SET is_primary = 0 WHERE property_id = ?'
      )
        .bind(propertyId)
        .run();
    }

    // Insert new image
    await env.DB.prepare(
      `INSERT INTO property_image (property_id, image_url, caption, display_order, is_primary)
       VALUES (?, ?, ?, ?, ?)`
    )
      .bind(propertyId, image_url, caption || null, displayOrder, is_primary)
      .run();

    // Get the created image
    const created = await env.DB.prepare(
      'SELECT * FROM property_image WHERE property_id = ? AND image_url = ? ORDER BY uploaded_at DESC LIMIT 1'
    )
      .bind(propertyId, image_url)
      .first<PropertyImage>();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Image added successfully',
        image: created,
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Images POST] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to add image' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
