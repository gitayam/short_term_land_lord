/**
 * Image Upload API
 * POST /api/upload/image - Upload image to R2 bucket
 * Returns the public URL of the uploaded image
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// Max file size: 10MB
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// Allowed image types
const ALLOWED_TYPES = [
  'image/jpeg',
  'image/jpg',
  'image/png',
  'image/gif',
  'image/webp',
];

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Check if R2 bucket is available
    if (!env.BUCKET) {
      return new Response(
        JSON.stringify({ error: 'File storage not configured' }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Parse multipart form data
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const category = formData.get('category') as string; // e.g., 'repair', 'property', 'profile'
    const relatedId = formData.get('related_id') as string;

    if (!file) {
      return new Response(
        JSON.stringify({ error: 'No file provided' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Validate file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return new Response(
        JSON.stringify({
          error: 'Invalid file type',
          allowed: ALLOWED_TYPES,
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      return new Response(
        JSON.stringify({
          error: 'File too large',
          max_size: MAX_FILE_SIZE,
          your_size: file.size,
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Generate unique filename
    const timestamp = Date.now();
    const randomStr = Math.random().toString(36).substring(2, 15);
    const extension = file.name.split('.').pop() || 'jpg';
    const filename = `${category || 'general'}/${user.userId}/${timestamp}-${randomStr}.${extension}`;

    // Upload to R2
    const fileBuffer = await file.arrayBuffer();
    await env.BUCKET.put(filename, fileBuffer, {
      httpMetadata: {
        contentType: file.type,
      },
      customMetadata: {
        uploadedBy: user.userId.toString(),
        originalName: file.name,
        category: category || 'general',
        relatedId: relatedId || '',
        uploadedAt: new Date().toISOString(),
      },
    });

    // Generate public URL
    // Note: For production, configure R2 custom domain in wrangler.toml or use Cloudflare Images
    // For now, we'll use a relative path that will be served by a worker endpoint
    const publicUrl = `/api/files/${filename}`;

    return new Response(
      JSON.stringify({
        success: true,
        url: publicUrl,
        filename,
        size: file.size,
        type: file.type,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Upload] Image upload error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to upload image' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
