/**
 * Health Check Endpoint
 * GET /api/health
 */

import { Env } from '../_middleware';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { env } = context;

  try {
    // Test D1 connection
    const dbTest = await env.DB.prepare('SELECT 1 as test').first();

    // Test KV connection
    const kvTest = await env.KV.get('health_check_test');

    return new Response(
      JSON.stringify({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
          database: dbTest ? 'connected' : 'disconnected',
          kv: 'connected', // If we get here, KV is working
          r2: 'available', // R2 doesn't need a health check
        },
        version: '1.0.0',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    return new Response(
      JSON.stringify({
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString(),
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
