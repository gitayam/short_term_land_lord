/**
 * Test Stripe Integration
 * This script tests if the Stripe payment link generation works
 */

// Simulate the createStripePaymentLink function
async function testStripePaymentLink(apiKey) {
  console.log('🔐 Testing Stripe API key...');
  console.log('📝 API Key prefix:', apiKey.substring(0, 12) + '...');

  try {
    // Test 1: Create a test product
    console.log('\n1️⃣ Creating test product...');
    const productResponse = await fetch('https://api.stripe.com/v1/products', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        name: 'Test Booking - Fayetteville Property',
      }),
    });

    if (!productResponse.ok) {
      const error = await productResponse.json();
      console.error('❌ Product creation failed:', error);
      return { success: false, error: error.error?.message || 'Product creation failed' };
    }

    const product = await productResponse.json();
    console.log('✅ Product created:', product.id);

    // Test 2: Create a price for the product
    console.log('\n2️⃣ Creating price...');
    const priceResponse = await fetch('https://api.stripe.com/v1/prices', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        product: product.id,
        unit_amount: '50000', // $500.00 in cents
        currency: 'usd',
      }),
    });

    if (!priceResponse.ok) {
      const error = await priceResponse.json();
      console.error('❌ Price creation failed:', error);
      return { success: false, error: error.error?.message || 'Price creation failed' };
    }

    const price = await priceResponse.json();
    console.log('✅ Price created:', price.id, '($500.00)');

    // Test 3: Create payment link
    console.log('\n3️⃣ Creating payment link...');
    const linkParams = new URLSearchParams({
      'line_items[0][price]': price.id,
      'line_items[0][quantity]': '1',
      'metadata[test]': 'true',
      'metadata[booking_id]': 'test_booking_123',
    });

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
      console.error('❌ Payment link creation failed:', error);
      return { success: false, error: error.error?.message || 'Payment link creation failed' };
    }

    const link = await linkResponse.json();
    console.log('✅ Payment link created!');
    console.log('🔗 Link URL:', link.url);
    console.log('📋 Link ID:', link.id);

    console.log('\n🎉 SUCCESS! Stripe integration is working correctly!');
    console.log('\n📌 Next steps:');
    console.log('   1. Create a test booking request in your app');
    console.log('   2. Approve it as a property owner');
    console.log('   3. Check the approval email for the payment link');
    console.log('   4. Test payment with card: 4242 4242 4242 4242');

    return {
      success: true,
      paymentLink: link.url,
      paymentLinkId: link.id,
    };
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    return { success: false, error: error.message };
  }
}

// Get API key from command line argument
const apiKey = process.argv[2];

if (!apiKey) {
  console.error('❌ Error: Stripe API key required');
  console.log('\nUsage: node test-stripe.js sk_test_xxxxx');
  console.log('\nTo test with your Cloudflare environment variable:');
  console.log('1. Get the key from Cloudflare Dashboard → Pages → Settings → Environment Variables');
  console.log('2. Run: node test-stripe.js <your-stripe-secret-key>');
  process.exit(1);
}

if (!apiKey.startsWith('sk_test_') && !apiKey.startsWith('sk_live_')) {
  console.error('❌ Error: Invalid Stripe API key format');
  console.log('Expected format: sk_test_... or sk_live_...');
  process.exit(1);
}

if (apiKey.startsWith('sk_live_')) {
  console.warn('⚠️  WARNING: Using LIVE API key! This will create real payment links.');
  console.warn('   Consider using test mode (sk_test_...) for testing.');
}

// Run the test
testStripePaymentLink(apiKey)
  .then(result => {
    if (!result.success) {
      console.error('\n❌ Test failed:', result.error);
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('\n❌ Unexpected error:', error);
    process.exit(1);
  });
