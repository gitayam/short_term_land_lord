/**
 * Cloudflare Pages Functions Middleware
 * Handles CORS, authentication, and logging for all API routes
 */

export interface Env {
  DB: D1Database;
  KV: KVNamespace;
  BUCKET: R2Bucket;
  JWT_SECRET?: string;
}

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*', // Configure this for production
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',
};

// Handle CORS preflight requests
export const onRequestOptions: PagesFunction<Env> = async () => {
  return new Response(null, {
    status: 204,
    headers: corsHeaders,
  });
};

// Global middleware for all requests
export const onRequest: PagesFunction<Env> = async (context) => {
  const { request } = context;

  console.log(`[${new Date().toISOString()}] ${request.method} ${new URL(request.url).pathname}`);

  // Handle preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: corsHeaders,
    });
  }

  // Continue to next middleware/handler
  const response = await context.next();

  // Add CORS headers to response
  const newResponse = new Response(response.body, response);
  Object.entries(corsHeaders).forEach(([key, value]) => {
    newResponse.headers.set(key, value);
  });

  return newResponse;
};
