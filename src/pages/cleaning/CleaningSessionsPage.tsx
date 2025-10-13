import { useEffect, useState } from 'react';
import { cleaningApi, propertiesApi } from '../../services/api';
import type { CleaningSession } from '../../types';

export function CleaningSessionsPage() {
  const [sessions, setSessions] = useState<CleaningSession[]>([]);
  const [properties, setProperties] = useState<any[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [showStartForm, setShowStartForm] = useState(false);
  const [selectedSession, setSelectedSession] = useState<CleaningSession | null>(null);
  const [formData, setFormData] = useState({
    property_id: '',
    notes: '',
  });

  useEffect(() => {
    loadSessions();
    loadProperties();
  }, [filter]);

  const loadSessions = async () => {
    try {
      const filters = filter === 'all' ? {} : { status: filter };
      const data = await cleaningApi.list(filters);
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load cleaning sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadProperties = async () => {
    try {
      const data = await propertiesApi.list();
      setProperties(data.properties || []);
    } catch (error) {
      console.error('Failed to load properties:', error);
    }
  };

  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await cleaningApi.start(formData.property_id, formData.notes);
      setShowStartForm(false);
      setFormData({ property_id: '', notes: '' });
      loadSessions();
    } catch (error: any) {
      alert(error.message || 'Failed to start cleaning session');
    }
  };

  const handleCompleteSession = async (sessionId: string) => {
    if (!confirm('Mark this cleaning session as complete?')) {
      return;
    }

    try {
      await cleaningApi.complete(sessionId);
      loadSessions();
    } catch (error: any) {
      alert(error.message || 'Failed to complete session');
    }
  };

  const handleViewDetails = (session: CleaningSession) => {
    setSelectedSession(session);
  };

  const handleCloseDetails = () => {
    setSelectedSession(null);
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      in_progress: 'badge-in-progress',
      completed: 'badge-completed',
      cancelled: 'badge-failed',
    };
    return badges[status as keyof typeof badges] || 'badge';
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
        <h1 className="text-3xl font-bold text-gray-900">Cleaning Sessions</h1>
        <button
          onClick={() => setShowStartForm(!showStartForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showStartForm ? 'Cancel' : '+ Start Session'}
        </button>
      </div>

      {showStartForm && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Start Cleaning Session</h2>
          <form onSubmit={handleStartSession} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Property *
              </label>
              <select
                value={formData.property_id}
                onChange={(e) => setFormData({ ...formData, property_id: e.target.value })}
                className="input"
                required
              >
                <option value="">Select a property</option>
                {properties.map((prop) => (
                  <option key={prop.id} value={prop.id}>
                    {prop.name || prop.address}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes (optional)
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="input"
                rows={3}
                placeholder="Any special instructions or notes for this cleaning..."
              />
            </div>

            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => setShowStartForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Start Session
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="mb-6 flex gap-2">
        {['all', 'in_progress', 'completed'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === status
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status === 'all' ? 'All' : status.replace('_', ' ')}
          </button>
        ))}
      </div>

      {sessions.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">🧹</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No cleaning sessions</h3>
          <p className="text-gray-600 mb-6">
            {filter === 'all'
              ? 'Start your first cleaning session'
              : `No ${filter.replace('_', ' ')} sessions`}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {sessions.map((session) => (
            <div key={session.id} className="card hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {session.property_name}
                  </h3>
                  <p className="text-sm text-gray-600">{session.property_address}</p>
                </div>
                <span className={`badge ${getStatusBadge(session.status)}`}>
                  {session.status.replace('_', ' ')}
                </span>
              </div>

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Cleaner:</span>
                  <span className="font-medium text-gray-900">
                    {session.cleaner_first_name} {session.cleaner_last_name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Started:</span>
                  <span className="font-medium text-gray-900">
                    {new Date(session.start_time).toLocaleString()}
                  </span>
                </div>
                {session.end_time && (
                  <div className="flex justify-between">
                    <span>Completed:</span>
                    <span className="font-medium text-gray-900">
                      {new Date(session.end_time).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>

              {session.notes && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-600">{session.notes}</p>
                </div>
              )}

              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => handleViewDetails(session)}
                  className="btn-secondary text-sm flex-1"
                >
                  View Details
                </button>
                {session.status === 'in_progress' && (
                  <button
                    onClick={() => handleCompleteSession(session.id)}
                    className="btn-success text-sm flex-1"
                  >
                    Complete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedSession && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {selectedSession.property_name}
                  </h2>
                  <p className="text-gray-600">{selectedSession.property_address}</p>
                </div>
                <button
                  onClick={handleCloseDetails}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Status</label>
                    <p className="mt-1">
                      <span className={`badge ${getStatusBadge(selectedSession.status)}`}>
                        {selectedSession.status.replace('_', ' ')}
                      </span>
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Cleaner</label>
                    <p className="mt-1 text-gray-900">
                      {selectedSession.cleaner_first_name} {selectedSession.cleaner_last_name}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Start Time</label>
                    <p className="mt-1 text-gray-900">
                      {new Date(selectedSession.start_time).toLocaleString()}
                    </p>
                  </div>
                  {selectedSession.end_time && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">End Time</label>
                      <p className="mt-1 text-gray-900">
                        {new Date(selectedSession.end_time).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>

                {selectedSession.notes && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Notes</label>
                    <p className="mt-1 text-gray-900 bg-gray-50 p-3 rounded-lg">
                      {selectedSession.notes}
                    </p>
                  </div>
                )}

                <div className="pt-4 border-t border-gray-200 flex gap-3">
                  <button
                    onClick={handleCloseDetails}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex-1"
                  >
                    Close
                  </button>
                  {selectedSession.status === 'in_progress' && (
                    <button
                      onClick={() => {
                        handleCompleteSession(selectedSession.id);
                        handleCloseDetails();
                      }}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex-1"
                    >
                      Complete Session
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
