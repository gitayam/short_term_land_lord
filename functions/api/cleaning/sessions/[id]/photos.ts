/**
 * Cleaning Session Photos/Videos Endpoint
 * GET /api/cleaning/sessions/[id]/photos - Get all media for session
 * POST /api/cleaning/sessions/[id]/photos - Upload photos/videos to R2
 * DELETE /api/cleaning/sessions/[id]/photos?key=... - Delete specific media
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';
import {
  parseFormData,
  uploadToR2,
  generateFileKey,
  isValidImageType,
  isValidVideoType,
  isValidFileSize,
  getPublicUrl,
  deleteFromR2,
} from '../../../../utils/storage';

const MAX_IMAGE_SIZE_MB = 10;
const MAX_VIDEO_SIZE_MB = 100;

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const sessionId = params.id;

    if (!sessionId) {
      return new Response(
        JSON.stringify({ error: 'Session ID is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify session exists and user has access
    const session = await env.DB.prepare(
      'SELECT cs.*, p.owner_id FROM cleaning_session cs LEFT JOIN property p ON cs.property_id = p.id WHERE cs.id = ?'
    )
      .bind(sessionId)
      .first();

    if (!session) {
      return new Response(
        JSON.stringify({ error: 'Cleaning session not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify access
    const hasAccess =
      user.role === 'admin' ||
      session.cleaner_id === user.userId ||
      session.owner_id === user.userId;

    if (!hasAccess) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get media list from KV
    const mediaKey = `cleaning-session:${sessionId}:media`;
    const media = await env.KV.get(mediaKey, { type: 'json' });

    return new Response(
      JSON.stringify({
        success: true,
        session_id: sessionId,
        media: media || [],
        count: (media as any[])?.length || 0,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Cleaning Session Photos] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to fetch session photos',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const sessionId = params.id;

    if (!sessionId) {
      return new Response(
        JSON.stringify({ error: 'Session ID is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Parse form data
    const formData = await parseFormData(request);
    const file = formData.get('file') as File;
    const photoType = formData.get('photo_type') as string; // 'before', 'after', 'issue', 'general'

    if (!file) {
      return new Response(
        JSON.stringify({ error: 'No file provided' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify session exists and user has access
    const session = await env.DB.prepare(
      'SELECT cs.*, p.owner_id FROM cleaning_session cs LEFT JOIN property p ON cs.property_id = p.id WHERE cs.id = ?'
    )
      .bind(sessionId)
      .first();

    if (!session) {
      return new Response(
        JSON.stringify({ error: 'Cleaning session not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify user is the cleaner or has admin/owner permissions
    const canUpload =
      user.role === 'admin' ||
      session.cleaner_id === user.userId ||
      session.owner_id === user.userId;

    if (!canUpload) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate file type
    const isImage = isValidImageType(file.type);
    const isVideo = isValidVideoType(file.type);

    if (!isImage && !isVideo) {
      return new Response(
        JSON.stringify({
          error: 'Invalid file type. Allowed: Images (JPEG, PNG, GIF, WebP, HEIC) or Videos (MP4, MOV, WebM)',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate file size
    const maxSize = isImage ? MAX_IMAGE_SIZE_MB : MAX_VIDEO_SIZE_MB;
    if (!isValidFileSize(file.size, maxSize)) {
      return new Response(
        JSON.stringify({
          error: `File size exceeds ${maxSize}MB limit`,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Generate unique file key
    const fileKey = generateFileKey(
      `cleaning-sessions/${sessionId}/${photoType || 'general'}`,
      file.name,
      user.userId
    );

    // Upload to R2
    const arrayBuffer = await file.arrayBuffer();
    await uploadToR2(env, fileKey, arrayBuffer, {
      contentType: file.type,
      customMetadata: {
        uploadedBy: user.userId.toString(),
        sessionId: sessionId.toString(),
        propertyId: session.property_id.toString(),
        photoType: photoType || 'general',
        originalName: file.name,
        uploadDate: new Date().toISOString(),
      },
    });

    // Get public URL
    const fileUrl = getPublicUrl(fileKey);

    // Update media list in KV
    const mediaKey = `cleaning-session:${sessionId}:media`;
    const existingMedia = (await env.KV.get(mediaKey, { type: 'json' })) || [];

    const newMediaItem = {
      key: fileKey,
      url: fileUrl,
      type: isImage ? 'image' : 'video',
      photoType: photoType || 'general',
      size: file.size,
      contentType: file.type,
      uploadedBy: user.userId,
      uploadedAt: new Date().toISOString(),
      originalName: file.name,
    };

    const updatedMedia = [...(existingMedia as any[]), newMediaItem];

    await env.KV.put(mediaKey, JSON.stringify(updatedMedia), {
      expirationTtl: 86400 * 365, // 1 year
    });

    return new Response(
      JSON.stringify({
        success: true,
        file: newMediaItem,
        message: 'Media uploaded successfully',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Cleaning Session Photos] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to upload media',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const sessionId = params.id;
    const url = new URL(request.url);
    const fileKey = url.searchParams.get('key');

    if (!sessionId || !fileKey) {
      return new Response(
        JSON.stringify({ error: 'Session ID and file key are required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify session exists and user has access
    const session = await env.DB.prepare(
      'SELECT cs.*, p.owner_id FROM cleaning_session cs LEFT JOIN property p ON cs.property_id = p.id WHERE cs.id = ?'
    )
      .bind(sessionId)
      .first();

    if (!session) {
      return new Response(
        JSON.stringify({ error: 'Cleaning session not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Only admin or property owner can delete media
    const canDelete = user.role === 'admin' || session.owner_id === user.userId;

    if (!canDelete) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Delete from R2
    await deleteFromR2(env, fileKey);

    // Update media list in KV
    const mediaKey = `cleaning-session:${sessionId}:media`;
    const existingMedia = (await env.KV.get(mediaKey, { type: 'json' })) || [];
    const updatedMedia = (existingMedia as any[]).filter(
      (item) => item.key !== fileKey
    );

    await env.KV.put(mediaKey, JSON.stringify(updatedMedia), {
      expirationTtl: 86400 * 365,
    });

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Media deleted successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Cleaning Session Photos] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to delete media',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
