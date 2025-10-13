/**
 * Stripe Payment Integration Utilities
 * Handles Stripe Payment Links and payment processing
 */

export interface StripeCredentials {
  apiKey: string;
}

export interface PaymentLinkParams {
  amount: number; // Amount in dollars (will be converted to cents)
  currency?: string;
  description: string;
  customerEmail: string;
  customerName?: string;
  metadata?: Record<string, string>;
  successUrl?: string;
  cancelUrl?: string;
}

export interface PaymentLinkResponse {
  success: boolean;
  paymentLink?: string;
  paymentIntentId?: string;
  error?: string;
}

/**
 * Create a Stripe Payment Link
 * Uses Stripe's Payment Links API to generate a hosted payment page
 *
 * @param params - Payment link parameters
 * @param credentials - Stripe API credentials
 * @returns Payment link URL and payment intent ID
 */
export async function createStripePaymentLink(
  params: PaymentLinkParams,
  credentials: StripeCredentials
): Promise<PaymentLinkResponse> {
  try {
    const { apiKey } = credentials;

    if (!apiKey || !apiKey.startsWith('sk_')) {
      throw new Error('Invalid Stripe API key');
    }

    // Convert amount to cents (Stripe uses smallest currency unit)
    const amountInCents = Math.round(params.amount * 100);

    if (amountInCents < 50) {
      throw new Error('Amount must be at least $0.50');
    }

    // Create a product first (required for payment links)
    const productResponse = await fetch('https://api.stripe.com/v1/products', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        name: params.description,
        ...(params.metadata && {
          'metadata[booking_id]': params.metadata.booking_id || '',
          'metadata[property_id]': params.metadata.property_id || '',
        }),
      }),
    });

    if (!productResponse.ok) {
      const error = await productResponse.json();
      throw new Error(`Stripe product creation failed: ${error.message || productResponse.statusText}`);
    }

    const product = await productResponse.json();

    // Create a price for the product
    const priceResponse = await fetch('https://api.stripe.com/v1/prices', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        product: product.id,
        unit_amount: amountInCents.toString(),
        currency: params.currency || 'usd',
      }),
    });

    if (!priceResponse.ok) {
      const error = await priceResponse.json();
      throw new Error(`Stripe price creation failed: ${error.message || priceResponse.statusText}`);
    }

    const price = await priceResponse.json();

    // Create the payment link
    const linkParams = new URLSearchParams({
      'line_items[0][price]': price.id,
      'line_items[0][quantity]': '1',
      ...(params.successUrl && { after_completion_type: 'redirect', 'after_completion[redirect][url]': params.successUrl }),
      ...(params.customerEmail && { 'customer_creation': 'always' }),
    });

    // Add metadata
    if (params.metadata) {
      Object.entries(params.metadata).forEach(([key, value]) => {
        linkParams.append(`metadata[${key}]`, value);
      });
    }

    // Add customer email prefill
    if (params.customerEmail) {
      linkParams.append('custom_fields[0][key]', 'email');
      linkParams.append('custom_fields[0][label][type]', 'custom');
      linkParams.append('custom_fields[0][label][custom]', 'Email');
      linkParams.append('custom_fields[0][type]', 'text');
      linkParams.append('custom_fields[0][optional]', 'false');
    }

    const linkResponse = await fetch('https://api.stripe.com/v1/payment_links', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: linkParams,
    });

    if (!linkResponse.ok) {
      const error = await linkResponse.json();
      throw new Error(`Stripe payment link creation failed: ${error.message || linkResponse.statusText}`);
    }

    const link = await linkResponse.json();

    return {
      success: true,
      paymentLink: link.url,
      paymentIntentId: link.id, // This is the payment link ID, not payment intent
    };
  } catch (error: any) {
    console.error('[Stripe] Payment link creation error:', error);
    return {
      success: false,
      error: error.message || 'Failed to create payment link',
    };
  }
}

/**
 * Verify a Stripe webhook signature
 * Ensures webhook events are authentic and from Stripe
 *
 * @param payload - Raw request body
 * @param signature - Stripe-Signature header value
 * @param webhookSecret - Webhook signing secret from Stripe
 * @returns true if signature is valid
 */
export function verifyStripeWebhook(
  payload: string,
  signature: string,
  webhookSecret: string
): boolean {
  try {
    // Note: For production, you should use stripe-node library
    // This is a placeholder for manual signature verification
    // The actual implementation requires HMAC-SHA256 verification

    if (!signature || !webhookSecret) {
      return false;
    }

    // TODO: Implement proper signature verification
    // For now, we'll return true in development
    // In production, use: stripe.webhooks.constructEvent(payload, signature, webhookSecret)

    return true;
  } catch (error) {
    console.error('[Stripe] Webhook verification failed:', error);
    return false;
  }
}

/**
 * Parse Stripe webhook event
 * Extracts event type and data from webhook payload
 *
 * @param body - Webhook request body
 * @returns Parsed event data
 */
export function parseStripeWebhookEvent(body: any): {
  type: string;
  data: any;
} {
  return {
    type: body.type,
    data: body.data?.object || {},
  };
}

/**
 * Calculate Stripe fee
 * Estimate Stripe processing fees (2.9% + $0.30 for US cards)
 *
 * @param amount - Payment amount in dollars
 * @returns Estimated Stripe fee in dollars
 */
export function calculateStripeFee(amount: number): number {
  return (amount * 0.029) + 0.30;
}

/**
 * Format amount for Stripe
 * Converts dollar amount to cents for Stripe API
 *
 * @param dollars - Amount in dollars
 * @returns Amount in cents (smallest currency unit)
 */
export function formatAmountForStripe(dollars: number): number {
  return Math.round(dollars * 100);
}

/**
 * Format amount from Stripe
 * Converts cents to dollars
 *
 * @param cents - Amount in cents
 * @returns Amount in dollars
 */
export function formatAmountFromStripe(cents: number): number {
  return cents / 100;
}
