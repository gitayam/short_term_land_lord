/**
 * Booking Confirmation Page
 * Shows booking details after successful booking
 * Accessible via /booking/:id/confirmation
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';

interface BookingConfirmation {
  booking: {
    id: string;
    external_id: string;
    check_in_date: string;
    check_out_date: string;
    guest_name: string;
    guest_email: string;
    guest_phone: string | null;
    num_guests: number;
    total_paid: number;
    booking_status: string;
  };
  property: {
    id: string;
    name: string;
    address: string;
    city: string;
    state: string;
    country: string;
    checkin_time: string;
    checkout_time: string;
    guest_checkin_instructions: string;
    guest_wifi_instructions: string;
    emergency_contact: string;
  };
}

export function BookingConfirmationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [confirmation, setConfirmation] = useState<BookingConfirmation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadConfirmation(id);
    }
  }, [id]);

  const loadConfirmation = async (bookingId: string) => {
    try {
      setLoading(true);
      setError(null);

      // For guest bookings, we use the external_id
      const response = await fetch(`/api/bookings/${bookingId}/confirmation`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Booking not found');
        }
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load booking details');
      }

      const data = await response.json();
      setConfirmation(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatTime = (timeStr: string) => {
    // timeStr is like "15:00:00" or "3:00 PM"
    try {
      const [hours, minutes] = timeStr.split(':');
      const hour = parseInt(hours);
      const ampm = hour >= 12 ? 'PM' : 'AM';
      const displayHour = hour % 12 || 12;
      return `${displayHour}:${minutes} ${ampm}`;
    } catch {
      return timeStr;
    }
  };

  const calculateNights = (checkIn: string, checkOut: string) => {
    const start = new Date(checkIn);
    const end = new Date(checkOut);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading your booking details...</p>
        </div>
      </div>
    );
  }

  if (error || !confirmation) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Booking Not Found</h1>
          <p className="text-gray-600 mb-4">{error || 'This booking could not be found.'}</p>
          <Link
            to="/"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-medium"
          >
            Return Home
          </Link>
        </div>
      </div>
    );
  }

  const { booking, property } = confirmation;
  const nights = calculateNights(booking.check_in_date, booking.check_out_date);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Success Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h1 className="text-4xl font-bold mb-2">Booking Confirmed!</h1>
          <p className="text-xl text-green-100">
            Your reservation has been successfully created
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 -mt-8">
        {/* Booking Summary Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <div className="flex items-center gap-3 mb-6 pb-6 border-b border-gray-200">
            <div className="text-4xl">✅</div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Your Reservation</h2>
              <p className="text-gray-600">Confirmation #{booking.external_id}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Property Info */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Property</h3>
              <p className="text-lg font-semibold text-gray-900">{property.name}</p>
              <p className="text-sm text-gray-600">{property.address}</p>
              <p className="text-sm text-gray-600">
                {property.city}, {property.state} {property.country}
              </p>
            </div>

            {/* Guest Info */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Guest</h3>
              <p className="text-lg font-semibold text-gray-900">{booking.guest_name}</p>
              <p className="text-sm text-gray-600">{booking.guest_email}</p>
              {booking.guest_phone && (
                <p className="text-sm text-gray-600">{booking.guest_phone}</p>
              )}
            </div>

            {/* Dates */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Check-in</h3>
              <p className="text-lg font-semibold text-gray-900">
                {formatDate(booking.check_in_date)}
              </p>
              {property.checkin_time && (
                <p className="text-sm text-gray-600">
                  After {formatTime(property.checkin_time)}
                </p>
              )}
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Check-out</h3>
              <p className="text-lg font-semibold text-gray-900">
                {formatDate(booking.check_out_date)}
              </p>
              {property.checkout_time && (
                <p className="text-sm text-gray-600">
                  Before {formatTime(property.checkout_time)}
                </p>
              )}
            </div>

            {/* Summary */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Duration</h3>
              <p className="text-lg font-semibold text-gray-900">
                {nights} {nights === 1 ? 'night' : 'nights'}
              </p>
              <p className="text-sm text-gray-600">
                {booking.num_guests} {booking.num_guests === 1 ? 'guest' : 'guests'}
              </p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Total Paid</h3>
              <p className="text-lg font-semibold text-green-600">
                ${booking.total_paid.toFixed(2)}
              </p>
              <p className="text-sm text-gray-600">Payment confirmed</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 pt-6 border-t border-gray-200">
            <button
              onClick={() => window.print()}
              className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
            >
              📄 Print Confirmation
            </button>
            <Link
              to={`/p/${property.id}`}
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-center"
            >
              View Property Details
            </Link>
          </div>
        </div>

        {/* Check-in Instructions */}
        {property.guest_checkin_instructions && (
          <div className="bg-white rounded-xl shadow p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>📥</span> Check-in Instructions
            </h2>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">
                {property.guest_checkin_instructions}
              </p>
            </div>
          </div>
        )}

        {/* WiFi Instructions */}
        {property.guest_wifi_instructions && (
          <div className="bg-white rounded-xl shadow p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>📶</span> WiFi Access
            </h2>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">
                {property.guest_wifi_instructions}
              </p>
            </div>
          </div>
        )}

        {/* Emergency Contact */}
        {property.emergency_contact && (
          <div className="bg-white rounded-xl shadow p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>🚨</span> Emergency Contact
            </h2>
            <p className="text-gray-700">{property.emergency_contact}</p>
          </div>
        )}

        {/* What's Next */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">What's Next?</h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="text-2xl">✉️</div>
              <div>
                <h3 className="font-semibold text-gray-900">Check Your Email</h3>
                <p className="text-sm text-gray-600">
                  We've sent a confirmation to {booking.guest_email}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="text-2xl">📅</div>
              <div>
                <h3 className="font-semibold text-gray-900">Save the Dates</h3>
                <p className="text-sm text-gray-600">
                  Add this booking to your calendar so you don't forget
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="text-2xl">🏠</div>
              <div>
                <h3 className="font-semibold text-gray-900">Plan Your Stay</h3>
                <p className="text-sm text-gray-600">
                  Review property details and local recommendations
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Create Account CTA */}
        <div className="bg-white rounded-xl shadow p-6 text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-2">Want to Manage Your Bookings?</h2>
          <p className="text-gray-600 mb-4">
            Create an account to view all your reservations, update details, and get faster bookings next time.
          </p>
          <Link
            to={`/convert-guest?email=${encodeURIComponent(booking.guest_email)}&name=${encodeURIComponent(booking.guest_name)}`}
            className="inline-block bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-3 rounded-lg hover:from-blue-700 hover:to-purple-700 font-semibold"
          >
            Create Free Account
          </Link>
          <p className="text-sm text-gray-500 mt-2">
            Or <Link to="/" className="text-blue-600 hover:underline">continue browsing properties</Link>
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-800 text-white py-8 mt-12">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <p className="text-gray-400 text-sm">
            Questions? Contact us at {property.emergency_contact || 'support@fayettevillerentals.com'}
          </p>
          <p className="text-gray-500 text-xs mt-2">
            © 2025 Fayetteville Rentals. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
