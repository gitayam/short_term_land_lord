# Stripe Payment Integration Setup Guide

This guide walks you through setting up Stripe payment processing for guest booking approvals.

## Why Stripe?

- **Trusted**: Industry-leading payment processor
- **Simple**: Payment Links eliminate complex frontend integration
- **Secure**: PCI DSS compliant, handles all sensitive data
- **Affordable**: 2.9% + $0.30 per transaction (US cards)
- **Feature-rich**: Built-in fraud protection, international payments, refunds

## Step 1: Create Stripe Account

1. Go to [https://dashboard.stripe.com/register](https://dashboard.stripe.com/register)
2. Sign up for a new Stripe account
3. Complete your business profile
4. Enable your account for live payments

## Step 2: Get API Keys

### Test Mode (Development)

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Click **Developers** → **API keys**
3. Copy your **Secret key** (starts with `sk_test_...`)
4. Keep this key secure - never commit to git!

### Live Mode (Production)

1. Toggle to **Live mode** in the Stripe dashboard
2. Go to **Developers** → **API keys**
3. Copy your **Secret key** (starts with `sk_live_...`)
4. Store securely in environment variables

## Step 3: Configure Cloudflare Environment Variables

Add Stripe credentials to **Cloudflare Dashboard → Pages → short-term-landlord → Settings → Environment Variables**:

### Production Environment:

```bash
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxxx
```

### Preview/Development Environment:

```bash
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
```

## Step 4: Test Payment Flow

### Manual Test:

1. Create a test booking request from the public booking form
2. As property owner, approve the booking request
3. Check that the approval email includes a payment link
4. Click the payment link (opens Stripe hosted checkout)
5. Use test card: `4242 4242 4242 4242`, any future expiry, any CVC
6. Complete payment and verify success

### Test Cards:

- **Successful payment**: `4242 4242 4242 4242`
- **Payment requires authentication**: `4000 0025 0000 3155`
- **Card declined**: `4000 0000 0000 9995`
- **Expired card**: `4000 0000 0000 0069`

More test cards: [https://stripe.com/docs/testing](https://stripe.com/docs/testing)

## Step 5: Webhook Setup (Optional but Recommended)

Webhooks allow Stripe to notify your app when payments succeed.

1. Go to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Endpoint URL: `https://short-term-landlord.pages.dev/api/webhooks/stripe`
4. Select events:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Copy the **Signing secret** (starts with `whsec_...`)
6. Add to Cloudflare environment variables:

```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx
```

## Step 6: Configure Property Pricing

Ensure your properties have pricing information:

1. Go to **Properties** in the admin dashboard
2. Edit each property
3. Set **Nightly Rate** (e.g., $150)
4. Set **Cleaning Fee** (e.g., $75)
5. Save changes

The total booking price will be calculated as:
```
Total = (Nightly Rate × Number of Nights) + Cleaning Fee
```

## Payment Flow Overview

Here's how the payment integration works:

```
1. Guest submits booking request
   ↓
2. Owner reviews and approves request
   ↓
3. System creates Stripe Payment Link
   - Amount = (nightly_rate × nights) + cleaning_fee
   - Link stored in database
   ↓
4. Email sent to guest with payment link
   ↓
5. Guest clicks link → Stripe hosted checkout
   ↓
6. Guest completes payment with card
   ↓
7. Stripe processes payment
   ↓
8. Payment record created in database
   ↓
9. Booking confirmed (calendar event created)
```

## Database Schema

### booking_request Table

Added payment tracking columns:
```sql
estimated_total         REAL    -- Total booking amount
deposit_amount          REAL    -- Optional deposit (future use)
payment_status          TEXT    -- pending, deposit_paid, fully_paid, refunded
stripe_payment_link     TEXT    -- Stripe Payment Link URL
stripe_payment_intent_id TEXT   -- Stripe Payment Intent/Link ID
```

### payment_transactions Table

Tracks all payment transactions:
```sql
id                       INTEGER PRIMARY KEY
transaction_type         TEXT    -- booking_payment, booking_deposit, refund
amount                   REAL
currency                 TEXT    -- USD, EUR, etc.
status                   TEXT    -- pending, processing, succeeded, failed
stripe_payment_intent_id TEXT
property_id              INTEGER
booking_request_id       INTEGER
calendar_event_id        INTEGER
description              TEXT
payment_date             TEXT
```

## Troubleshooting

### Issue: Payment link not generated

**Check:**
1. `STRIPE_SECRET_KEY` is set in Cloudflare environment variables
2. Key starts with `sk_test_` (test) or `sk_live_` (production)
3. Property has `nightly_rate` and `cleaning_fee` set
4. Check Cloudflare Functions logs for errors

### Issue: "Invalid API key"

**Solution:**
- Verify the API key is copied correctly (no spaces)
- Ensure you're using the Secret key, not Publishable key
- Check that test/live mode matches your key type

### Issue: Payment succeeds but booking not confirmed

**Solution:**
- Implement webhook handler (Step 5)
- Webhooks automatically update payment status
- Without webhooks, payment tracking is manual

### Issue: Email doesn't include payment link

**Solution:**
- Verify `STRIPE_SECRET_KEY` environment variable is set
- Check that Stripe payment link creation succeeded
- Review Cloudflare Functions logs for Stripe API errors

## Security Best Practices

1. **Never expose Secret keys**
   - Only store in environment variables
   - Never commit to git
   - Rotate keys every 90 days

2. **Use test mode for development**
   - Always test with test keys first
   - Only enable live mode when ready for production

3. **Verify webhook signatures**
   - Always validate webhook signatures
   - Prevents fraudulent webhook calls

4. **Monitor for fraud**
   - Enable Stripe Radar (built-in fraud detection)
   - Review failed payments regularly
   - Set up email alerts for disputes

5. **Secure your environment variables**
   - Use Cloudflare's encrypted environment variables
   - Restrict access to production credentials
   - Audit access logs regularly

## Cost Breakdown

**Stripe Standard Pricing (US):**
- 2.9% + $0.30 per successful transaction
- No monthly fees
- No setup fees
- No hidden costs

**Example Booking:**
- Booking total: $500
- Stripe fee: ($500 × 0.029) + $0.30 = $14.80
- You receive: $485.20

**Volume Discounts:**
- Contact Stripe for custom pricing at high volumes
- Typically available for >$80k/month in processing

## Additional Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Payment Links Guide](https://stripe.com/docs/payment-links)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Stripe Dashboard](https://dashboard.stripe.com)
- [Webhook Documentation](https://stripe.com/docs/webhooks)

## Support

If you encounter issues:
1. Check Cloudflare Functions logs for errors
2. Review Stripe Dashboard logs (Developers → Logs)
3. Test with Stripe test mode first
4. Contact Stripe support if payment processing issues

## What's Next?

After setting up Stripe:
1. ✅ Configure webhook handler for automated payment confirmation
2. ✅ Add deposit payment option (partial upfront, rest later)
3. ✅ Implement refund workflow for cancellations
4. ✅ Add payment reminders for unpaid bookings
5. ✅ Create payment receipt generation
