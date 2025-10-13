/**
 * Property Image Upload API
 * POST /api/properties/[id]/images/upload - Upload image file
 *
 * For MVP: Accepts image URLs or base64 data
 * Future: Direct R2 upload with presigned URLs
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

// POST /api/properties/[id]/images/upload
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;

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

    const contentType = request.headers.get('content-type') || '';

    // Handle multipart form data (actual file upload)
    if (contentType.includes('multipart/form-data')) {
      const formData = await request.formData();
      const file = formData.get('image') as File;

      if (!file) {
        return new Response(
          JSON.stringify({ error: 'No image file provided' }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // Validate file type
      if (!file.type.startsWith('image/')) {
        return new Response(
          JSON.stringify({ error: 'File must be an image' }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        return new Response(
          JSON.stringify({ error: 'Image must be less than 10MB' }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // Check if R2 bucket is available
      if (!env.BUCKET) {
        return new Response(
          JSON.stringify({ error: 'File storage not configured' }),
          { status: 500, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // Upload to R2 instead of base64
      const timestamp = Date.now();
      const randomStr = Math.random().toString(36).substring(2, 15);
      const extension = file.name.split('.').pop() || 'jpg';
      const filename = `properties/${propertyId}/images/${timestamp}-${randomStr}.${extension}`;

      const fileBuffer = await file.arrayBuffer();
      await env.BUCKET.put(filename, fileBuffer, {
        httpMetadata: {
          contentType: file.type,
        },
        customMetadata: {
          uploadedBy: user.userId.toString(),
          propertyId: propertyId,
          originalName: file.name,
          uploadedAt: new Date().toISOString(),
        },
      });

      // Generate URL for serving via /api/files/
      const imageUrl = `/api/files/${filename}`;

      // Get current max display_order
      const maxOrder = await env.DB.prepare(
        'SELECT MAX(display_order) as max_order FROM property_image WHERE property_id = ?'
      )
        .bind(propertyId)
        .first();

      const displayOrder = ((maxOrder as any)?.max_order || 0) + 1;

      // Check if this is the first image (auto-set as primary)
      const imageCount = await env.DB.prepare(
        'SELECT COUNT(*) as count FROM property_image WHERE property_id = ?'
      )
        .bind(propertyId)
        .first();

      const isPrimary = ((imageCount as any)?.count || 0) === 0 ? 1 : 0;

      // Insert image record
      await env.DB.prepare(
        `INSERT INTO property_image (property_id, image_url, display_order, is_primary)
         VALUES (?, ?, ?, ?)`
      )
        .bind(propertyId, imageUrl, displayOrder, isPrimary)
        .run();

      // Get the created image
      const created = await env.DB.prepare(
        'SELECT * FROM property_image WHERE property_id = ? ORDER BY uploaded_at DESC LIMIT 1'
      )
        .bind(propertyId)
        .first();

      return new Response(
        JSON.stringify({
          success: true,
          message: 'Image uploaded successfully',
          image: created,
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Handle JSON with image URL
    const data = await request.json();
    const { image_url, caption } = data;

    if (!image_url) {
      return new Response(
        JSON.stringify({ error: 'image_url is required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Validate URL format
    try {
      new URL(image_url);
    } catch {
      return new Response(
        JSON.stringify({ error: 'Invalid image URL' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get current max display_order
    const maxOrder = await env.DB.prepare(
      'SELECT MAX(display_order) as max_order FROM property_image WHERE property_id = ?'
    )
      .bind(propertyId)
      .first();

    const displayOrder = ((maxOrder as any)?.max_order || 0) + 1;

    // Check if this is the first image
    const imageCount = await env.DB.prepare(
      'SELECT COUNT(*) as count FROM property_image WHERE property_id = ?'
    )
      .bind(propertyId)
      .first();

    const isPrimary = ((imageCount as any)?.count || 0) === 0 ? 1 : 0;

    // Insert image record
    await env.DB.prepare(
      `INSERT INTO property_image (property_id, image_url, caption, display_order, is_primary)
       VALUES (?, ?, ?, ?, ?)`
    )
      .bind(propertyId, image_url, caption || null, displayOrder, isPrimary)
      .run();

    // Get the created image
    const created = await env.DB.prepare(
      'SELECT * FROM property_image WHERE property_id = ? ORDER BY uploaded_at DESC LIMIT 1'
    )
      .bind(propertyId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Image added successfully',
        image: created,
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Image Upload] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to upload image' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
