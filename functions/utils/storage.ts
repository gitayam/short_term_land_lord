/**
 * Storage Utilities for R2
 * File upload, download, and management
 */

import { Env } from '../_middleware';

/**
 * Upload file to R2 bucket
 */
export async function uploadToR2(
  env: Env,
  key: string,
  data: ArrayBuffer | ReadableStream,
  metadata?: {
    contentType?: string;
    customMetadata?: Record<string, string>;
  }
): Promise<void> {
  await env.BUCKET.put(key, data, {
    httpMetadata: {
      contentType: metadata?.contentType || 'application/octet-stream',
      cacheControl: 'public, max-age=31536000', // 1 year for immutable files
    },
    customMetadata: metadata?.customMetadata,
  });
}

/**
 * Get file from R2 bucket
 */
export async function getFromR2(env: Env, key: string): Promise<R2ObjectBody | null> {
  return await env.BUCKET.get(key);
}

/**
 * Delete file from R2 bucket
 */
export async function deleteFromR2(env: Env, key: string): Promise<void> {
  await env.BUCKET.delete(key);
}

/**
 * Generate a unique file key for R2
 */
export function generateFileKey(
  prefix: string,
  filename: string,
  userId?: number
): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  const sanitized = filename.replace(/[^a-zA-Z0-9.-]/g, '_');

  if (userId) {
    return `${prefix}/${userId}/${timestamp}-${random}-${sanitized}`;
  }

  return `${prefix}/${timestamp}-${random}-${sanitized}`;
}

/**
 * Validate file type for images
 */
export function isValidImageType(contentType: string): boolean {
  const validTypes = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/heic',
  ];
  return validTypes.includes(contentType.toLowerCase());
}

/**
 * Validate file type for videos
 */
export function isValidVideoType(contentType: string): boolean {
  const validTypes = [
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'video/webm',
  ];
  return validTypes.includes(contentType.toLowerCase());
}

/**
 * Get file extension from content type
 */
export function getExtensionFromContentType(contentType: string): string {
  const map: { [key: string]: string } = {
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'image/webp': 'webp',
    'video/mp4': 'mp4',
    'video/quicktime': 'mov',
    'video/webm': 'webm',
  };
  return map[contentType.toLowerCase()] || 'bin';
}

/**
 * Validate file size (in bytes)
 */
export function isValidFileSize(size: number, maxSizeMB: number = 10): boolean {
  const maxBytes = maxSizeMB * 1024 * 1024;
  return size <= maxBytes;
}

/**
 * Parse multipart form data for file uploads
 */
export async function parseFormData(request: Request): Promise<FormData> {
  const contentType = request.headers.get('content-type') || '';

  if (!contentType.includes('multipart/form-data')) {
    throw new Error('Content-Type must be multipart/form-data');
  }

  return await request.formData();
}

/**
 * Get public URL for R2 object
 * Note: This requires R2 bucket to be configured with public access or custom domain
 */
export function getPublicUrl(key: string, customDomain?: string): string {
  if (customDomain) {
    return `https://${customDomain}/${key}`;
  }
  // Default R2 URL format (requires public bucket)
  return `https://files.yourdomain.com/${key}`;
}
