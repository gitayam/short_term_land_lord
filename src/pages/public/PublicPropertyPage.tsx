/**
 * Public Property Showcase Page
 * Displays property information for guests without authentication
 */

import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { GuestBookingFlow } from '../../components/booking/GuestBookingFlow';

interface PropertyImage {
  id: string;
  image_url: string;
  caption: string | null;
  display_order: number;
  is_primary: number;
}

interface PropertyRoom {
  id: string;
  room_type: 'bedroom' | 'bathroom' | 'kitchen' | 'living_room' | 'other';
  name: string | null;
  bed_type: string | null;
  bed_count: number;
  has_ensuite: number;
  amenities: string | null;
  notes: string | null;
}

interface Property {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  country: string;
  property_type: string;
  bedrooms: number;
  bathrooms: number;
  square_feet: number;
  total_beds: number;
  description: string;
  checkin_time: string;
  checkout_time: string;
  guest_rules: string;
  guest_checkin_instructions: string;
  guest_checkout_instructions: string;
  guest_wifi_instructions: string;
  local_attractions: string;
  emergency_contact: string;
  guest_faq: string;
}

const ROOM_TYPE_ICONS = {
  bedroom: '🛏️',
  bathroom: '🚿',
  kitchen: '🍳',
  living_room: '🛋️',
  other: '📦',
};

export function PublicPropertyPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [property, setProperty] = useState<Property | null>(null);
  const [images, setImages] = useState<PropertyImage[]>([]);
  const [rooms, setRooms] = useState<PropertyRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<number>(0);
  const [showBookingForm, setShowBookingForm] = useState(false);

  useEffect(() => {
    if (id) {
      loadProperty(id, token);
    }
  }, [id, token]);

  const loadProperty = async (propertyId: string, accessToken: string | null) => {
    try {
      setLoading(true);
      setError(null);

      const url = accessToken
        ? `/api/public/properties/${propertyId}?token=${accessToken}`
        : `/api/public/properties/${propertyId}`;

      const response = await fetch(url);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load property');
      }

      const data = await response.json();
      setProperty(data.property);
      setImages(data.images || []);
      setRooms(data.rooms || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading property...</p>
        </div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="text-6xl mb-4">🏠</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Property Not Available</h1>
          <p className="text-gray-600 mb-4">{error || 'This property could not be found.'}</p>
          <p className="text-sm text-gray-500">
            Please check your link or contact the property owner.
          </p>
        </div>
      </div>
    );
  }

  // Group rooms by type
  const bedrooms = rooms.filter((r) => r.room_type === 'bedroom');
  const bathrooms = rooms.filter((r) => r.room_type === 'bathroom');
  const otherRooms = rooms.filter((r) => !['bedroom', 'bathroom'].includes(r.room_type));

  // Find primary image or use first image
  const primaryImage = images.find((img) => img.is_primary === 1) || images[0];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section with Image Gallery */}
      {images.length > 0 ? (
        <div className="relative bg-gray-900">
          <div className="relative h-96 md:h-[500px]">
            <img
              src={images[selectedImage]?.image_url || primaryImage?.image_url}
              alt={property.name}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
          </div>

          {/* Thumbnail Navigation */}
          {images.length > 1 && (
            <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-2 px-4 overflow-x-auto">
              {images.map((img, idx) => (
                <button
                  key={img.id}
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
      ) : (
        <div className="relative bg-gradient-to-r from-blue-600 to-purple-600 h-64">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-white">
              <div className="text-6xl mb-4">🏠</div>
              <h1 className="text-3xl font-bold">{property.name}</h1>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6 -mt-20 relative z-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{property.name}</h1>
          <p className="text-gray-600 flex items-center gap-2">
            📍 {property.city}, {property.state} {property.country}
          </p>
          <div className="flex flex-wrap gap-4 mt-4 text-sm">
            {property.bedrooms && (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                🛏️ {property.bedrooms} Bedrooms
              </span>
            )}
            {property.bathrooms && (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                🚿 {property.bathrooms} Bathrooms
              </span>
            )}
            {property.total_beds && (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                🛌 {property.total_beds} Beds
              </span>
            )}
            {property.square_feet && (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                📐 {property.square_feet} sq ft
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            {property.description && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">About This Property</h2>
                <p className="text-gray-700 whitespace-pre-wrap">{property.description}</p>
              </div>
            )}

            {/* Rooms */}
            {rooms.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Rooms & Spaces</h2>

                {/* Bedrooms */}
                {bedrooms.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">🛏️ Bedrooms</h3>
                    <div className="space-y-3">
                      {bedrooms.map((room) => (
                        <div key={room.id} className="border border-gray-200 rounded-lg p-4">
                          <div className="font-medium text-gray-900">
                            {room.name || 'Bedroom'}
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

                {/* Bathrooms */}
                {bathrooms.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">🚿 Bathrooms</h3>
                    <div className="text-gray-700">
                      {bathrooms.length} {bathrooms.length === 1 ? 'bathroom' : 'bathrooms'}
                    </div>
                  </div>
                )}

                {/* Other Rooms */}
                {otherRooms.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">Other Spaces</h3>
                    <div className="space-y-2">
                      {otherRooms.map((room) => (
                        <div key={room.id} className="text-gray-700">
                          {ROOM_TYPE_ICONS[room.room_type]} {room.name || room.room_type}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Local Attractions */}
            {property.local_attractions && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">🎯 Local Attractions</h2>
                <p className="text-gray-700 whitespace-pre-wrap">{property.local_attractions}</p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Check-in/Check-out */}
            {(property.checkin_time || property.checkout_time) && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4">⏰ Check-in & Check-out</h2>
                {property.checkin_time && (
                  <div className="mb-2">
                    <span className="text-gray-600">Check-in:</span>
                    <span className="ml-2 font-medium">{property.checkin_time}</span>
                  </div>
                )}
                {property.checkout_time && (
                  <div>
                    <span className="text-gray-600">Check-out:</span>
                    <span className="ml-2 font-medium">{property.checkout_time}</span>
                  </div>
                )}
              </div>
            )}

            {/* House Rules */}
            {property.guest_rules && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4">📋 House Rules</h2>
                <p className="text-gray-700 text-sm whitespace-pre-wrap">{property.guest_rules}</p>
              </div>
            )}

            {/* Emergency Contact */}
            {property.emergency_contact && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4">🚨 Emergency Contact</h2>
                <p className="text-gray-700">{property.emergency_contact}</p>
              </div>
            )}

            {/* Guest Access CTA */}
            <div className="space-y-4">
              {/* Current Guest Access */}
              <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg shadow-lg p-6 text-white">
                <h2 className="text-xl font-bold mb-2">Staying here now? 🏠</h2>
                <p className="text-sm text-green-100 mb-4">
                  Access WiFi, full address, host contact, and more details for your stay.
                </p>
                <button
                  onClick={() => navigate(`/guest-stay/verify?property_id=${id}`)}
                  className="w-full bg-white text-green-600 font-semibold py-3 px-4 rounded-lg hover:bg-green-50 transition-colors"
                >
                  I'm Staying Here
                </button>
              </div>

              {/* Book Now CTA */}
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-6 text-white">
                <h2 className="text-xl font-bold mb-2">Ready to book?</h2>
                <p className="text-sm text-blue-100 mb-4">
                  Select your dates and complete your reservation instantly!
                </p>
                <button
                  onClick={() => setShowBookingForm(true)}
                  className="w-full bg-white text-blue-600 font-semibold py-3 px-4 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  Book Now
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Additional Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* Check-in Instructions */}
          {property.guest_checkin_instructions && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">📥 Check-in Instructions</h2>
              <p className="text-gray-700 whitespace-pre-wrap">{property.guest_checkin_instructions}</p>
            </div>
          )}

          {/* Check-out Instructions */}
          {property.guest_checkout_instructions && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">📤 Check-out Instructions</h2>
              <p className="text-gray-700 whitespace-pre-wrap">{property.guest_checkout_instructions}</p>
            </div>
          )}
        </div>

        {/* WiFi Instructions */}
        {property.guest_wifi_instructions && (
          <div className="bg-white rounded-lg shadow p-6 mt-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">📶 WiFi Access</h2>
            <p className="text-gray-700 whitespace-pre-wrap">{property.guest_wifi_instructions}</p>
          </div>
        )}

        {/* FAQ */}
        {property.guest_faq && (
          <div className="bg-white rounded-lg shadow p-6 mt-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">❓ Frequently Asked Questions</h2>
            <p className="text-gray-700 whitespace-pre-wrap">{property.guest_faq}</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-gray-800 text-white py-8 mt-12">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p className="text-gray-400 text-sm">
            Powered by Short Term Land Lord
          </p>
        </div>
      </div>

      {/* Frictionless Booking Flow */}
      <GuestBookingFlow
        property={property}
        isOpen={showBookingForm}
        onClose={() => setShowBookingForm(false)}
      />
    </div>
  );
}
