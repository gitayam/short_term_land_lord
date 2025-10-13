import { useState, useEffect } from 'react';
import { calendarApi } from '../../services/api';

interface Calendar {
  id: number;
  property_id: number;
  platform_name: string;
  ical_url: string;
  is_active: boolean;
  last_synced: string | null;
  sync_status: string | null;
  sync_error: string | null;
  created_at: string;
  updated_at: string;
}

interface CalendarManagementProps {
  propertyId: string;
}

export function CalendarManagement({ propertyId }: CalendarManagementProps) {
  const [calendars, setCalendars] = useState<Calendar[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [syncing, setSyncing] = useState<{ [key: number]: boolean }>({});

  const [formData, setFormData] = useState({
    platform_name: '',
    ical_url: '',
  });

  useEffect(() => {
    loadCalendars();
  }, [propertyId]);

  const loadCalendars = async () => {
    try {
      const data = await calendarApi.listPropertyCalendars(propertyId);
      setCalendars(data.calendars || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load calendars');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCalendar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await calendarApi.addPropertyCalendar(propertyId, formData);
      setShowAddForm(false);
      setFormData({ platform_name: '', ical_url: '' });
      await loadCalendars();
    } catch (err: any) {
      setError(err.message || 'Failed to add calendar');
    }
  };

  const handleDeleteCalendar = async (calendarId: number) => {
    if (!confirm('Are you sure you want to delete this calendar?')) return;

    try {
      await calendarApi.deletePropertyCalendar(propertyId, calendarId.toString());
      await loadCalendars();
    } catch (err: any) {
      setError(err.message || 'Failed to delete calendar');
    }
  };

  const handleSyncCalendar = async (calendarId: number) => {
    setSyncing({ ...syncing, [calendarId]: true });
    setError('');

    try {
      await calendarApi.syncCalendar(propertyId);
      await loadCalendars();
    } catch (err: any) {
      setError(err.message || 'Failed to sync calendar');
    } finally {
      setSyncing({ ...syncing, [calendarId]: false });
    }
  };

  const handleToggleActive = async (calendar: Calendar) => {
    try {
      await calendarApi.updatePropertyCalendar(
        propertyId,
        calendar.id.toString(),
        { is_active: !calendar.is_active }
      );
      await loadCalendars();
    } catch (err: any) {
      setError(err.message || 'Failed to update calendar');
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getPlatformColor = (platform: string) => {
    const colors: { [key: string]: string } = {
      airbnb: 'bg-red-100 text-red-800',
      vrbo: 'bg-blue-100 text-blue-800',
      booking: 'bg-green-100 text-green-800',
      direct: 'bg-purple-100 text-purple-800',
    };
    return colors[platform.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  const getStatusBadge = (status: string | null) => {
    if (!status) return <span className="badge bg-gray-100 text-gray-700">Not Synced</span>;

    if (status === 'success') {
      return <span className="badge bg-green-100 text-green-800">✓ Synced</span>;
    }
    if (status === 'failed') {
      return <span className="badge bg-red-100 text-red-800">✗ Failed</span>;
    }
    return <span className="badge bg-yellow-100 text-yellow-800">⏳ Syncing...</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Calendar Sources</h3>
          <p className="text-sm text-gray-600">Sync bookings from external platforms</p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showAddForm ? 'Cancel' : '+ Add Calendar'}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {showAddForm && (
        <form onSubmit={handleAddCalendar} className="card space-y-4">
          <h4 className="font-medium text-gray-900">Add External Calendar</h4>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Platform
            </label>
            <select
              value={formData.platform_name}
              onChange={(e) => setFormData({ ...formData, platform_name: e.target.value })}
              className="input"
              required
            >
              <option value="">Select platform...</option>
              <option value="airbnb">Airbnb</option>
              <option value="vrbo">VRBO</option>
              <option value="booking">Booking.com</option>
              <option value="direct">Direct Bookings</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              iCal URL
            </label>
            <input
              type="url"
              value={formData.ical_url}
              onChange={(e) => setFormData({ ...formData, ical_url: e.target.value })}
              className="input"
              placeholder="https://www.airbnb.com/calendar/ical/..."
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Get this from your platform's calendar export settings
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                setShowAddForm(false);
                setFormData({ platform_name: '', ical_url: '' });
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add Calendar
            </button>
          </div>
        </form>
      )}

      {calendars.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">📅</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No calendars connected</h3>
          <p className="text-gray-600 mb-6">
            Connect your Airbnb, VRBO, or other booking platform calendars
          </p>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Your First Calendar
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {calendars.map((calendar) => (
            <div key={calendar.id} className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPlatformColor(calendar.platform_name)}`}>
                    {calendar.platform_name}
                  </span>
                  {getStatusBadge(calendar.sync_status)}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleActive(calendar)}
                    className={`px-3 py-1 rounded text-sm ${
                      calendar.is_active
                        ? 'bg-green-100 text-green-800 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {calendar.is_active ? 'Active' : 'Inactive'}
                  </button>

                  <button
                    onClick={() => handleSyncCalendar(calendar.id)}
                    disabled={syncing[calendar.id]}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm hover:bg-blue-200 disabled:opacity-50"
                  >
                    {syncing[calendar.id] ? 'Syncing...' : '↻ Sync Now'}
                  </button>

                  <button
                    onClick={() => handleDeleteCalendar(calendar.id)}
                    className="px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-600">iCal URL:</span>
                  <div className="mt-1 p-2 bg-gray-50 rounded text-xs font-mono break-all">
                    {calendar.ical_url}
                  </div>
                </div>

                <div className="flex gap-6 text-xs text-gray-600">
                  <div>
                    <span className="font-medium">Last Synced:</span> {formatDate(calendar.last_synced)}
                  </div>
                  {calendar.sync_error && (
                    <div className="text-red-600">
                      <span className="font-medium">Error:</span> {calendar.sync_error}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Export Calendar Section */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">📤 Export Your Calendar</h3>
        <p className="text-sm text-gray-600 mb-4">
          Share this URL with Airbnb, VRBO, or other platforms to sync bookings FROM this system TO them.
          This enables two-way calendar sync.
        </p>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              iCal Feed URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={calendarApi.getICalFeedUrl(propertyId)}
                readOnly
                className="input font-mono text-sm flex-1"
              />
              <button
                onClick={() => {
                  navigator.clipboard.writeText(calendarApi.getICalFeedUrl(propertyId));
                  alert('Copied to clipboard!');
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 whitespace-nowrap"
              >
                📋 Copy
              </button>
            </div>
          </div>

          <div className="text-xs text-gray-600 space-y-1">
            <p><strong>How to use:</strong></p>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              <li>Copy the URL above</li>
              <li>Go to your booking platform (Airbnb, VRBO, etc.)</li>
              <li>Find "Calendar Settings" or "Import Calendar"</li>
              <li>Paste this URL to import bookings</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
