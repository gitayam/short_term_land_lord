/**
 * Upload Property Image to R2
 * POST /api/upload/property-image
 * Uploads property images to R2 bucket and stores reference in database
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';
import {
  parseFormData,
  uploadToR2,
  generateFileKey,
  isValidImageType,
  isValidFileSize,
  getPublicUrl,
} from '../../utils/storage';

const MAX_IMAGE_SIZE_MB = 10;

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    // Authenticate user
    const user = await requireAuth(request, env);

    // Parse form data
    const formData = await parseFormData(request);
    const file = formData.get('file') as File;
    const propertyIdStr = formData.get('property_id') as string;

    if (!file) {
      return new Response(
        JSON.stringify({ error: 'No file provided' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    if (!propertyIdStr) {
      return new Response(
        JSON.stringify({ error: 'property_id is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const propertyId = parseInt(propertyIdStr);

    // Verify property ownership
    const property = await env.DB.prepare(
      'SELECT id FROM property WHERE id = ? AND owner_id = ?'
    )
      .bind(propertyId, user.userId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found or access denied' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate file type
    if (!isValidImageType(file.type)) {
      return new Response(
        JSON.stringify({
          error: 'Invalid file type. Allowed: JPEG, PNG, GIF, WebP',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate file size
    if (!isValidFileSize(file.size, MAX_IMAGE_SIZE_MB)) {
      return new Response(
        JSON.stringify({
          error: `File size exceeds ${MAX_IMAGE_SIZE_MB}MB limit`,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Generate unique file key
    const fileKey = generateFileKey(
      `properties/${propertyId}/images`,
      file.name,
      user.userId
    );

    // Upload to R2
    const arrayBuffer = await file.arrayBuffer();
    await uploadToR2(env, fileKey, arrayBuffer, {
      contentType: file.type,
      customMetadata: {
        uploadedBy: user.userId.toString(),
        propertyId: propertyId.toString(),
        originalName: file.name,
        uploadDate: new Date().toISOString(),
      },
    });

    // Store reference in database (we'll add this table in next migration)
    // For now, we can store in property images table or return the URL
    const imageUrl = getPublicUrl(fileKey);

    // Cache the image URL in KV for faster access
    await env.KV.put(`property:${propertyId}:image:${fileKey}`, imageUrl, {
      expirationTtl: 86400 * 30, // 30 days
    });

    return new Response(
      JSON.stringify({
        success: true,
        file: {
          key: fileKey,
          url: imageUrl,
          size: file.size,
          type: file.type,
          propertyId,
        },
        message: 'Image uploaded successfully',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Upload Property Image] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to upload image',
        message: error.message,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
