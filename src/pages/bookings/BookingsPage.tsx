import { useEffect, useState } from 'react';
import { calendarApi, propertiesApi } from '../../services/api';

interface Booking {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  source: string;
  guest_name?: string;
  guest_count?: number;
  booking_amount?: number;
  booking_status: 'confirmed' | 'pending' | 'cancelled' | 'blocked';
  platform_name?: string;
}

export function BookingsPage() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [properties, setProperties] = useState<any[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProperties();
  }, []);

  useEffect(() => {
    if (properties.length > 0) {
      loadBookings();
    }
  }, [selectedProperty, statusFilter, properties]);

  const loadProperties = async () => {
    try {
      const data = await propertiesApi.list();
      setProperties(data.properties || []);
    } catch (error) {
      console.error('Failed to load properties:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadBookings = async () => {
    try {
      setLoading(true);
      let allBookings: Booking[] = [];

      if (selectedProperty === 'all') {
        // Load bookings for all properties
        const bookingPromises = properties.map(prop =>
          calendarApi.getEvents(prop.id)
        );
        const results = await Promise.all(bookingPromises);
        allBookings = results.flatMap(result => result.events || []);
      } else {
        // Load bookings for selected property
        const data = await calendarApi.getEvents(selectedProperty);
        allBookings = data.events || [];
      }

      // Filter by status
      if (statusFilter !== 'all') {
        allBookings = allBookings.filter(b => b.booking_status === statusFilter);
      }

      // Sort by start date (most recent first)
      allBookings.sort((a, b) =>
        new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
      );

      setBookings(allBookings);
    } catch (error) {
      console.error('Failed to load bookings:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      confirmed: 'badge-completed',
      pending: 'badge-pending',
      cancelled: 'badge-failed',
      blocked: 'badge',
    };
    return badges[status as keyof typeof badges] || 'badge';
  };

  const getPropertyName = (booking: Booking) => {
    // This would need to be enhanced if we store property info with booking
    // For now, it's just shown in the selected filter
    return 'Property'; // Placeholder
  };

  const calculateNights = (startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getTotalRevenue = () => {
    return bookings
      .filter(b => b.booking_status === 'confirmed' && b.booking_amount)
      .reduce((sum, b) => sum + (b.booking_amount || 0), 0);
  };

  const getUpcomingBookings = () => {
    const today = new Date().toISOString().split('T')[0];
    return bookings.filter(
      b => b.booking_status === 'confirmed' && b.start_date >= today
    ).length;
  };

  const getActiveBookings = () => {
    const today = new Date().toISOString().split('T')[0];
    return bookings.filter(
      b =>
        b.booking_status === 'confirmed' &&
        b.start_date <= today &&
        b.end_date >= today
    ).length;
  };

  if (loading && properties.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Bookings</h1>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Total Bookings</div>
          <div className="text-3xl font-bold text-gray-900">{bookings.length}</div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Active Now</div>
          <div className="text-3xl font-bold text-green-600">{getActiveBookings()}</div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Upcoming</div>
          <div className="text-3xl font-bold text-blue-600">{getUpcomingBookings()}</div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Total Revenue</div>
          <div className="text-3xl font-bold text-gray-900">
            ${getTotalRevenue().toLocaleString()}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Property
            </label>
            <select
              value={selectedProperty}
              onChange={(e) => setSelectedProperty(e.target.value)}
              className="input"
            >
              <option value="all">All Properties</option>
              {properties.map((prop) => (
                <option key={prop.id} value={prop.id}>
                  {prop.name || prop.address}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <div className="flex gap-2">
              {['all', 'confirmed', 'pending', 'cancelled'].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    statusFilter === status
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bookings List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : bookings.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">📅</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No bookings found</h3>
          <p className="text-gray-600">
            {statusFilter === 'all'
              ? selectedProperty === 'all'
                ? 'No bookings yet'
                : 'No bookings for this property'
              : `No ${statusFilter} bookings`}
          </p>
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Guest
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dates
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nights
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Platform
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {bookings.map((booking) => (
                <tr key={booking.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {booking.guest_name || booking.title}
                    </div>
                    {booking.guest_count && (
                      <div className="text-sm text-gray-500">
                        {booking.guest_count} guest{booking.guest_count > 1 ? 's' : ''}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {new Date(booking.start_date).toLocaleDateString()}
                    </div>
                    <div className="text-sm text-gray-500">
                      to {new Date(booking.end_date).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {calculateNights(booking.start_date, booking.end_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {booking.platform_name || booking.source || 'Direct'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {booking.booking_amount
                      ? `$${booking.booking_amount.toLocaleString()}`
                      : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${getStatusBadge(booking.booking_status)}`}>
                      {booking.booking_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
