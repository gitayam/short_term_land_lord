import { CalendarEvent } from './CalendarGrid';

interface CalendarEventModalProps {
  event: CalendarEvent | null;
  isOpen: boolean;
  onClose: () => void;
}

export function CalendarEventModal({ event, isOpen, onClose }: CalendarEventModalProps) {
  if (!isOpen || !event) return null;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getStatusBadge = (status?: string) => {
    const statusLower = status?.toLowerCase() || '';
    const badges: Record<string, string> = {
      confirmed: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      cancelled: 'bg-red-100 text-red-800',
      blocked: 'bg-gray-100 text-gray-800',
    };
    return badges[statusLower] || 'bg-blue-100 text-blue-800';
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
          {/* Header */}
          <div className="flex justify-between items-start p-6 border-b border-gray-200">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {event.guest_name || event.title || 'Booking Details'}
              </h2>
              {event.platform_name && (
                <p className="text-sm text-gray-600 mt-1">
                  via {event.platform_name}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-4">
            {event.booking_status && (
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Status
                </label>
                <span
                  className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(
                    event.booking_status
                  )}`}
                >
                  {event.booking_status}
                </span>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Check-in
              </label>
              <p className="text-gray-900">{formatDate(event.start_date)}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Check-out
              </label>
              <p className="text-gray-900">{formatDate(event.end_date)}</p>
            </div>

            {event.guest_count && (
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Guests
                </label>
                <p className="text-gray-900">{event.guest_count} guests</p>
              </div>
            )}

            {event.booking_amount && (
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Booking Amount
                </label>
                <p className="text-gray-900 font-semibold text-lg">
                  ${event.booking_amount.toFixed(2)}
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Source
              </label>
              <p className="text-gray-900">{event.source || 'Direct'}</p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
