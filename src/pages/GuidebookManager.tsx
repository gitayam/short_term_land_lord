/**
 * Guidebook Manager Page
 * Host interface for creating and managing property guidebooks
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface Property {
  id: number;
  name: string;
  slug: string;
}

interface GuidebookSection {
  id?: number;
  section_type: string;
  title: string;
  content: string;
  display_order: number;
  icon: string;
  is_published: boolean;
}

interface Recommendation {
  id?: number;
  category: string;
  name: string;
  description: string;
  address: string;
  phone: string;
  website: string;
  distance_miles?: number;
  walking_time_minutes?: number;
  price_level?: number;
  rating?: number;
  hours: string;
  tags: string[];
  is_featured: boolean;
  display_order: number;
}

export function GuidebookManager() {
  const navigate = useNavigate();
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'sections' | 'recommendations'>('sections');

  // Sections state
  const [sections, setSections] = useState<GuidebookSection[]>([]);
  const [editingSection, setEditingSection] = useState<GuidebookSection | null>(null);

  // Recommendations state
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [editingRecommendation, setEditingRecommendation] = useState<Recommendation | null>(null);

  useEffect(() => {
    loadProperties();
  }, []);

  useEffect(() => {
    if (selectedProperty) {
      loadGuidebook();
    }
  }, [selectedProperty]);

  const loadProperties = async () => {
    try {
      const response = await fetch('/api/calendar/availability?year=2025&month=10');
      const data = await response.json();
      if (data.properties) {
        setProperties(data.properties);
        if (data.properties.length > 0) {
          setSelectedProperty(data.properties[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading properties:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadGuidebook = async () => {
    if (!selectedProperty) return;

    const property = properties.find(p => p.id === selectedProperty);
    if (!property) return;

    try {
      const response = await fetch(`/api/guidebook/${property.slug || property.id}`);
      const data = await response.json();

      if (response.ok) {
        setSections(data.sections || []);

        // Flatten recommendations from grouped format
        const allRecs: Recommendation[] = [];
        Object.entries(data.recommendations || {}).forEach(([category, recs]: [string, any]) => {
          recs.forEach((rec: any) => allRecs.push(rec));
        });
        setRecommendations(allRecs);
      }
    } catch (error) {
      console.error('Error loading guidebook:', error);
    }
  };

  const sectionTypes = [
    { value: 'welcome', label: 'Welcome Message', icon: '👋' },
    { value: 'access', label: 'Access & Check-in', icon: '🔑' },
    { value: 'house_rules', label: 'House Rules', icon: '📋' },
    { value: 'property_guide', label: 'Property Guide', icon: '🏠' },
    { value: 'emergency', label: 'Emergency Info', icon: '🚨' },
    { value: 'local_tips', label: 'Local Tips', icon: '💡' },
  ];

  const recommendationCategories = [
    { value: 'restaurant', label: 'Restaurants', icon: '🍽️' },
    { value: 'coffee', label: 'Coffee & Cafes', icon: '☕' },
    { value: 'grocery', label: 'Grocery Stores', icon: '🛒' },
    { value: 'attraction', label: 'Attractions', icon: '🎭' },
    { value: 'park', label: 'Parks & Nature', icon: '🌳' },
    { value: 'shopping', label: 'Shopping', icon: '🛍️' },
    { value: 'activity', label: 'Activities', icon: '⚽' },
  ];

  const handleSaveSection = async () => {
    if (!editingSection || !selectedProperty) return;

    try {
      const method = editingSection.id ? 'PUT' : 'POST';
      const payload = {
        ...editingSection,
        property_id: selectedProperty
      };

      const response = await fetch('/api/guidebook/sections', {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        // Reload guidebook to show updated data
        await loadGuidebook();
        setEditingSection(null);
        alert(editingSection.id ? 'Section updated successfully!' : 'Section created successfully!');
      } else {
        alert(`Error: ${data.error || 'Failed to save section'}`);
      }
    } catch (error) {
      console.error('Error saving section:', error);
      alert('Failed to save section. Please try again.');
    }
  };

  const handleSaveRecommendation = async () => {
    if (!editingRecommendation || !selectedProperty) return;

    try {
      const method = editingRecommendation.id ? 'PUT' : 'POST';
      const payload = {
        ...editingRecommendation,
        property_id: selectedProperty
      };

      const response = await fetch('/api/guidebook/recommendations', {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        // Reload guidebook to show updated data
        await loadGuidebook();
        setEditingRecommendation(null);
        alert(editingRecommendation.id ? 'Recommendation updated successfully!' : 'Recommendation created successfully!');
      } else {
        alert(`Error: ${data.error || 'Failed to save recommendation'}`);
      }
    } catch (error) {
      console.error('Error saving recommendation:', error);
      alert('Failed to save recommendation. Please try again.');
    }
  };

  const handleDeleteSection = async (id: number) => {
    if (!confirm('Are you sure you want to delete this section?')) return;

    try {
      const response = await fetch(`/api/guidebook/sections?id=${id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadGuidebook();
        alert('Section deleted successfully!');
      } else {
        const data = await response.json();
        alert(`Error: ${data.error || 'Failed to delete section'}`);
      }
    } catch (error) {
      console.error('Error deleting section:', error);
      alert('Failed to delete section. Please try again.');
    }
  };

  const handleDeleteRecommendation = async (id: number) => {
    if (!confirm('Are you sure you want to delete this recommendation?')) return;

    try {
      const response = await fetch(`/api/guidebook/recommendations?id=${id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadGuidebook();
        alert('Recommendation deleted successfully!');
      } else {
        const data = await response.json();
        alert(`Error: ${data.error || 'Failed to delete recommendation'}`);
      }
    } catch (error) {
      console.error('Error deleting recommendation:', error);
      alert('Failed to delete recommendation. Please try again.');
    }
  };

  const newSection = (): GuidebookSection => ({
    section_type: 'welcome',
    title: '',
    content: '',
    display_order: sections.length + 1,
    icon: '👋',
    is_published: true,
  });

  const newRecommendation = (): Recommendation => ({
    category: 'restaurant',
    name: '',
    description: '',
    address: '',
    phone: '',
    website: '',
    hours: '',
    tags: [],
    is_featured: false,
    display_order: recommendations.length + 1,
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const selectedProp = properties.find(p => p.id === selectedProperty);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Guidebook Manager</h1>
              <p className="text-sm text-gray-600 mt-1">Create helpful guides for your guests</p>
            </div>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              ← Back to Calendar
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Property Selector */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Property</label>
          <select
            value={selectedProperty || ''}
            onChange={(e) => setSelectedProperty(parseInt(e.target.value))}
            className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg"
          >
            {properties.map((property) => (
              <option key={property.id} value={property.id}>
                {property.name}
              </option>
            ))}
          </select>
        </div>

        {selectedProperty && (
          <>
            {/* Tabs */}
            <div className="bg-white rounded-lg shadow mb-6">
              <div className="border-b border-gray-200">
                <div className="flex">
                  <button
                    onClick={() => setActiveTab('sections')}
                    className={`px-6 py-3 font-medium transition-colors ${
                      activeTab === 'sections'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    📖 Guidebook Sections ({sections.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('recommendations')}
                    className={`px-6 py-3 font-medium transition-colors ${
                      activeTab === 'recommendations'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    📍 Local Recommendations ({recommendations.length})
                  </button>
                </div>
              </div>

              <div className="p-6">
                {activeTab === 'sections' ? (
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <p className="text-sm text-gray-600">
                        Create sections to help guests with check-in, house rules, and local tips.
                      </p>
                      <button
                        onClick={() => setEditingSection(newSection())}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        + Add Section
                      </button>
                    </div>

                    {sections.length === 0 ? (
                      <div className="text-center py-12 bg-gray-50 rounded-lg">
                        <p className="text-gray-500">No sections yet. Click "Add Section" to create your first one!</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {sections.map((section) => (
                          <div key={section.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-2xl">{section.icon}</span>
                                  <h3 className="font-semibold text-gray-900">{section.title}</h3>
                                  {!section.is_published && (
                                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Draft</span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600 line-clamp-2">{section.content}</p>
                              </div>
                              <div className="ml-4 flex gap-2">
                                <button
                                  onClick={() => setEditingSection(section)}
                                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={() => section.id && handleDeleteSection(section.id)}
                                  className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                                >
                                  Delete
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <p className="text-sm text-gray-600">
                        Add local restaurants, attractions, and activities your guests will love.
                      </p>
                      <button
                        onClick={() => setEditingRecommendation(newRecommendation())}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        + Add Recommendation
                      </button>
                    </div>

                    {recommendations.length === 0 ? (
                      <div className="text-center py-12 bg-gray-50 rounded-lg">
                        <p className="text-gray-500">No recommendations yet. Click "Add Recommendation" to create your first one!</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {recommendations.map((rec) => (
                          <div key={rec.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-xl">{recommendationCategories.find(c => c.value === rec.category)?.icon || '📌'}</span>
                                  <h3 className="font-semibold text-gray-900">{rec.name}</h3>
                                  {rec.is_featured && (
                                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">⭐ Featured</span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
                                <div className="flex items-center gap-3 text-xs text-gray-500">
                                  {rec.distance_miles && <span>{rec.distance_miles} mi away</span>}
                                  {rec.rating && <span>★ {rec.rating}</span>}
                                  {rec.price_level && <span>{'$'.repeat(rec.price_level)}</span>}
                                </div>
                              </div>
                              <div className="ml-4 flex gap-2">
                                <button
                                  onClick={() => setEditingRecommendation(rec)}
                                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={() => rec.id && handleDeleteRecommendation(rec.id)}
                                  className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                                >
                                  Delete
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Section Editor Modal */}
      {editingSection && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4" onClick={() => setEditingSection(null)}>
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="bg-blue-600 text-white p-6">
              <h2 className="text-2xl font-bold">{editingSection.id ? 'Edit Section' : 'New Section'}</h2>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Section Type</label>
                <select
                  value={editingSection.section_type}
                  onChange={(e) => {
                    const type = sectionTypes.find(t => t.value === e.target.value);
                    setEditingSection({
                      ...editingSection,
                      section_type: e.target.value,
                      icon: type?.icon || '📄'
                    });
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                >
                  {sectionTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.icon} {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
                <input
                  type="text"
                  value={editingSection.title}
                  onChange={(e) => setEditingSection({ ...editingSection, title: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  placeholder="e.g., Welcome to our home!"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Content</label>
                <textarea
                  value={editingSection.content}
                  onChange={(e) => setEditingSection({ ...editingSection, content: e.target.value })}
                  rows={8}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  placeholder="Write your guidebook content here..."
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={editingSection.is_published}
                  onChange={(e) => setEditingSection({ ...editingSection, is_published: e.target.checked })}
                  className="w-5 h-5"
                />
                <label className="text-sm text-gray-700">Published (visible to guests)</label>
              </div>
            </div>

            <div className="border-t border-gray-200 p-4 flex gap-3">
              <button
                onClick={() => setEditingSection(null)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSection}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Save Section
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Recommendation Editor Modal */}
      {editingRecommendation && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4" onClick={() => setEditingRecommendation(null)}>
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="bg-purple-600 text-white p-6">
              <h2 className="text-2xl font-bold">{editingRecommendation.id ? 'Edit Recommendation' : 'New Recommendation'}</h2>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <select
                    value={editingRecommendation.category}
                    onChange={(e) => setEditingRecommendation({ ...editingRecommendation, category: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  >
                    {recommendationCategories.map(cat => (
                      <option key={cat.value} value={cat.value}>
                        {cat.icon} {cat.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                  <input
                    type="text"
                    value={editingRecommendation.name}
                    onChange={(e) => setEditingRecommendation({ ...editingRecommendation, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    placeholder="Business name"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={editingRecommendation.description}
                  onChange={(e) => setEditingRecommendation({ ...editingRecommendation, description: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  placeholder="Why you recommend this place..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                  <input
                    type="text"
                    value={editingRecommendation.address}
                    onChange={(e) => setEditingRecommendation({ ...editingRecommendation, address: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                  <input
                    type="text"
                    value={editingRecommendation.phone}
                    onChange={(e) => setEditingRecommendation({ ...editingRecommendation, phone: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Website</label>
                  <input
                    type="url"
                    value={editingRecommendation.website}
                    onChange={(e) => setEditingRecommendation({ ...editingRecommendation, website: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Hours</label>
                  <input
                    type="text"
                    value={editingRecommendation.hours}
                    onChange={(e) => setEditingRecommendation({ ...editingRecommendation, hours: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    placeholder="Mon-Fri 9am-5pm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Distance (mi)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingRecommendation.distance_miles || ''}
                    onChange={(e) => setEditingRecommendation({ ...editingRecommendation, distance_miles: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Rating (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    step="0.1"
                    value={editingRecommendation.rating || ''}
                    onChange={(e) => setEditingRecommendation({ ...editingRecommendation, rating: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Price Level (1-4)</label>
                  <input
                    type="number"
                    min="1"
                    max="4"
                    value={editingRecommendation.price_level || ''}
                    onChange={(e) => setEditingRecommendation({ ...editingRecommendation, price_level: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={editingRecommendation.is_featured}
                  onChange={(e) => setEditingRecommendation({ ...editingRecommendation, is_featured: e.target.checked })}
                  className="w-5 h-5"
                />
                <label className="text-sm text-gray-700">⭐ Featured (show at top)</label>
              </div>
            </div>

            <div className="border-t border-gray-200 p-4 flex gap-3">
              <button
                onClick={() => setEditingRecommendation(null)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveRecommendation}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                Save Recommendation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
