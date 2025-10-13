import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { propertiesApi, tasksApi, cleaningApi } from '../services/api';

export function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    properties: 0,
    tasks: 0,
    cleaningSessions: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [propertiesData, tasksData, cleaningData] = await Promise.all([
        propertiesApi.list(),
        tasksApi.list({ status: 'PENDING' }),
        cleaningApi.list({ status: 'in_progress' }),
      ]);

      setStats({
        properties: propertiesData.properties?.length || 0,
        tasks: tasksData.tasks?.length || 0,
        cleaningSessions: cleaningData.sessions?.length || 0,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
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
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Welcome back, {user?.firstName}!
      </h1>

      {!user?.email_verified && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 className="font-medium text-yellow-900">Email not verified</h3>
          <p className="text-sm text-yellow-700 mt-1">
            Please check your email to verify your account.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Link to="/app/properties" className="card hover:shadow-md transition-shadow">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Properties</h3>
          <p className="text-3xl font-bold text-gray-900">{stats.properties}</p>
          <p className="text-sm text-gray-500 mt-2">Total managed properties</p>
        </Link>

        <Link to="/app/tasks" className="card hover:shadow-md transition-shadow">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Pending Tasks</h3>
          <p className="text-3xl font-bold text-gray-900">{stats.tasks}</p>
          <p className="text-sm text-gray-500 mt-2">Tasks requiring attention</p>
        </Link>

        <Link to="/app/cleaning" className="card hover:shadow-md transition-shadow">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Active Cleanings</h3>
          <p className="text-3xl font-bold text-gray-900">{stats.cleaningSessions}</p>
          <p className="text-sm text-gray-500 mt-2">Cleaning sessions in progress</p>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-2">
            <Link to="/app/properties" className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              🏠 Manage Properties
            </Link>
            <Link to="/app/tasks" className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              ✓ View Tasks
            </Link>
            <Link to="/app/calendar" className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              📅 Check Calendar
            </Link>
            <Link to="/app/cleaning" className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              🧹 Cleaning Sessions
            </Link>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Account Information</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-600">Name</dt>
              <dd className="text-gray-900">{user?.firstName} {user?.lastName}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-600">Email</dt>
              <dd className="text-gray-900">{user?.email}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-600">Role</dt>
              <dd>
                <span className="badge badge-pending">
                  {user?.role.replace('_', ' ')}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-600">Email Status</dt>
              <dd>
                {user?.email_verified ? (
                  <span className="text-green-600">✓ Verified</span>
                ) : (
                  <span className="text-yellow-600">⚠ Not Verified</span>
                )}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
