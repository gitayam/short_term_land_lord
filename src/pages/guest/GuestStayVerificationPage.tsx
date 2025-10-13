/**
 * Guest Stay Verification Page
 * Allows current guests to verify their stay using last 4 digits of phone number
 */

import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export function GuestStayVerificationPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const propertyIdParam = searchParams.get('property_id') || '';

  const [propertyId, setPropertyId] = useState(propertyIdParam);
  const [phoneLast4, setPhoneLast4] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Validate input
      if (!propertyId || !phoneLast4) {
        throw new Error('Please provide both property ID and last 4 digits of phone number');
      }

      if (phoneLast4.length !== 4 || !/^\d{4}$/.test(phoneLast4)) {
        throw new Error('Phone number must be exactly 4 digits');
      }

      // Call verification API
      const response = await fetch('/api/guest-stay/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_id: propertyId,
          phone_last_4: phoneLast4,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.error || 'Verification failed');
      }

      // Store session token
      localStorage.setItem('guest_session_token', data.session_token);

      // Store booking details for display
      localStorage.setItem('guest_booking_details', JSON.stringify(data.booking_details));

      // Redirect to guest stay details page
      navigate('/guest-stay/details');
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🏠</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome, Guest!</h1>
          <p className="text-gray-600">
            Verify your stay to access detailed property information
          </p>
        </div>

        {/* Verification Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Property ID */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Property ID
              </label>
              <input
                type="text"
                required
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter property ID"
                disabled={loading}
              />
              <p className="text-xs text-gray-500 mt-1">
                This was provided in your booking confirmation
              </p>
            </div>

            {/* Last 4 digits of phone */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Last 4 Digits of Your Phone Number
              </label>
              <input
                type="text"
                required
                value={phoneLast4}
                onChange={(e) => {
                  // Only allow digits, max 4 characters
                  const value = e.target.value.replace(/\D/g, '').slice(0, 4);
                  setPhoneLast4(value);
                }}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl tracking-widest font-mono"
                placeholder="••••"
                maxLength={4}
                disabled={loading}
              />
              <p className="text-xs text-gray-500 mt-1">
                The phone number you provided when booking
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">⚠️</span>
                  <div>
                    <h3 className="font-semibold text-red-900 mb-1">Verification Failed</h3>
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || phoneLast4.length !== 4}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Verifying...</span>
                </div>
              ) : (
                'Verify & Access Property Details'
              )}
            </button>
          </form>

          {/* Info Box */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">ℹ️ What you'll get access to:</h4>
            <ul className="text-xs text-blue-800 space-y-1">
              <li>✓ Full property address and directions</li>
              <li>✓ WiFi network and password</li>
              <li>✓ Direct contact to your host</li>
              <li>✓ Check-in/check-out instructions</li>
              <li>✓ House rules and local recommendations</li>
            </ul>
          </div>
        </div>

        {/* Help Text */}
        <div className="text-center mt-6 text-sm text-gray-600">
          <p>
            Having trouble? Contact your property owner or check your booking confirmation for the correct information.
          </p>
        </div>
      </div>
    </div>
  );
}
