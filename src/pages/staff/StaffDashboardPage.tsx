/**
 * Staff Dashboard Page
 * Mobile-friendly dashboard for service staff (cleaners, handymen, electricians, plumbers)
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface DashboardStats {
  assigned_properties: number;
  pending_repairs: number;
  unread_notifications: number;
  recent_work_logs: number;
}

interface Property {
  assignment_id: string;
  role_type: string;
  assigned_at: string;
  property_id: string;
  name: string;
  address: string;
  city: string;
  state: string;
}

interface RepairRequest {
  id: string;
  title: string;
  description: string;
  location: string | null;
  severity: 'low' | 'medium' | 'high' | 'urgent';
  status: string;
  property_name: string;
  property_address: string;
  reported_by_name: string;
  created_at: string;
}

interface Notification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  link: string | null;
  created_at: string;
}

export function StaffDashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [repairs, setRepairs] = useState<RepairRequest[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch('/api/staff/dashboard', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load dashboard');
      }

      const data = await response.json();
      setStats(data.stats);
      setProperties(data.assigned_properties || []);
      setRepairs(data.pending_repairs || []);
      setNotifications(data.notifications || []);
    } catch (err: any) {
      setError(err.message);
      if (err.message.includes('Unauthorized') || err.message.includes('authenticated')) {
        setTimeout(() => navigate('/login'), 2000);
      }
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'urgent':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4 mx-auto"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="card max-w-md text-center">
          <div className="text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button onClick={loadDashboard} className="btn-primary">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">Staff Dashboard 🔧</h1>
          <p className="text-sm opacity-90 mt-1">Manage your properties and tasks</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="card text-center">
            <div className="text-3xl font-bold text-blue-600">{stats?.assigned_properties || 0}</div>
            <div className="text-sm text-gray-600 mt-1">Properties</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-orange-600">{stats?.pending_repairs || 0}</div>
            <div className="text-sm text-gray-600 mt-1">Repairs</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-purple-600">{stats?.unread_notifications || 0}</div>
            <div className="text-sm text-gray-600 mt-1">Notifications</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-green-600">{stats?.recent_work_logs || 0}</div>
            <div className="text-sm text-gray-600 mt-1">Work Logs</div>
          </div>
        </div>

        {/* Pending Repairs */}
        {repairs.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-3">Pending Repairs</h2>
            <div className="space-y-3">
              {repairs.map((repair) => (
                <div
                  key={repair.id}
                  className="card cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => navigate(`/app/repair-requests/${repair.id}`)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-gray-900">{repair.title}</h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded border ${getSeverityColor(repair.severity)}`}>
                      {repair.severity.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mb-2 line-clamp-2">{repair.description}</p>
                  <div className="text-xs text-gray-500">
                    <div>📍 {repair.property_name}</div>
                    {repair.location && <div className="mt-1">🔧 {repair.location}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Assigned Properties */}
        {properties.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-3">Assigned Properties</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {properties.map((property) => (
                <div
                  key={property.assignment_id}
                  className="card cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => navigate(`/app/properties/${property.property_id}`)}
                >
                  <h3 className="font-semibold text-gray-900 mb-1">{property.name}</h3>
                  <p className="text-sm text-gray-600 mb-2">
                    {property.city}, {property.state}
                  </p>
                  {property.role_type && (
                    <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                      {property.role_type}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Notifications */}
        {notifications.length > 0 && (
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-xl font-bold text-gray-900">Recent Notifications</h2>
              <button
                onClick={() => navigate('/app/staff/notifications')}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                View All →
              </button>
            </div>
            <div className="space-y-2">
              {notifications.slice(0, 5).map((notification) => (
                <div key={notification.id} className="card bg-blue-50 border-blue-200">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-gray-900">{notification.title}</h4>
                      <p className="text-sm text-gray-700 mt-1">{notification.message}</p>
                    </div>
                    <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                      {new Date(notification.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {properties.length === 0 && repairs.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <div className="text-6xl mb-4">🏗️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Assignments Yet</h3>
            <p className="text-gray-600">
              You'll see your assigned properties and repair requests here once they're assigned to you.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
