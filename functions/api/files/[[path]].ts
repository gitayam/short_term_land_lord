/**
 * File Serving API
 * GET /api/files/[...path] - Serve files from R2 bucket
 * This endpoint serves uploaded files from R2 storage
 */

import { Env } from '../../_middleware';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, env } = context;

  try {
    // Check if R2 bucket is available
    if (!env.BUCKET) {
      return new Response('File storage not configured', { status: 500 });
    }

    // Get the file path from URL params
    const path = (params.path as string[])?.join('/') || '';

    if (!path) {
      return new Response('File path required', { status: 400 });
    }

    // Fetch file from R2
    const object = await env.BUCKET.get(path);

    if (!object) {
      return new Response('File not found', { status: 404 });
    }

    // Get file metadata
    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set('etag', object.httpEtag);

    // Add cache headers for better performance
    headers.set('Cache-Control', 'public, max-age=31536000'); // Cache for 1 year
    headers.set('Access-Control-Allow-Origin', '*'); // Allow CORS for images

    return new Response(object.body, {
      headers,
    });
  } catch (error: any) {
    console.error('[Files] Serve error:', error);
    return new Response(
      error.message || 'Failed to serve file',
      { status: 500 }
    );
  }
};
