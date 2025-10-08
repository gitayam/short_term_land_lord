import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { propertiesApi } from '../../services/api';
import type { Property } from '../../types';

export function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [property, setProperty] = useState<Property | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) {
      loadProperty(id);
    }
  }, [id]);

  const loadProperty = async (propertyId: string) => {
    try {
      const data = await propertiesApi.get(propertyId);
      setProperty(data.property);
    } catch (err: any) {
      setError(err.message || 'Failed to load property');
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

  if (error || !property) {
    return (
      <div className="card text-center py-12">
        <div className="text-5xl mb-4">❌</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Property Not Found</h3>
        <p className="text-gray-600 mb-6">{error}</p>
        <Link to="/properties" className="btn-secondary">
          Back to Properties
        </Link>
      </div>
    );
  }

  return (
    <div>
      <Link to="/properties" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">
        ← Back to Properties
      </Link>

      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {property.name || 'Unnamed Property'}
          </h1>
          <p className="text-gray-600">{property.address}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary">Edit</button>
          <button className="btn-danger">Delete</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Details</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-600">Address</dt>
              <dd className="text-gray-900">{property.address}</dd>
            </div>
            {property.city && (
              <div>
                <dt className="text-sm font-medium text-gray-600">City</dt>
                <dd className="text-gray-900">{property.city}</dd>
              </div>
            )}
            {property.state && (
              <div>
                <dt className="text-sm font-medium text-gray-600">State</dt>
                <dd className="text-gray-900">{property.state}</dd>
              </div>
            )}
            {property.bedrooms && (
              <div>
                <dt className="text-sm font-medium text-gray-600">Bedrooms</dt>
                <dd className="text-gray-900">{property.bedrooms}</dd>
              </div>
            )}
            {property.bathrooms && (
              <div>
                <dt className="text-sm font-medium text-gray-600">Bathrooms</dt>
                <dd className="text-gray-900">{property.bathrooms}</dd>
              </div>
            )}
            <div>
              <dt className="text-sm font-medium text-gray-600">Status</dt>
              <dd>
                <span className="badge badge-completed">{property.status || 'active'}</span>
              </dd>
            </div>
          </dl>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-2">
            <Link
              to={`/calendar?property=${property.id}`}
              className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              📅 View Calendar
            </Link>
            <Link
              to={`/tasks?property=${property.id}`}
              className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              ✓ View Tasks
            </Link>
            <Link
              to={`/cleaning?property=${property.id}`}
              className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              🧹 Cleaning History
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
