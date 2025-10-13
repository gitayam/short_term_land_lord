/**
 * Booking Requests Management Page
 * View and manage direct booking requests from guests
 */

import { useEffect, useState } from 'react';

interface BookingRequest {
  id: string;
  property_id: string;
  property_name: string;
  property_address: string;
  guest_name: string;
  guest_email: string;
  guest_phone: string | null;
  check_in_date: string;
  check_out_date: string;
  num_guests: number;
  message: string | null;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  owner_response: string | null;
  created_at: string;
  updated_at: string;
}

export function BookingRequestsPage() {
  const [requests, setRequests] = useState<BookingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedRequest, setSelectedRequest] = useState<BookingRequest | null>(null);
  const [responseText, setResponseText] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadBookingRequests();
  }, []);

  const loadBookingRequests = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch('/api/booking-requests', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load booking requests');
      }

      const data = await response.json();
      setRequests(data.booking_requests || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (requestId: string, status: string) => {
    try {
      setError(null);
      setSuccessMessage(null);
      setActionLoading(true);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`/api/booking-requests/${requestId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status,
          owner_response: responseText || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update booking request');
      }

      const result = await response.json();

      // Show success message
      const messages = {
        approved: '✅ Booking approved! Calendar has been updated.',
        rejected: '❌ Booking request rejected.',
        cancelled: '🚫 Booking request cancelled.',
      };
      setSuccessMessage(messages[status as keyof typeof messages] || result.message);

      // Clear form and reload
      setSelectedRequest(null);
      setResponseText('');
      await loadBookingRequests();

      // Auto-hide success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      setError(err.message);
      // Auto-hide error after 8 seconds
      setTimeout(() => setError(null), 8000);
    } finally {
      setActionLoading(false);
    }
  };

  const filteredRequests = statusFilter === 'all'
    ? requests
    : requests.filter((r) => r.status === statusFilter);

  const getStatusBadge = (status: string) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return styles[status as keyof typeof styles] || styles.pending;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const calculateNights = (checkIn: string, checkOut: string) => {
    const start = new Date(checkIn);
    const end = new Date(checkOut);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Booking Requests</h1>
          <p className="text-gray-600 mt-1">Manage direct booking inquiries from guests</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <div className="flex items-center">
            <span className="text-xl mr-2">⚠️</span>
            {error}
          </div>
        </div>
      )}

      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          {successMessage}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
      </div>

      {/* Requests List */}
      {filteredRequests.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-6xl mb-4">📨</div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">No Booking Requests</h3>
          <p className="text-gray-600">
            {statusFilter === 'all'
              ? 'You haven\'t received any booking requests yet.'
              : `No ${statusFilter} booking requests.`}
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredRequests.map((request) => (
            <div key={request.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-bold text-gray-900">
                        {request.property_name}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(request.status)}`}>
                        {request.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{request.property_address}</p>
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    <div>Requested {formatDate(request.created_at)}</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="text-xs text-blue-600 font-medium mb-1">Guest</div>
                    <div className="font-semibold text-gray-900">{request.guest_name}</div>
                    <div className="text-sm text-gray-600">{request.guest_email}</div>
                    {request.guest_phone && (
                      <div className="text-sm text-gray-600">{request.guest_phone}</div>
                    )}
                  </div>

                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="text-xs text-green-600 font-medium mb-1">Stay</div>
                    <div className="font-semibold text-gray-900">
                      {formatDate(request.check_in_date)} → {formatDate(request.check_out_date)}
                    </div>
                    <div className="text-sm text-gray-600">
                      {calculateNights(request.check_in_date, request.check_out_date)} nights
                    </div>
                  </div>

                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                    <div className="text-xs text-purple-600 font-medium mb-1">Guests</div>
                    <div className="font-semibold text-gray-900">
                      {request.num_guests} {request.num_guests === 1 ? 'guest' : 'guests'}
                    </div>
                  </div>
                </div>

                {request.message && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
                    <div className="text-xs text-gray-600 font-medium mb-2">Message from Guest:</div>
                    <p className="text-sm text-gray-800">{request.message}</p>
                  </div>
                )}

                {request.owner_response && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <div className="text-xs text-blue-600 font-medium mb-2">Your Response:</div>
                    <p className="text-sm text-gray-800">{request.owner_response}</p>
                  </div>
                )}

                {request.status === 'pending' && (
                  <div className="flex gap-3 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => setSelectedRequest(request)}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Are you sure you want to reject this booking request?')) {
                          handleUpdateStatus(request.id, 'rejected');
                        }
                      }}
                      className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Approval Modal */}
      {selectedRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full">
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Approve Booking Request
              </h2>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-sm text-blue-800">
                  <strong>{selectedRequest.guest_name}</strong> has requested to book{' '}
                  <strong>{selectedRequest.property_name}</strong> from{' '}
                  {formatDate(selectedRequest.check_in_date)} to{' '}
                  {formatDate(selectedRequest.check_out_date)}
                </p>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Response to Guest (optional)
                </label>
                <textarea
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Add a message for the guest (booking details, payment instructions, etc.)"
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setSelectedRequest(null);
                    setResponseText('');
                  }}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleUpdateStatus(selectedRequest.id, 'approved')}
                  disabled={actionLoading}
                  className="flex-1 px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {actionLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Approving...
                    </>
                  ) : (
                    'Approve Booking'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
