/**
 * Create Payment Intent
 * POST /api/create-payment-intent - Create Stripe Payment Intent for booking
 */

import { Env } from '../_middleware';

interface PaymentIntentRequest {
  amount: number;
  currency?: string;
  property_id: string;
  check_in_date: string;
  check_out_date: string;
}

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    if (!env.STRIPE_SECRET_KEY) {
      return new Response(
        JSON.stringify({ error: 'Stripe not configured' }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const data: PaymentIntentRequest = await request.json();
    const { amount, currency = 'usd', property_id, check_in_date, check_out_date } = data;

    if (!amount || !property_id || !check_in_date || !check_out_date) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Convert amount to cents
    const amountInCents = Math.round(amount * 100);

    // Create Payment Intent
    const response = await fetch('https://api.stripe.com/v1/payment_intents', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.STRIPE_SECRET_KEY}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        amount: amountInCents.toString(),
        currency,
        'automatic_payment_methods[enabled]': 'true',
        'capture_method': 'manual', // Important: Don't charge until approved
        'metadata[property_id]': property_id,
        'metadata[check_in_date]': check_in_date,
        'metadata[check_out_date]': check_out_date,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('[Payment Intent] Stripe error:', error);
      return new Response(
        JSON.stringify({ error: 'Failed to create payment intent', details: error }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const paymentIntent = await response.json();

    return new Response(
      JSON.stringify({
        success: true,
        clientSecret: paymentIntent.client_secret,
        paymentIntentId: paymentIntent.id,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Payment Intent] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to create payment intent' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
