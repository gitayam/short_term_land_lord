/**
 * Favorites/Wishlist Page
 * Shows all properties saved by the guest
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useFavoritesStore } from '../stores/favoritesStore';
import { FavoriteButton } from '../components/FavoriteButton';

interface Property {
  id: string;
  slug: string;
  name: string;
  city: string;
  state: string;
  bedrooms: number;
  bathrooms: number;
  nightly_rate?: number;
  max_guests?: number;
  property_type?: string;
  images?: PropertyImage[];
  description?: string;
  average_rating?: number;
  total_reviews?: number;
}

interface PropertyImage {
  id: number;
  image_url: string;
  caption?: string;
  display_order: number;
  is_primary: boolean;
}

export function FavoritesPage() {
  const { favorites, clearFavorites } = useFavoritesStore();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFavoriteProperties();
  }, [favorites]);

  const loadFavoriteProperties = async () => {
    if (favorites.length === 0) {
      setProperties([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Fetch all favorite properties
      const propertyPromises = favorites.map(slug =>
        fetch(`/api/properties/${slug}`).then(res => {
          if (!res.ok) return null;
          return res.json();
        })
      );

      const results = await Promise.all(propertyPromises);
      const validProperties = results.filter(p => p !== null);
      setProperties(validProperties);
    } catch (err) {
      console.error('Error loading favorites:', err);
      setError('Failed to load favorite properties');
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = () => {
    if (confirm('Remove all properties from your favorites?')) {
      clearFavorites();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between">
            <div>
              <Link
                to="/"
                className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700 mb-4"
              >
                <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Search
              </Link>
              <h1 className="text-3xl font-bold text-gray-900">My Favorites</h1>
              <p className="mt-2 text-gray-600">
                {favorites.length === 0
                  ? 'No saved properties yet'
                  : `${favorites.length} ${favorites.length === 1 ? 'property' : 'properties'} saved`}
              </p>
            </div>
            {favorites.length > 0 && (
              <button
                onClick={handleClearAll}
                className="px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
              >
                Clear All
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-800">{error}</p>
            <button
              onClick={loadFavoriteProperties}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        ) : favorites.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-sm p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="mb-6">
                <svg
                  className="w-24 h-24 mx-auto text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">No favorites yet</h2>
              <p className="text-gray-600 mb-6">
                Start exploring properties and save your favorites by clicking the heart icon
              </p>
              <Link
                to="/"
                className="inline-block px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                Browse Properties
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {properties.map((property) => {
              const primaryImage = property.images?.find(img => img.is_primary) || property.images?.[0];

              return (
                <Link
                  key={property.slug}
                  to={`/property/${property.slug}`}
                  className="group bg-white rounded-xl shadow-sm hover:shadow-lg transition-all overflow-hidden"
                >
                  {/* Property Image */}
                  <div className="relative h-48 overflow-hidden bg-gray-200">
                    {primaryImage ? (
                      <img
                        src={primaryImage.image_url}
                        alt={property.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-100 to-purple-100">
                        <span className="text-4xl">🏠</span>
                      </div>
                    )}
                    {/* Favorite Button */}
                    <div className="absolute top-3 right-3">
                      <FavoriteButton slug={property.slug} size="md" />
                    </div>
                    {/* Rating Badge */}
                    {property.average_rating && property.total_reviews && property.total_reviews > 0 && (
                      <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-sm px-2 py-1 rounded-lg flex items-center gap-1">
                        <span className="text-yellow-500">★</span>
                        <span className="font-semibold text-sm">{property.average_rating.toFixed(1)}</span>
                        <span className="text-xs text-gray-600">({property.total_reviews})</span>
                      </div>
                    )}
                  </div>

                  {/* Property Info */}
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        {property.property_type && (
                          <p className="text-xs text-gray-500 capitalize mb-1">{property.property_type}</p>
                        )}
                        <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 line-clamp-1">
                          {property.name}
                        </h3>
                      </div>
                    </div>

                    <p className="text-sm text-gray-600 mb-3">
                      {property.city}, {property.state}
                    </p>

                    <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                      <span>{property.bedrooms} bed</span>
                      <span>•</span>
                      <span>{property.bathrooms} bath</span>
                      {property.max_guests && (
                        <>
                          <span>•</span>
                          <span>{property.max_guests} guests</span>
                        </>
                      )}
                    </div>

                    {property.nightly_rate && (
                      <div className="pt-3 border-t border-gray-200">
                        <p className="text-lg font-bold text-gray-900">
                          ${property.nightly_rate}
                          <span className="text-sm font-normal text-gray-600"> / night</span>
                        </p>
                      </div>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
