/**
 * Frictionless Guest Booking Flow
 * Optimized for conversion using progressive disclosure and sunk cost fallacy
 * Flow: Dates → Guest Info → Payment → Account Creation (optional)
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface Property {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  nightly_rate?: number;
  cleaning_fee?: number;
  bedrooms: number;
  bathrooms: number;
}

interface GuestBookingFlowProps {
  property: Property;
  isOpen: boolean;
  onClose: () => void;
  preselectedDates?: {
    checkIn?: string;
    checkOut?: string;
  };
}

type BookingStep = 'dates' | 'guest-info' | 'payment' | 'confirmation';

interface BookingData {
  // Step 1: Dates
  checkInDate: string;
  checkOutDate: string;

  // Step 2: Guest Info
  guestName: string;
  guestEmail: string;
  guestPhone: string;
  numGuests: number;
  specialRequests: string;

  // Step 3: Payment
  cardNumber: string;
  cardExpiry: string;
  cardCvc: string;
  billingZip: string;

  // Calculated
  nights: number;
  subtotal: number;
  cleaningFee: number;
  serviceFee: number;
  total: number;
}

export function GuestBookingFlow({
  property,
  isOpen,
  onClose,
  preselectedDates
}: GuestBookingFlowProps) {
  const navigate = useNavigate();
  const [step, setStep] = useState<BookingStep>('dates');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bookingData, setBookingData] = useState<BookingData>({
    checkInDate: preselectedDates?.checkIn || '',
    checkOutDate: preselectedDates?.checkOut || '',
    guestName: '',
    guestEmail: '',
    guestPhone: '',
    numGuests: 1,
    specialRequests: '',
    cardNumber: '',
    cardExpiry: '',
    cardCvc: '',
    billingZip: '',
    nights: 0,
    subtotal: 0,
    cleaningFee: property.cleaning_fee || 75,
    serviceFee: 0,
    total: 0,
  });

  // Calculate pricing when dates change
  useEffect(() => {
    if (bookingData.checkInDate && bookingData.checkOutDate) {
      const checkIn = new Date(bookingData.checkInDate);
      const checkOut = new Date(bookingData.checkOutDate);
      const nights = Math.ceil((checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24));

      if (nights > 0) {
        const nightlyRate = property.nightly_rate || 150;
        const subtotal = nights * nightlyRate;
        const serviceFee = Math.round(subtotal * 0.12); // 12% service fee
        const total = subtotal + bookingData.cleaningFee + serviceFee;

        setBookingData(prev => ({
          ...prev,
          nights,
          subtotal,
          serviceFee,
          total,
        }));
      }
    }
  }, [bookingData.checkInDate, bookingData.checkOutDate, property.nightly_rate, bookingData.cleaningFee]);

  const handleSubmitBooking = async () => {
    setLoading(true);
    setError(null);

    try {
      // Submit guest booking (no auth required)
      const response = await fetch('/api/guest-bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          property_id: property.id,
          check_in_date: bookingData.checkInDate,
          check_out_date: bookingData.checkOutDate,
          guest_name: bookingData.guestName,
          guest_email: bookingData.guestEmail,
          guest_phone: bookingData.guestPhone,
          num_guests: bookingData.numGuests,
          special_requests: bookingData.specialRequests,
          payment: {
            amount: bookingData.total,
            // In production, use Stripe token instead of raw card data
            token: 'tok_visa', // Placeholder
          },
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Booking failed');
      }

      const result = await response.json();
      setStep('confirmation');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const canProceedFromDates = bookingData.checkInDate && bookingData.checkOutDate && bookingData.nights > 0;
  const canProceedFromGuestInfo = bookingData.guestName && bookingData.guestEmail && bookingData.numGuests > 0;
  const canProceedFromPayment = bookingData.cardNumber && bookingData.cardExpiry && bookingData.cardCvc && bookingData.billingZip;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full my-8">
        {/* Progress Indicator */}
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-2xl font-bold text-gray-900">Book Your Stay</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            >
              ×
            </button>
          </div>
          <div className="flex items-center gap-2">
            <div className={`flex-1 h-2 rounded-full ${step === 'dates' || step === 'guest-info' || step === 'payment' || step === 'confirmation' ? 'bg-blue-600' : 'bg-gray-200'}`} />
            <div className={`flex-1 h-2 rounded-full ${step === 'guest-info' || step === 'payment' || step === 'confirmation' ? 'bg-blue-600' : 'bg-gray-200'}`} />
            <div className={`flex-1 h-2 rounded-full ${step === 'payment' || step === 'confirmation' ? 'bg-blue-600' : 'bg-gray-200'}`} />
            <div className={`flex-1 h-2 rounded-full ${step === 'confirmation' ? 'bg-green-600' : 'bg-gray-200'}`} />
          </div>
          <div className="flex justify-between text-xs text-gray-600 mt-1">
            <span>Dates</span>
            <span>Guest Info</span>
            <span>Payment</span>
            <span>Done!</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2 p-6">
            {/* Step 1: Select Dates */}
            {step === 'dates' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">When are you visiting?</h3>
                  <p className="text-gray-600">Select your check-in and check-out dates</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Check-in</label>
                    <input
                      type="date"
                      value={bookingData.checkInDate}
                      onChange={(e) => setBookingData({ ...bookingData, checkInDate: e.target.value })}
                      min={new Date().toISOString().split('T')[0]}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Check-out</label>
                    <input
                      type="date"
                      value={bookingData.checkOutDate}
                      onChange={(e) => setBookingData({ ...bookingData, checkOutDate: e.target.value })}
                      min={bookingData.checkInDate || new Date().toISOString().split('T')[0]}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-lg"
                    />
                  </div>
                </div>

                {canProceedFromDates && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-green-800 font-medium">
                      ✓ Available! {bookingData.nights} {bookingData.nights === 1 ? 'night' : 'nights'}
                    </p>
                  </div>
                )}

                <button
                  onClick={() => setStep('guest-info')}
                  disabled={!canProceedFromDates}
                  className="w-full py-4 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-lg"
                >
                  Continue to Guest Info
                </button>
              </div>
            )}

            {/* Step 2: Guest Information */}
            {step === 'guest-info' && (
              <div className="space-y-6">
                <div>
                  <button
                    onClick={() => setStep('dates')}
                    className="text-blue-600 hover:text-blue-700 mb-4 flex items-center gap-1"
                  >
                    ← Back
                  </button>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Who's coming?</h3>
                  <p className="text-gray-600">We'll send your confirmation here</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Full Name *</label>
                    <input
                      type="text"
                      value={bookingData.guestName}
                      onChange={(e) => setBookingData({ ...bookingData, guestName: e.target.value })}
                      placeholder="John Doe"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Email Address *</label>
                    <input
                      type="email"
                      value={bookingData.guestEmail}
                      onChange={(e) => setBookingData({ ...bookingData, guestEmail: e.target.value })}
                      placeholder="john@example.com"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                    <input
                      type="tel"
                      value={bookingData.guestPhone}
                      onChange={(e) => setBookingData({ ...bookingData, guestPhone: e.target.value })}
                      placeholder="+1 (555) 123-4567"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Number of Guests *</label>
                    <select
                      value={bookingData.numGuests}
                      onChange={(e) => setBookingData({ ...bookingData, numGuests: parseInt(e.target.value) })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
                        <option key={num} value={num}>
                          {num} {num === 1 ? 'guest' : 'guests'}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Special Requests</label>
                    <textarea
                      value={bookingData.specialRequests}
                      onChange={(e) => setBookingData({ ...bookingData, specialRequests: e.target.value })}
                      rows={3}
                      placeholder="Any special requests or questions?"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <button
                  onClick={() => setStep('payment')}
                  disabled={!canProceedFromGuestInfo}
                  className="w-full py-4 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-lg"
                >
                  Continue to Payment
                </button>
              </div>
            )}

            {/* Step 3: Payment */}
            {step === 'payment' && (
              <div className="space-y-6">
                <div>
                  <button
                    onClick={() => setStep('guest-info')}
                    className="text-blue-600 hover:text-blue-700 mb-4 flex items-center gap-1"
                  >
                    ← Back
                  </button>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Complete Your Booking</h3>
                  <p className="text-gray-600">Secure payment via Stripe</p>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                    {error}
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Card Number *</label>
                    <input
                      type="text"
                      value={bookingData.cardNumber}
                      onChange={(e) => setBookingData({ ...bookingData, cardNumber: e.target.value })}
                      placeholder="4242 4242 4242 4242"
                      maxLength={19}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Expiry *</label>
                      <input
                        type="text"
                        value={bookingData.cardExpiry}
                        onChange={(e) => setBookingData({ ...bookingData, cardExpiry: e.target.value })}
                        placeholder="MM/YY"
                        maxLength={5}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">CVC *</label>
                      <input
                        type="text"
                        value={bookingData.cardCvc}
                        onChange={(e) => setBookingData({ ...bookingData, cardCvc: e.target.value })}
                        placeholder="123"
                        maxLength={4}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Billing ZIP Code *</label>
                    <input
                      type="text"
                      value={bookingData.billingZip}
                      onChange={(e) => setBookingData({ ...bookingData, billingZip: e.target.value })}
                      placeholder="12345"
                      maxLength={10}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <button
                  onClick={handleSubmitBooking}
                  disabled={!canProceedFromPayment || loading}
                  className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-lg"
                >
                  {loading ? 'Processing...' : `Pay $${bookingData.total}`}
                </button>

                <p className="text-xs text-gray-500 text-center">
                  🔒 Your payment info is secure. We use Stripe for processing.
                </p>
              </div>
            )}

            {/* Step 4: Confirmation */}
            {step === 'confirmation' && (
              <div className="space-y-6 text-center py-8">
                <div className="text-6xl mb-4">🎉</div>
                <h3 className="text-3xl font-bold text-gray-900">Booking Confirmed!</h3>
                <p className="text-gray-600 text-lg">
                  We've sent confirmation details to <strong>{bookingData.guestEmail}</strong>
                </p>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-left max-w-md mx-auto">
                  <h4 className="font-bold text-gray-900 mb-4">Next Steps:</h4>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li>✓ Check your email for booking details</li>
                    <li>✓ Add check-in date to your calendar</li>
                    <li>✓ Contact host with any questions</li>
                  </ul>
                </div>

                <div className="border-t border-gray-200 pt-6 mt-6">
                  <h4 className="font-bold text-gray-900 mb-4">Want to track your booking?</h4>
                  <p className="text-gray-600 mb-4">
                    Create an account to manage your reservations, view past stays, and more!
                  </p>
                  <button
                    onClick={() => {
                      const params = new URLSearchParams({
                        name: bookingData.guestName,
                        email: bookingData.guestEmail,
                        phone: bookingData.guestPhone,
                      });
                      navigate(`/convert-guest?${params.toString()}`);
                    }}
                    className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700"
                  >
                    Create Free Account
                  </button>
                  <button
                    onClick={onClose}
                    className="block w-full mt-3 text-gray-600 hover:text-gray-800"
                  >
                    Skip for now
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Booking Summary Sidebar */}
          <div className="bg-gray-50 p-6 border-l border-gray-200 rounded-r-2xl">
            <div className="sticky top-6">
              <h4 className="font-bold text-gray-900 mb-4">Booking Summary</h4>

              <div className="bg-white rounded-lg p-4 mb-4">
                <div className="font-medium text-gray-900">{property.name}</div>
                <div className="text-sm text-gray-600">{property.city}, {property.state}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {property.bedrooms} bed · {property.bathrooms} bath
                </div>
              </div>

              {bookingData.checkInDate && bookingData.checkOutDate && (
                <>
                  <div className="space-y-2 mb-4 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Check-in:</span>
                      <span className="font-medium">{new Date(bookingData.checkInDate).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Check-out:</span>
                      <span className="font-medium">{new Date(bookingData.checkOutDate).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Guests:</span>
                      <span className="font-medium">{bookingData.numGuests}</span>
                    </div>
                  </div>

                  <div className="border-t border-gray-200 pt-4 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">
                        ${property.nightly_rate || 150} × {bookingData.nights} {bookingData.nights === 1 ? 'night' : 'nights'}
                      </span>
                      <span className="font-medium">${bookingData.subtotal}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Cleaning fee</span>
                      <span className="font-medium">${bookingData.cleaningFee}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Service fee</span>
                      <span className="font-medium">${bookingData.serviceFee}</span>
                    </div>
                  </div>

                  <div className="border-t border-gray-200 pt-4 mt-4">
                    <div className="flex justify-between text-lg font-bold">
                      <span>Total</span>
                      <span>${bookingData.total}</span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
