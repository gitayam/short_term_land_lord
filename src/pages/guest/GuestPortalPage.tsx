import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { guidebookApi } from '../../services/api';

interface Recommendation {
  name: string;
  category: string;
  description?: string;
  phone?: string;
  website?: string;
  address?: string;
  distance_miles?: number;
  price_range?: string;
  rating?: number;
  notes?: string;
  is_favorite: boolean;
}

interface Guidebook {
  welcome_message?: string;
  checkin_time: string;
  checkout_time: string;
  checkin_instructions?: string;
  checkout_instructions?: string;
  wifi_network?: string;
  wifi_password?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  host_phone?: string;
  host_email?: string;
  parking_info?: string;
  parking_instructions?: string;
  house_rules?: string;
  quiet_hours?: string;
  max_guests?: number;
  smoking_allowed: boolean;
  pets_allowed: boolean;
  parties_allowed: boolean;
  recommendations: Recommendation[];
}

export function GuestPortalPage() {
  const { accessCode } = useParams<{ accessCode: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [guestName, setGuestName] = useState<string>('');
  const [property, setProperty] = useState<any>(null);
  const [guidebook, setGuidebook] = useState<Guidebook | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    loadGuestPortal();
  }, [accessCode]);

  const loadGuestPortal = async () => {
    if (!accessCode) {
      setError('Access code is required');
      setLoading(false);
      return;
    }

    try {
      const response = await guidebookApi.getByAccessCode(accessCode);
      setGuestName(response.guest_name);
      setProperty(response.property);
      setGuidebook(response.guidebook);
    } catch (err: any) {
      setError(err.message || 'Failed to load guest portal');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      restaurant: '🍽️',
      attraction: '🎭',
      grocery: '🛒',
      pharmacy: '💊',
      hospital: '🏥',
      shopping: '🛍️',
      entertainment: '🎬',
      transportation: '🚗',
      gas_station: '⛽',
      bank: '🏦',
      other: '📍',
    };
    return icons[category] || '📍';
  };

  const categories = guidebook?.recommendations
    ? [...new Set(guidebook.recommendations.map((r) => r.category))]
    : [];

  const filteredRecommendations =
    selectedCategory === 'all'
      ? guidebook?.recommendations || []
      : guidebook?.recommendations.filter((r) => r.category === selectedCategory) || [];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="card max-w-md text-center">
          <div className="text-5xl mb-4">🔒</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!guidebook) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="card max-w-md text-center">
          <div className="text-5xl mb-4">📖</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Guidebook Not Available</h2>
          <p className="text-gray-600">The property guidebook has not been published yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-2">Welcome, {guestName}! 👋</h1>
          <h2 className="text-xl opacity-90">{property.name}</h2>
          <p className="text-sm opacity-80 mt-1">{property.address}</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Welcome Message */}
        {guidebook.welcome_message && (
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Welcome Message</h3>
            <p className="text-gray-700 whitespace-pre-wrap">{guidebook.welcome_message}</p>
          </div>
        )}

        {/* Check-in / Check-out */}
        <div className="grid grid-cols-2 gap-4">
          <div className="card">
            <div className="text-3xl mb-2">🔑</div>
            <h3 className="font-semibold text-gray-900 mb-1">Check-in</h3>
            <p className="text-2xl font-bold text-blue-600">{guidebook.checkin_time}</p>
            {guidebook.checkin_instructions && (
              <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">
                {guidebook.checkin_instructions}
              </p>
            )}
          </div>
          <div className="card">
            <div className="text-3xl mb-2">👋</div>
            <h3 className="font-semibold text-gray-900 mb-1">Check-out</h3>
            <p className="text-2xl font-bold text-blue-600">{guidebook.checkout_time}</p>
            {guidebook.checkout_instructions && (
              <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">
                {guidebook.checkout_instructions}
              </p>
            )}
          </div>
        </div>

        {/* WiFi */}
        {(guidebook.wifi_network || guidebook.wifi_password) && (
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">📶</span>
              <h3 className="text-lg font-semibold text-gray-900">WiFi Information</h3>
            </div>
            {guidebook.wifi_network && (
              <div className="mb-2">
                <span className="text-sm text-gray-600">Network: </span>
                <span className="font-mono font-semibold text-gray-900">
                  {guidebook.wifi_network}
                </span>
              </div>
            )}
            {guidebook.wifi_password && (
              <div>
                <span className="text-sm text-gray-600">Password: </span>
                <span className="font-mono font-semibold text-gray-900">
                  {guidebook.wifi_password}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Emergency & Host Contact */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(guidebook.emergency_contact || guidebook.emergency_phone) && (
            <div className="card bg-red-50 border-red-200">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">🚨</span>
                <h3 className="font-semibold text-gray-900">Emergency Contact</h3>
              </div>
              {guidebook.emergency_contact && (
                <p className="text-gray-700 mb-1">{guidebook.emergency_contact}</p>
              )}
              {guidebook.emergency_phone && (
                <a
                  href={`tel:${guidebook.emergency_phone}`}
                  className="text-blue-600 font-semibold hover:text-blue-700"
                >
                  {guidebook.emergency_phone}
                </a>
              )}
            </div>
          )}

          {(guidebook.host_phone || guidebook.host_email) && (
            <div className="card">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">👤</span>
                <h3 className="font-semibold text-gray-900">Host Contact</h3>
              </div>
              {guidebook.host_phone && (
                <div className="mb-1">
                  <a
                    href={`tel:${guidebook.host_phone}`}
                    className="text-blue-600 font-semibold hover:text-blue-700"
                  >
                    {guidebook.host_phone}
                  </a>
                </div>
              )}
              {guidebook.host_email && (
                <div>
                  <a
                    href={`mailto:${guidebook.host_email}`}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    {guidebook.host_email}
                  </a>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Parking */}
        {guidebook.parking_info && (
          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">🅿️</span>
              <h3 className="text-lg font-semibold text-gray-900">Parking</h3>
            </div>
            <p className="text-gray-700 whitespace-pre-wrap">{guidebook.parking_info}</p>
            {guidebook.parking_instructions && (
              <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">
                {guidebook.parking_instructions}
              </p>
            )}
          </div>
        )}

        {/* House Rules */}
        {guidebook.house_rules && (
          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">📋</span>
              <h3 className="text-lg font-semibold text-gray-900">House Rules</h3>
            </div>
            <p className="text-gray-700 whitespace-pre-wrap mb-3">{guidebook.house_rules}</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {guidebook.quiet_hours && (
                <div className="text-gray-600">
                  🤫 Quiet hours: <span className="font-medium">{guidebook.quiet_hours}</span>
                </div>
              )}
              {guidebook.max_guests && (
                <div className="text-gray-600">
                  👥 Max guests: <span className="font-medium">{guidebook.max_guests}</span>
                </div>
              )}
              <div className="text-gray-600">
                🚭 Smoking: {guidebook.smoking_allowed ? '✅ Allowed' : '❌ Not allowed'}
              </div>
              <div className="text-gray-600">
                🐾 Pets: {guidebook.pets_allowed ? '✅ Allowed' : '❌ Not allowed'}
              </div>
              <div className="text-gray-600">
                🎉 Parties: {guidebook.parties_allowed ? '✅ Allowed' : '❌ Not allowed'}
              </div>
            </div>
          </div>
        )}

        {/* Local Recommendations */}
        {guidebook.recommendations && guidebook.recommendations.length > 0 && (
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">🗺️</span>
              <h3 className="text-lg font-semibold text-gray-900">Local Recommendations</h3>
            </div>

            {/* Category Filter */}
            <div className="flex gap-2 flex-wrap mb-4">
              <button
                onClick={() => setSelectedCategory('all')}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  selectedCategory === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    selectedCategory === category
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {getCategoryIcon(category)} {category.replace('_', ' ')}
                </button>
              ))}
            </div>

            {/* Recommendations List */}
            <div className="space-y-3">
              {filteredRecommendations.map((rec, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{getCategoryIcon(rec.category)}</span>
                      <h4 className="font-semibold text-gray-900">{rec.name}</h4>
                      {rec.is_favorite && <span className="text-yellow-500">⭐</span>}
                    </div>
                    {rec.rating && (
                      <span className="text-sm font-medium text-gray-600">
                        ⭐ {rec.rating.toFixed(1)}
                      </span>
                    )}
                  </div>
                  {rec.description && (
                    <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
                  )}
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
                    {rec.address && <span>📍 {rec.address}</span>}
                    {rec.distance_miles && <span>🚗 {rec.distance_miles} miles</span>}
                    {rec.price_range && <span>💰 {rec.price_range}</span>}
                  </div>
                  {(rec.phone || rec.website) && (
                    <div className="flex gap-3 mt-2">
                      {rec.phone && (
                        <a
                          href={`tel:${rec.phone}`}
                          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                        >
                          📞 Call
                        </a>
                      )}
                      {rec.website && (
                        <a
                          href={rec.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                        >
                          🌐 Website
                        </a>
                      )}
                    </div>
                  )}
                  {rec.notes && (
                    <p className="text-sm text-gray-500 italic mt-2 border-t border-gray-200 pt-2">
                      {rec.notes}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="max-w-4xl mx-auto px-4 py-8 text-center text-sm text-gray-500">
        <p>Enjoy your stay! 🏡</p>
      </div>
    </div>
  );
}
