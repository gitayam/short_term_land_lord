import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { propertiesApi } from '../../services/api';
import type { Property } from '../../types';

export function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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
        <button className="btn-primary">+ Add Property</button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {properties.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">🏠</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No properties yet</h3>
          <p className="text-gray-600 mb-6">Get started by adding your first property</p>
          <button className="btn-primary">Add Your First Property</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {properties.map((property) => (
            <Link
              key={property.id}
              to={`/properties/${property.id}`}
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
