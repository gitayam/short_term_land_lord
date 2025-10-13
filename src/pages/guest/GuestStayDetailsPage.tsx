/**
 * Guest Stay Details Page
 * Displays enhanced property information for verified current guests
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface GuestInfo {
  name: string;
  email: string;
  check_in: string;
  check_out: string;
}

interface PropertyImage {
  image_url: string;
  caption: string | null;
  is_primary: number;
  display_order: number;
}

interface PropertyRoom {
  room_type: string;
  name: string | null;
  bed_type: string | null;
  bed_count: number;
  has_ensuite: number;
  amenities: string | null;
}

interface Property {
  id: string;
  name: string;
  address: string;
  street_address: string;
  city: string;
  state: string;
  zip_code: string;
  description: string | null;
  bedrooms: number;
  bathrooms: number;
  wifi_network: string | null;
  wifi_password: string | null;
  checkin_time: string;
  checkout_time: string;
  guest_rules: string | null;
  guest_checkin_instructions: string | null;
  guest_checkout_instructions: string | null;
  guest_wifi_instructions: string | null;
  local_attractions: string | null;
  emergency_contact: string | null;
  guest_faq: string | null;
  trash_day: string | null;
  recycling_day: string | null;
  cleaning_supplies_location: string | null;
  special_instructions: string | null;
  owner_first_name: string;
  owner_last_name: string;
  owner_email: string;
  owner_phone: string;
  images: PropertyImage[];
  rooms: PropertyRoom[];
}

export function GuestStayDetailsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [guestInfo, setGuestInfo] = useState<GuestInfo | null>(null);
  const [property, setProperty] = useState<Property | null>(null);
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    loadPropertyDetails();
  }, []);

  const loadPropertyDetails = async () => {
    try {
      // Get session token
      const sessionToken = localStorage.getItem('guest_session_token');
      if (!sessionToken) {
        throw new Error('No session token found. Please verify your stay first.');
      }

      // Call property details API
      const response = await fetch('/api/guest-stay/property', {
        headers: {
          Authorization: `Bearer ${sessionToken}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.error || 'Failed to load property details');
      }

      setGuestInfo(data.guest_info);
      setProperty(data.property);
    } catch (err: any) {
      setError(err.message);
      // If unauthorized, redirect back to verification
      if (err.message.includes('session') || err.message.includes('token')) {
        setTimeout(() => navigate('/guest-stay/verify'), 2000);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4 mx-auto"></div>
          <p className="text-gray-600">Loading your stay details...</p>
        </div>
      </div>
    );
  }

  if (error || !property || !guestInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="card max-w-md text-center">
          <div className="text-5xl mb-4">🔒</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Error</h2>
          <p className="text-gray-600 mb-4">{error || 'Unable to load property details'}</p>
          <button
            onClick={() => navigate('/guest-stay/verify')}
            className="btn-primary"
          >
            Return to Verification
          </button>
        </div>
      </div>
    );
  }

  const primaryImage = property.images.find((img) => img.is_primary === 1) || property.images[0];
  const bedrooms = property.rooms.filter((r) => r.room_type === 'bedroom');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-2">Welcome, {guestInfo.name}! 👋</h1>
          <h2 className="text-xl opacity-90">{property.name}</h2>
          <div className="flex items-center gap-4 mt-3 text-sm opacity-80">
            <span>📅 Check-in: {formatDate(guestInfo.check_in)}</span>
            <span>•</span>
            <span>📅 Check-out: {formatDate(guestInfo.check_out)}</span>
          </div>
        </div>
      </div>

      {/* Photo Gallery */}
      {property.images.length > 0 && (
        <div className="relative bg-gray-900">
          <div className="relative h-64 md:h-80">
            <img
              src={property.images[selectedImage]?.image_url || primaryImage?.image_url}
              alt={property.name}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Thumbnail Navigation */}
          {property.images.length > 1 && (
            <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-2 px-4 overflow-x-auto">
              {property.images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={`flex-shrink-0 w-16 h-16 rounded overflow-hidden border-2 transition-all ${
                    selectedImage === idx ? 'border-white scale-110' : 'border-transparent opacity-60'
                  }`}
                >
                  <img src={img.image_url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Full Address */}
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">📍</span>
            <h3 className="text-lg font-semibold text-gray-900">Property Address</h3>
          </div>
          <p className="text-xl font-medium text-gray-900">{property.street_address}</p>
          <p className="text-gray-700">
            {property.city}, {property.state} {property.zip_code}
          </p>
          <a
            href={`https://maps.google.com/?q=${encodeURIComponent(property.address)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block mt-3 text-blue-600 hover:text-blue-700 font-semibold"
          >
            🗺️ Open in Google Maps
          </a>
        </div>

        {/* Check-in / Check-out */}
        <div className="grid grid-cols-2 gap-4">
          <div className="card">
            <div className="text-3xl mb-2">🔑</div>
            <h3 className="font-semibold text-gray-900 mb-1">Check-in</h3>
            <p className="text-2xl font-bold text-blue-600">{property.checkin_time}</p>
            {property.guest_checkin_instructions && (
              <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">
                {property.guest_checkin_instructions}
              </p>
            )}
          </div>
          <div className="card">
            <div className="text-3xl mb-2">👋</div>
            <h3 className="font-semibold text-gray-900 mb-1">Check-out</h3>
            <p className="text-2xl font-bold text-blue-600">{property.checkout_time}</p>
            {property.guest_checkout_instructions && (
              <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">
                {property.guest_checkout_instructions}
              </p>
            )}
          </div>
        </div>

        {/* WiFi */}
        {(property.wifi_network || property.wifi_password) && (
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">📶</span>
              <h3 className="text-lg font-semibold text-gray-900">WiFi Information</h3>
            </div>
            {property.wifi_network && (
              <div className="mb-2">
                <span className="text-sm text-gray-600">Network: </span>
                <span className="font-mono font-semibold text-gray-900 text-lg">
                  {property.wifi_network}
                </span>
              </div>
            )}
            {property.wifi_password && (
              <div>
                <span className="text-sm text-gray-600">Password: </span>
                <span className="font-mono font-semibold text-gray-900 text-lg">
                  {property.wifi_password}
                </span>
              </div>
            )}
            {property.guest_wifi_instructions && (
              <p className="text-sm text-gray-600 mt-3 whitespace-pre-wrap">
                {property.guest_wifi_instructions}
              </p>
            )}
          </div>
        )}

        {/* Host Contact */}
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">👤</span>
            <h3 className="text-lg font-semibold text-gray-900">Contact Your Host</h3>
          </div>
          <p className="text-lg font-medium text-gray-900 mb-3">
            {property.owner_first_name} {property.owner_last_name}
          </p>
          <div className="space-y-2">
            <div>
              <a
                href={`tel:${property.owner_phone}`}
                className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-semibold"
              >
                📞 {property.owner_phone}
              </a>
            </div>
            <div>
              <a
                href={`mailto:${property.owner_email}`}
                className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700"
              >
                ✉️ {property.owner_email}
              </a>
            </div>
          </div>
        </div>

        {/* Emergency Contact */}
        {property.emergency_contact && (
          <div className="card bg-red-50 border-red-200">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">🚨</span>
              <h3 className="font-semibold text-gray-900">Emergency Contact</h3>
            </div>
            <p className="text-gray-700 whitespace-pre-wrap">{property.emergency_contact}</p>
          </div>
        )}

        {/* Property Description */}
        {property.description && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">About This Property</h3>
            <p className="text-gray-700 whitespace-pre-wrap">{property.description}</p>
          </div>
        )}

        {/* Rooms */}
        {bedrooms.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">🛏️ Bedrooms</h3>
            <div className="space-y-3">
              {bedrooms.map((room, idx) => (
                <div key={idx} className="border border-gray-200 rounded-lg p-4">
                  <div className="font-medium text-gray-900">
                    {room.name || `Bedroom ${idx + 1}`}
                    {room.has_ensuite === 1 && (
                      <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        Ensuite
                      </span>
                    )}
                  </div>
                  {room.bed_type && (
                    <p className="text-sm text-gray-600 mt-1">
                      {room.bed_count > 1 ? `${room.bed_count}x ` : ''}
                      {room.bed_type}
                    </p>
                  )}
                  {room.amenities && (
                    <p className="text-sm text-gray-600 mt-1">✨ {room.amenities}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* House Rules */}
        {property.guest_rules && (
          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">📋</span>
              <h3 className="text-lg font-semibold text-gray-900">House Rules</h3>
            </div>
            <p className="text-gray-700 whitespace-pre-wrap">{property.guest_rules}</p>
          </div>
        )}

        {/* Trash & Recycling */}
        {(property.trash_day || property.recycling_day) && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">🗑️ Trash & Recycling</h3>
            <div className="space-y-2 text-gray-700">
              {property.trash_day && <p>Trash Day: {property.trash_day}</p>}
              {property.recycling_day && <p>Recycling Day: {property.recycling_day}</p>}
            </div>
          </div>
        )}

        {/* Cleaning Supplies */}
        {property.cleaning_supplies_location && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">🧹 Cleaning Supplies</h3>
            <p className="text-gray-700 whitespace-pre-wrap">{property.cleaning_supplies_location}</p>
          </div>
        )}

        {/* Local Attractions */}
        {property.local_attractions && (
          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">🗺️</span>
              <h3 className="text-lg font-semibold text-gray-900">Local Recommendations</h3>
            </div>
            <p className="text-gray-700 whitespace-pre-wrap">{property.local_attractions}</p>
          </div>
        )}

        {/* Special Instructions */}
        {property.special_instructions && (
          <div className="card bg-yellow-50 border-yellow-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">⚠️ Special Instructions</h3>
            <p className="text-gray-700 whitespace-pre-wrap">{property.special_instructions}</p>
          </div>
        )}

        {/* FAQ */}
        {property.guest_faq && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">❓ Frequently Asked Questions</h3>
            <p className="text-gray-700 whitespace-pre-wrap">{property.guest_faq}</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="max-w-4xl mx-auto px-4 py-8 text-center text-sm text-gray-500">
        <p>Enjoy your stay! 🏡</p>
        <p className="mt-2">Need help? Contact {property.owner_first_name} at {property.owner_phone}</p>
      </div>
    </div>
  );
}
