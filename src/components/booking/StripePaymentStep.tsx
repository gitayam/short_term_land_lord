/**
 * Stripe Payment Step Component
 * Handles secure card collection using Stripe Elements
 */

import { useState } from 'react';
import { PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';

interface StripePaymentStepProps {
  amount: number;
  onBack: () => void;
  onSuccess: (paymentMethodId: string) => void;
  onError: (error: string) => void;
}

export function StripePaymentStep({ amount, onBack, onSuccess, onError }: StripePaymentStepProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      onError('Stripe has not loaded yet. Please wait and try again.');
      return;
    }

    setProcessing(true);

    try {
      // Submit the payment element to Stripe
      const { error: submitError } = await elements.submit();

      if (submitError) {
        onError(submitError.message || 'Failed to validate card');
        setProcessing(false);
        return;
      }

      // Confirm the payment (but won't charge due to manual capture)
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        redirect: 'if_required',
        confirmParams: {
          return_url: `${window.location.origin}/booking/confirmation`,
        },
      });

      if (error) {
        onError(error.message || 'Card validation failed');
        setProcessing(false);
        return;
      }

      if (paymentIntent && paymentIntent.status === 'requires_capture') {
        // Success! Card is validated, payment method is stored
        onSuccess(paymentIntent.id);
      } else {
        onError('Unexpected payment status. Please try again.');
        setProcessing(false);
      }
    } catch (err: any) {
      onError(err.message || 'Payment failed');
      setProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <button
          type="button"
          onClick={onBack}
          className="text-blue-600 hover:text-blue-700 mb-4 flex items-center gap-1"
        >
          ← Back
        </button>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Secure Your Reservation</h3>
        <p className="text-gray-600 mb-4">
          Your card will be validated but <strong>not charged</strong> until the owner approves your booking.
        </p>
      </div>

      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <PaymentElement />
      </div>

      <div className="text-sm text-gray-600 space-y-2">
        <p className="flex items-start gap-2">
          <span className="text-green-600 font-bold">✓</span>
          <span>Your card will only be charged if the owner approves your booking</span>
        </p>
        <p className="flex items-start gap-2">
          <span className="text-green-600 font-bold">✓</span>
          <span>No fees or charges until approval</span>
        </p>
        <p className="flex items-start gap-2">
          <span className="text-green-600 font-bold">✓</span>
          <span>Secure payment processing by Stripe</span>
        </p>
      </div>

      <button
        type="submit"
        disabled={!stripe || processing}
        className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-lg"
      >
        {processing ? 'Validating Card...' : `Validate Card & Request Booking`}
      </button>

      <p className="text-xs text-center text-gray-500">
        🔒 Payment information is encrypted and secure
      </p>
    </form>
  );
}
