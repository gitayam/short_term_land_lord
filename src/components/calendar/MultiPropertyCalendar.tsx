import { useState, useEffect } from 'react';
import type { Property } from '../../types';
import { CalendarEvent } from './CalendarGrid';

interface MultiPropertyCalendarProps {
  properties: Property[];
  allEvents: Record<string, CalendarEvent[]>; // propertyId -> events
  onEventSelect?: (event: CalendarEvent) => void;
  loading?: boolean;
}

export function MultiPropertyCalendar({
  properties,
  allEvents,
  onEventSelect,
  loading = false,
}: MultiPropertyCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [visibleDays, setVisibleDays] = useState(14); // Show 2 weeks by default

  // Calculate the date range to display - start from currentDate (today by default)
  const startDate = new Date(currentDate);
  startDate.setHours(0, 0, 0, 0);
  const endDate = new Date(startDate);
  endDate.setDate(startDate.getDate() + visibleDays - 1);

  // Generate array of dates to display
  const dates: Date[] = [];
  for (let i = 0; i < visibleDays; i++) {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + i);
    dates.push(date);
  }

  const handlePreviousPeriod = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() - visibleDays);
    setCurrentDate(newDate);
  };

  const handleNextPeriod = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + visibleDays);
    setCurrentDate(newDate);
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const formatDateHeader = (date: Date) => {
    const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
    const dayNum = date.getDate();
    return { dayName, dayNum };
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const getEventsForPropertyAndDate = (propertyId: string, date: Date): CalendarEvent[] => {
    const events = allEvents[propertyId] || [];
    return events.filter((event) => {
      const eventStart = new Date(event.start_date);
      const eventEnd = new Date(event.end_date);
      const checkDate = new Date(date);
      checkDate.setHours(0, 0, 0, 0);
      eventStart.setHours(0, 0, 0, 0);
      eventEnd.setHours(0, 0, 0, 0);
      return checkDate >= eventStart && checkDate <= eventEnd;
    });
  };

  // Check if a date is the last day of an event (checkout day)
  const isCheckoutDay = (event: CalendarEvent, date: Date): boolean => {
    const eventEnd = new Date(event.end_date);
    const checkDate = new Date(date);
    eventEnd.setHours(0, 0, 0, 0);
    checkDate.setHours(0, 0, 0, 0);
    return eventEnd.getTime() === checkDate.getTime();
  };

  // Check if a date is the first day of an event (checkin day)
  const isCheckinDay = (event: CalendarEvent, date: Date): boolean => {
    const eventStart = new Date(event.start_date);
    const checkDate = new Date(date);
    eventStart.setHours(0, 0, 0, 0);
    checkDate.setHours(0, 0, 0, 0);
    return eventStart.getTime() === checkDate.getTime();
  };

  // Detect same-day checkout/checkin for a property on a specific date
  const getSameDayTransitions = (propertyId: string, date: Date) => {
    const events = getEventsForPropertyAndDate(propertyId, date);
    const checkouts = events.filter((e) => isCheckoutDay(e, date));
    const checkins = events.filter((e) => isCheckinDay(e, date));

    const hasSameDayTransition = checkouts.length > 0 && checkins.length > 0 &&
                                 checkouts.some(co => checkins.some(ci => co.id !== ci.id));

    return { checkouts, checkins, hasSameDayTransition };
  };

  const getEventBlockInfo = (event: CalendarEvent, startDate: Date, endDate: Date) => {
    const eventStart = new Date(event.start_date);
    const eventEnd = new Date(event.end_date);
    const viewStart = new Date(startDate);
    const viewEnd = new Date(endDate);

    // Reset hours for accurate comparison
    [eventStart, eventEnd, viewStart, viewEnd].forEach((d) => d.setHours(0, 0, 0, 0));

    // Calculate which day the event starts (relative to visible range)
    let dayOffset = 0;
    if (eventStart < viewStart) {
      dayOffset = 0; // Event started before visible range
    } else {
      dayOffset = Math.floor((eventStart.getTime() - viewStart.getTime()) / (1000 * 60 * 60 * 24));
    }

    // Calculate event duration in visible range
    const actualStart = eventStart < viewStart ? viewStart : eventStart;
    const actualEnd = eventEnd > viewEnd ? viewEnd : eventEnd;
    const durationDays = Math.floor((actualEnd.getTime() - actualStart.getTime()) / (1000 * 60 * 60 * 24)) + 1;

    return { dayOffset, durationDays };
  };

  // Get unique events for each property (avoiding duplicates across days)
  const getPropertyEventBlocks = (propertyId: string) => {
    const events = allEvents[propertyId] || [];
    const uniqueEvents = events.filter((event) => {
      const eventStart = new Date(event.start_date);
      const eventEnd = new Date(event.end_date);
      const viewStart = new Date(startDate);
      const viewEnd = new Date(endDate);

      // Reset hours
      [eventStart, eventEnd, viewStart, viewEnd].forEach((d) => d.setHours(0, 0, 0, 0));

      // Check if event overlaps with visible range
      return eventEnd >= viewStart && eventStart <= viewEnd;
    });

    return uniqueEvents.map((event) => ({
      event,
      ...getEventBlockInfo(event, startDate, endDate),
    }));
  };

  const getEventColor = (eventType: string) => {
    const colors = {
      booking: 'bg-blue-500 hover:bg-blue-600',
      blocked: 'bg-red-500 hover:bg-red-600',
      maintenance: 'bg-yellow-500 hover:bg-yellow-600',
      cleaning: 'bg-green-500 hover:bg-green-600',
      personal: 'bg-purple-500 hover:bg-purple-600',
    };
    return colors[eventType as keyof typeof colors] || 'bg-gray-500 hover:bg-gray-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePreviousPeriod}
            className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            ← Previous
          </button>
          <button
            onClick={handleToday}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Today
          </button>
          <button
            onClick={handleNextPeriod}
            className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Next →
          </button>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Days to show:</label>
          <select
            value={visibleDays}
            onChange={(e) => setVisibleDays(Number(e.target.value))}
            className="input py-1"
          >
            <option value="7">7 days</option>
            <option value="14">14 days</option>
            <option value="30">30 days</option>
            <option value="60">60 days</option>
          </select>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            {/* Header - Dates */}
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="sticky left-0 z-20 bg-gray-50 border-r border-gray-200 px-4 py-3 text-left font-semibold text-gray-700 min-w-[200px]">
                  Property
                </th>
                {dates.map((date, idx) => {
                  const { dayName, dayNum } = formatDateHeader(date);
                  const today = isToday(date);
                  return (
                    <th
                      key={idx}
                      className={`px-2 py-3 text-center min-w-[60px] border-r border-gray-200 ${
                        today ? 'bg-blue-100' : ''
                      }`}
                    >
                      <div className="text-xs text-gray-600">{dayName}</div>
                      <div
                        className={`text-lg font-semibold ${
                          today ? 'text-blue-600' : 'text-gray-900'
                        }`}
                      >
                        {dayNum}
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>

            {/* Body - Properties */}
            <tbody>
              {properties.length === 0 ? (
                <tr>
                  <td colSpan={dates.length + 1} className="text-center py-12 text-gray-500">
                    No properties to display
                  </td>
                </tr>
              ) : (
                properties.map((property) => {
                  const eventBlocks = getPropertyEventBlocks(property.id);
                  return (
                    <tr key={property.id} className="border-b border-gray-200 hover:bg-gray-50">
                      {/* Property Name Cell */}
                      <td className="sticky left-0 z-10 bg-white border-r border-gray-200 px-4 py-4">
                        <div className="font-medium text-gray-900">
                          {property.name || 'Unnamed Property'}
                        </div>
                        <div className="text-xs text-gray-500 truncate max-w-[180px]">
                          {property.address}
                        </div>
                      </td>

                      {/* Calendar Days Cell */}
                      <td colSpan={dates.length} className="p-0 relative">
                        <div className="relative h-16" style={{ width: `${dates.length * 60}px` }}>
                          {/* Grid lines for each day with transition indicators */}
                          {dates.map((date, idx) => {
                            const { checkouts, checkins, hasSameDayTransition } = getSameDayTransitions(property.id, date);
                            return (
                              <div
                                key={idx}
                                className={`absolute h-full border-r border-gray-100 ${
                                  isToday(date) ? 'bg-blue-50' : ''
                                } ${hasSameDayTransition ? 'bg-amber-50' : ''}`}
                                style={{
                                  left: `${idx * 60}px`,
                                  width: '60px',
                                }}
                              >
                                {/* Same-day transition indicator */}
                                {hasSameDayTransition && (
                                  <div className="absolute bottom-0 left-0 right-0 flex items-center justify-center gap-0.5 text-[8px] font-bold pb-0.5">
                                    <span className="text-red-600" title={`Checkout: ${checkouts.map(e => e.guest_name || e.title).join(', ')}`}>
                                      ↑OUT
                                    </span>
                                    <span className="text-gray-400">|</span>
                                    <span className="text-green-600" title={`Checkin: ${checkins.map(e => e.guest_name || e.title).join(', ')}`}>
                                      ↓IN
                                    </span>
                                  </div>
                                )}
                              </div>
                            );
                          })}

                          {/* Event blocks */}
                          {eventBlocks.map(({ event, dayOffset, durationDays }, idx) => (
                            <div
                              key={idx}
                              onClick={() => onEventSelect?.(event)}
                              className={`absolute h-10 top-3 rounded-md cursor-pointer transition-all shadow-sm ${getEventColor(
                                event.event_type
                              )}`}
                              style={{
                                left: `${dayOffset * 60 + 2}px`,
                                width: `${durationDays * 60 - 4}px`,
                                minWidth: '56px',
                              }}
                              title={`${event.title || event.event_type} - ${event.guest_name || 'No guest'}`}
                            >
                              <div className="px-2 py-1 text-white text-xs font-medium truncate">
                                {event.guest_name || event.title || event.event_type}
                              </div>
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <div className="flex items-center gap-6">
          <span className="text-sm font-medium text-gray-700">Legend:</span>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span className="text-sm text-gray-600">Booking</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span className="text-sm text-gray-600">Blocked</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="text-sm text-gray-600">Cleaning</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500 rounded"></div>
            <span className="text-sm text-gray-600">Maintenance</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-purple-500 rounded"></div>
            <span className="text-sm text-gray-600">Personal</span>
          </div>
        </div>
      </div>
    </div>
  );
}
