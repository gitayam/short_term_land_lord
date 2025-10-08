import { useEffect, useState } from 'react';
import { cleaningApi } from '../../services/api';
import type { CleaningSession } from '../../types';

export function CleaningSessionsPage() {
  const [sessions, setSessions] = useState<CleaningSession[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSessions();
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
        <button className="btn-primary">+ Start Session</button>
      </div>

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
                <button className="btn-secondary text-sm flex-1">View Details</button>
                {session.status === 'in_progress' && (
                  <button className="btn-success text-sm flex-1">Complete</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
