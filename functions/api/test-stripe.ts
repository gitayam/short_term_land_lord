/**
 * Test Stripe Integration Endpoint
 * GET /api/test-stripe - Verify Stripe credentials are configured
 *
 * IMPORTANT: Remove this endpoint before production deployment!
 */

import { Env } from '../_middleware';
import { requireAuth } from '../utils/auth';
import { createStripePaymentLink } from '../utils/stripe';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    // Require authentication for security
    const user = await requireAuth(request, env);

    // Only allow admin users to test
    if (user.role !== 'admin') {
      return new Response(
        JSON.stringify({ error: 'Admin access required' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check if Stripe key is configured
    if (!env.STRIPE_SECRET_KEY) {
      return new Response(
        JSON.stringify({
          success: false,
          error: 'STRIPE_SECRET_KEY not configured in environment variables',
          message: 'Please add STRIPE_SECRET_KEY to Cloudflare Pages Settings → Environment Variables',
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify key format
    const keyPrefix = env.STRIPE_SECRET_KEY.substring(0, 8);
    const isTestMode = env.STRIPE_SECRET_KEY.startsWith('sk_test_');
    const isLiveMode = env.STRIPE_SECRET_KEY.startsWith('sk_live_');

    if (!isTestMode && !isLiveMode) {
      return new Response(
        JSON.stringify({
          success: false,
          error: 'Invalid Stripe API key format',
          message: 'Key should start with sk_test_ or sk_live_',
          keyPrefix,
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Test payment link creation
    console.log('[Stripe Test] Testing payment link creation...');

    const testResult = await createStripePaymentLink(
      {
        amount: 500, // $500 test booking
        currency: 'usd',
        description: 'Test Booking - Fayetteville Property (2025-03-15 to 2025-03-18)',
        customerEmail: 'test@example.com',
        customerName: 'Test Guest',
        metadata: {
          test: 'true',
          booking_request_id: 'test_123',
          property_id: 'test_prop_1',
        },
        successUrl: `${new URL(request.url).origin}/booking-success`,
      },
      { apiKey: env.STRIPE_SECRET_KEY }
    );

    if (!testResult.success) {
      return new Response(
        JSON.stringify({
          success: false,
          error: 'Payment link creation failed',
          details: testResult.error,
          mode: isTestMode ? 'test' : 'live',
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: '✅ Stripe integration is working!',
        mode: isTestMode ? 'test' : 'live',
        keyPrefix,
        paymentLink: testResult.paymentLink,
        instructions: {
          '1': 'Create a test booking request in your app',
          '2': 'Approve it as a property owner',
          '3': 'Check the approval email for the payment link',
          '4': 'Test payment with card: 4242 4242 4242 4242',
        },
        warning: isLiveMode ? '⚠️ LIVE MODE: This will create real payment links!' : null,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Stripe Test] Error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message || 'Test failed',
        stack: error.stack,
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
