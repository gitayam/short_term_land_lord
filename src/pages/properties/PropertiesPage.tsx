import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { propertiesApi } from '../../services/api';
import type { Property } from '../../types';

export function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    street_address: '',
    city: '',
    state: '',
    zip_code: '',
    property_type: 'house',
    bedrooms: '',
    bathrooms: '',
    description: '',
  });

  useEffect(() => {
    loadProperties();
  }, []);

  const loadProperties = async () => {
    try {
      const data = await propertiesApi.list();
      setProperties(data.properties || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load properties');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Auto-generate full address from structured fields
      const fullAddress = [
        formData.street_address,
        formData.city,
        formData.state,
        formData.zip_code
      ].filter(Boolean).join(', ');

      await propertiesApi.create({
        ...formData,
        address: fullAddress || formData.address, // Use generated address or fallback
      });
      setShowCreateForm(false);
      setFormData({
        name: '',
        address: '',
        street_address: '',
        city: '',
        state: '',
        zip_code: '',
        property_type: 'house',
        bedrooms: '',
        bathrooms: '',
        description: '',
      });
      loadProperties();
    } catch (error: any) {
      alert(error.message || 'Failed to create property');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Properties</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showCreateForm ? 'Cancel' : '+ Add Property'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {showCreateForm && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Add New Property</h2>
          <form onSubmit={handleCreateProperty} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Property Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input"
                  placeholder="e.g., Beach House"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Property Type
                </label>
                <select
                  value={formData.property_type}
                  onChange={(e) => setFormData({ ...formData, property_type: e.target.value })}
                  className="input"
                >
                  <optgroup label="Houses & Apartments">
                    <option value="house">House</option>
                    <option value="apartment">Apartment</option>
                    <option value="condo">Condo</option>
                    <option value="townhouse">Townhouse</option>
                    <option value="loft">Loft</option>
                    <option value="studio">Studio</option>
                  </optgroup>
                  <optgroup label="Secondary Units">
                    <option value="suite">Suite</option>
                    <option value="guesthouse">Guesthouse</option>
                    <option value="guest-suite">Guest Suite</option>
                    <option value="in-law-unit">In-Law Unit</option>
                  </optgroup>
                  <optgroup label="Luxury & Unique">
                    <option value="villa">Villa</option>
                    <option value="cottage">Cottage</option>
                    <option value="bungalow">Bungalow</option>
                    <option value="cabin">Cabin</option>
                    <option value="chalet">Chalet</option>
                    <option value="castle">Castle</option>
                  </optgroup>
                  <optgroup label="Unique Spaces">
                    <option value="treehouse">Treehouse</option>
                    <option value="yurt">Yurt</option>
                    <option value="tiny-house">Tiny House</option>
                    <option value="barn">Barn</option>
                    <option value="farm-stay">Farm Stay</option>
                    <option value="houseboat">Houseboat</option>
                  </optgroup>
                  <optgroup label="Commercial">
                    <option value="bed-and-breakfast">Bed & Breakfast</option>
                    <option value="boutique-hotel">Boutique Hotel</option>
                    <option value="hostel">Hostel</option>
                  </optgroup>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Street Address
                </label>
                <input
                  type="text"
                  value={formData.street_address}
                  onChange={(e) => setFormData({ ...formData, street_address: e.target.value })}
                  className="input"
                  placeholder="123 Main St"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  City
                </label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="input"
                  placeholder="City"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  State
                </label>
                <input
                  type="text"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  className="input"
                  placeholder="CA"
                  maxLength={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ZIP Code
                </label>
                <input
                  type="text"
                  value={formData.zip_code}
                  onChange={(e) => setFormData({ ...formData, zip_code: e.target.value })}
                  className="input"
                  placeholder="90210"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bedrooms
                </label>
                <input
                  type="number"
                  value={formData.bedrooms}
                  onChange={(e) => setFormData({ ...formData, bedrooms: e.target.value })}
                  className="input"
                  placeholder="3"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bathrooms
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={formData.bathrooms}
                  onChange={(e) => setFormData({ ...formData, bathrooms: e.target.value })}
                  className="input"
                  placeholder="2"
                  min="0"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="input"
                rows={3}
                placeholder="Property description..."
              />
            </div>

            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Property
              </button>
            </div>
          </form>
        </div>
      )}

      {properties.length === 0 && !showCreateForm ? (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">🏠</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No properties yet</h3>
          <p className="text-gray-600 mb-6">Get started by adding your first property</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Your First Property
          </button>
        </div>
      ) : null}

      {properties.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {properties.map((property) => (
            <Link
              key={property.id}
              to={`/app/properties/${property.id}`}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {property.name || 'Unnamed Property'}
                </h3>
                <span className="badge badge-completed">
                  {property.status || 'active'}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{property.address}</p>
              {property.city && (
                <p className="text-xs text-gray-500">
                  {property.city}, {property.state} {property.zip_code}
                </p>
              )}
              {property.bedrooms && property.bathrooms && (
                <div className="mt-4 flex gap-4 text-sm text-gray-600">
                  <span>🛏 {property.bedrooms} bed</span>
                  <span>🛁 {property.bathrooms} bath</span>
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
