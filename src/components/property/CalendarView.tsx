import { useState, useEffect } from 'react';
import { calendarApi } from '../../services/api';

interface CalendarEvent {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  source: string;
  platform_name: string;
  guest_name?: string;
  guest_count?: number;
  booking_status: string;
  booking_amount?: number;
  external_id?: string;
}

interface CalendarViewProps {
  propertyId: string;
}

interface BookingDetailsModalProps {
  event: CalendarEvent | null;
  isOpen: boolean;
  onClose: () => void;
}

function BookingDetailsModal({ event, isOpen, onClose }: BookingDetailsModalProps) {
  if (!isOpen || !event) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-gray-900">Booking Details</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <span className={`px-3 py-1 rounded-full text-white text-sm ${
              event.platform_name === 'airbnb' ? 'bg-red-500' :
              event.platform_name === 'vrbo' ? 'bg-blue-500' :
              event.platform_name === 'booking' ? 'bg-green-500' :
              'bg-purple-500'
            }`}>
              {event.platform_name || event.source}
            </span>
          </div>

          <div>
            <div className="text-sm font-medium text-gray-600">Title</div>
            <div className="text-gray-900">{event.title}</div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-600">Check-in</div>
              <div className="text-gray-900">{new Date(event.start_date).toLocaleDateString()}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-600">Check-out</div>
              <div className="text-gray-900">{new Date(event.end_date).toLocaleDateString()}</div>
            </div>
          </div>

          {event.guest_name && (
            <div>
              <div className="text-sm font-medium text-gray-600">Guest Name</div>
              <div className="text-gray-900">{event.guest_name}</div>
            </div>
          )}

          {event.guest_count && (
            <div>
              <div className="text-sm font-medium text-gray-600">Number of Guests</div>
              <div className="text-gray-900">{event.guest_count}</div>
            </div>
          )}

          {event.booking_amount && (
            <div>
              <div className="text-sm font-medium text-gray-600">Booking Amount</div>
              <div className="text-gray-900">${event.booking_amount}</div>
            </div>
          )}

          <div>
            <div className="text-sm font-medium text-gray-600">Status</div>
            <span className="badge badge-completed">{event.booking_status}</span>
          </div>

          {event.external_id && (
            <div>
              <div className="text-sm font-medium text-gray-600">External ID</div>
              <div className="text-gray-900 text-xs font-mono break-all">{event.external_id}</div>
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

interface BlockDateModalProps {
  date: Date | null;
  isOpen: boolean;
  onClose: () => void;
  onBlock: (startDate: string, endDate: string, reason: string) => void;
}

function BlockDateModal({ date, isOpen, onClose, onBlock }: BlockDateModalProps) {
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');

  useEffect(() => {
    if (date) {
      const dateStr = date.toISOString().split('T')[0];
      setEndDate(dateStr);
    }
  }, [date]);

  if (!isOpen || !date) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const startDateStr = date.toISOString().split('T')[0];
    onBlock(startDateStr, endDate, reason);
    setReason('');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-gray-900">Block Dates</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={date.toISOString().split('T')[0]}
              readOnly
              className="input bg-gray-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              min={date.toISOString().split('T')[0]}
              className="input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason (optional)
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="input"
              rows={3}
              placeholder="Maintenance, personal use, etc."
            />
          </div>

          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Block Dates
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function CalendarView({ propertyId }: CalendarViewProps) {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<'month' | 'list'>('month');
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [showEventDetails, setShowEventDetails] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [showBlockDate, setShowBlockDate] = useState(false);

  useEffect(() => {
    loadEvents();
  }, [propertyId, currentDate]);

  const loadEvents = async () => {
    try {
      // Get events for current month ± 30 days
      const startDate = new Date(currentDate);
      startDate.setDate(1);
      startDate.setMonth(startDate.getMonth() - 1);

      const endDate = new Date(currentDate);
      endDate.setMonth(endDate.getMonth() + 2);
      endDate.setDate(0);

      const data = await calendarApi.getEvents(
        propertyId,
        startDate.toISOString().split('T')[0],
        endDate.toISOString().split('T')[0]
      );
      setEvents(data.events || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load calendar events');
    } finally {
      setLoading(false);
    }
  };

  const getMonthDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days: (Date | null)[] = [];

    // Add empty days for alignment
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }

    // Add actual days
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }

    return days;
  };

  const getEventsForDate = (date: Date | null): CalendarEvent[] => {
    if (!date) return [];

    const dateStr = date.toISOString().split('T')[0];

    return events.filter((event) => {
      return dateStr >= event.start_date && dateStr <= event.end_date;
    });
  };

  const getPlatformColor = (platform: string) => {
    const colors: { [key: string]: string } = {
      airbnb: 'bg-red-500',
      vrbo: 'bg-blue-500',
      booking: 'bg-green-500',
      direct: 'bg-purple-500',
    };
    return colors[platform?.toLowerCase()] || 'bg-gray-500';
  };

  const changeMonth = (offset: number) => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + offset, 1));
  };

  const formatMonthYear = () => {
    return currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const getUpcomingBookings = () => {
    const today = new Date().toISOString().split('T')[0];
    return events
      .filter((event) => event.end_date >= today)
      .sort((a, b) => a.start_date.localeCompare(b.start_date))
      .slice(0, 10);
  };

  const handleEventClick = (event: CalendarEvent) => {
    setSelectedEvent(event);
    setShowEventDetails(true);
  };

  const handleDateClick = (date: Date | null) => {
    if (!date) return;
    const dayEvents = getEventsForDate(date);

    // If date has events, show the first event
    if (dayEvents.length > 0) {
      handleEventClick(dayEvents[0]);
    } else {
      // Otherwise, allow blocking this date
      setSelectedDate(date);
      setShowBlockDate(true);
    }
  };

  const handleBlockDates = async (startDate: string, endDate: string, reason: string) => {
    try {
      // Create a blocked event
      await calendarApi.blockDates(propertyId, { start_date: startDate, end_date: endDate, reason });
      // Reload events
      await loadEvents();
    } catch (err: any) {
      setError(err.message || 'Failed to block dates');
    }
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Booking Calendar</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode(viewMode === 'month' ? 'list' : 'month')}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
          >
            {viewMode === 'month' ? '📋 List' : '📅 Calendar'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {viewMode === 'month' ? (
        <div className="card">
          {/* Month Navigation */}
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => changeMonth(-1)}
              className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200"
            >
              ← Prev
            </button>
            <h4 className="text-lg font-medium">{formatMonthYear()}</h4>
            <button
              onClick={() => changeMonth(1)}
              className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200"
            >
              Next →
            </button>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1">
            {/* Day headers */}
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
              <div key={day} className="text-center text-sm font-medium text-gray-600 py-2">
                {day}
              </div>
            ))}

            {/* Calendar days */}
            {getMonthDays().map((date, index) => {
              const dayEvents = getEventsForDate(date);
              const isToday =
                date && date.toDateString() === new Date().toDateString();

              return (
                <div
                  key={index}
                  onClick={() => handleDateClick(date)}
                  className={`min-h-[80px] border border-gray-200 p-1 ${
                    date ? 'bg-white cursor-pointer hover:bg-gray-50' : 'bg-gray-50'
                  } ${isToday ? 'ring-2 ring-blue-500' : ''}`}
                >
                  {date && (
                    <>
                      <div className="text-sm font-medium text-gray-700 mb-1">
                        {date.getDate()}
                      </div>
                      <div className="space-y-1">
                        {dayEvents.slice(0, 2).map((event, i) => (
                          <div
                            key={i}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEventClick(event);
                            }}
                            className={`text-xs px-1 py-0.5 rounded text-white truncate cursor-pointer hover:opacity-80 ${getPlatformColor(event.platform_name)}`}
                            title={`${event.title}${event.guest_name ? ' - ' + event.guest_name : ''}`}
                          >
                            {event.title}
                          </div>
                        ))}
                        {dayEvents.length > 2 && (
                          <div className="text-xs text-gray-500">
                            +{dayEvents.length - 2} more
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span>Airbnb</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-500 rounded"></div>
              <span>VRBO</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <span>Booking.com</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-500 rounded"></div>
              <span>Direct</span>
            </div>
          </div>
        </div>
      ) : (
        /* List View */
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900">Upcoming Bookings</h4>
          {getUpcomingBookings().length === 0 ? (
            <div className="card text-center py-8">
              <p className="text-gray-600">No upcoming bookings</p>
            </div>
          ) : (
            getUpcomingBookings().map((event) => (
              <div key={event.id} className="card">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-white text-sm ${getPlatformColor(event.platform_name)}`}>
                        {event.platform_name || event.source}
                      </span>
                      <h4 className="font-medium text-gray-900">{event.title}</h4>
                    </div>

                    <div className="text-sm text-gray-600 space-y-1">
                      <div>
                        <span className="font-medium">Dates:</span>{' '}
                        {new Date(event.start_date).toLocaleDateString()} -{' '}
                        {new Date(event.end_date).toLocaleDateString()}
                      </div>
                      {event.guest_name && (
                        <div>
                          <span className="font-medium">Guest:</span> {event.guest_name}
                        </div>
                      )}
                      {event.guest_count && (
                        <div>
                          <span className="font-medium">Guests:</span> {event.guest_count}
                        </div>
                      )}
                    </div>
                  </div>

                  <span className="badge badge-completed">{event.booking_status}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Booking Details Modal */}
      <BookingDetailsModal
        event={selectedEvent}
        isOpen={showEventDetails}
        onClose={() => setShowEventDetails(false)}
      />

      {/* Block Date Modal */}
      <BlockDateModal
        date={selectedDate}
        isOpen={showBlockDate}
        onClose={() => setShowBlockDate(false)}
        onBlock={handleBlockDates}
      />
    </div>
  );
}
