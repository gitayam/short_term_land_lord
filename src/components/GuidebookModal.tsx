/**
 * Property Guidebook Modal
 * Displays guidebook sections and local recommendations
 */

import { useState, useEffect } from 'react';

interface GuidebookSection {
  id: number;
  section_type: string;
  title: string;
  content: string;
  display_order: number;
  icon?: string;
}

interface Recommendation {
  id: number;
  category: string;
  name: string;
  description?: string;
  address?: string;
  phone?: string;
  website?: string;
  distance_miles?: number;
  walking_time_minutes?: number;
  price_level?: number;
  rating?: number;
  hours?: string;
  tags?: string[];
  is_featured: boolean;
}

interface GuidebookModalProps {
  propertySlug: string;
  propertyName: string;
  isOpen: boolean;
  onClose: () => void;
}

export function GuidebookModal({ propertySlug, propertyName, isOpen, onClose }: GuidebookModalProps) {
  const [loading, setLoading] = useState(true);
  const [sections, setSections] = useState<GuidebookSection[]>([]);
  const [recommendations, setRecommendations] = useState<Record<string, Recommendation[]>>({});
  const [activeTab, setActiveTab] = useState<'guide' | 'recommendations'>('guide');

  useEffect(() => {
    if (isOpen && propertySlug) {
      loadGuidebook();
    }
  }, [isOpen, propertySlug]);

  const loadGuidebook = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/guidebook/${propertySlug}`);
      const data = await response.json();

      if (response.ok) {
        setSections(data.sections || []);
        setRecommendations(data.recommendations || {});
      }
    } catch (error) {
      console.error('Error loading guidebook:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const categoryIcons: Record<string, string> = {
    restaurant: '🍽️',
    coffee: '☕',
    grocery: '🛒',
    attraction: '🎭',
    park: '🌳',
    shopping: '🛍️',
    activity: '⚽',
  };

  const categoryLabels: Record<string, string> = {
    restaurant: 'Restaurants',
    coffee: 'Coffee & Cafes',
    grocery: 'Grocery Stores',
    attraction: 'Attractions',
    park: 'Parks & Nature',
    shopping: 'Shopping',
    activity: 'Activities',
  };

  const renderPriceLevel = (level?: number) => {
    if (!level) return null;
    return <span className="text-gray-500">{'$'.repeat(level)}</span>;
  };

  const renderRating = (rating?: number) => {
    if (!rating) return null;
    return (
      <span className="flex items-center gap-1 text-sm">
        <span className="text-yellow-500">★</span>
        <span className="text-gray-700">{rating.toFixed(1)}</span>
      </span>
    );
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-1">Property Guidebook</h2>
              <p className="text-blue-100">{propertyName}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-3xl font-bold"
              aria-label="Close guidebook"
            >
              ×
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 bg-gray-50">
          <div className="flex">
            <button
              onClick={() => setActiveTab('guide')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'guide'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📖 Property Guide
            </button>
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'recommendations'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📍 Local Recommendations
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : activeTab === 'guide' ? (
            <div className="space-y-6">
              {sections.length === 0 ? (
                <p className="text-gray-500 text-center py-12">
                  No guidebook available for this property yet.
                </p>
              ) : (
                sections.map((section) => (
                  <div key={section.id} className="bg-gray-50 rounded-lg p-5">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                      {section.icon && <span className="text-2xl">{section.icon}</span>}
                      {section.title}
                    </h3>
                    <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                      {section.content}
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="space-y-8">
              {Object.keys(recommendations).length === 0 ? (
                <p className="text-gray-500 text-center py-12">
                  No recommendations available yet.
                </p>
              ) : (
                Object.entries(recommendations).map(([category, items]) => (
                  <div key={category}>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      <span className="text-2xl">{categoryIcons[category] || '📌'}</span>
                      {categoryLabels[category] || category}
                    </h3>
                    <div className="grid gap-4">
                      {items.map((rec) => (
                        <div
                          key={rec.id}
                          className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-semibold text-gray-900">{rec.name}</h4>
                              <div className="flex items-center gap-3 mt-1">
                                {renderPriceLevel(rec.price_level)}
                                {renderRating(rec.rating)}
                                {rec.distance_miles && (
                                  <span className="text-xs text-gray-500">
                                    {rec.distance_miles.toFixed(1)} mi away
                                  </span>
                                )}
                                {rec.walking_time_minutes && (
                                  <span className="text-xs text-gray-500">
                                    ({rec.walking_time_minutes} min walk)
                                  </span>
                                )}
                              </div>
                            </div>
                            {rec.is_featured && (
                              <span className="bg-yellow-100 text-yellow-800 text-xs font-medium px-2 py-1 rounded">
                                ⭐ Featured
                              </span>
                            )}
                          </div>

                          {rec.description && (
                            <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
                          )}

                          {rec.hours && (
                            <p className="text-xs text-gray-500 mb-2">🕒 {rec.hours}</p>
                          )}

                          {rec.tags && rec.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-2">
                              {rec.tags.map((tag, idx) => (
                                <span
                                  key={idx}
                                  className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}

                          <div className="flex gap-3 mt-3">
                            {rec.phone && (
                              <a
                                href={`tel:${rec.phone}`}
                                className="text-xs text-blue-600 hover:text-blue-800"
                              >
                                📞 Call
                              </a>
                            )}
                            {rec.address && (
                              <a
                                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(rec.address)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-blue-600 hover:text-blue-800"
                              >
                                🗺️ Directions
                              </a>
                            )}
                            {rec.website && (
                              <a
                                href={rec.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-blue-600 hover:text-blue-800"
                              >
                                🌐 Website
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 bg-gray-50 p-4 text-center">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
