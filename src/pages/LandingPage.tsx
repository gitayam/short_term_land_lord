/**
 * Landing Page - Availability Calendar
 * Public calendar showing available dates for short-term rentals
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { GuestBookingFlow } from '../components/booking/GuestBookingFlow';

interface CalendarDay {
  date: string;
  isAvailable: boolean;
  isToday: boolean;
  isCurrentMonth: boolean;
}

interface Property {
  id: string;
  name: string;
  address: string;
  city: string;
  bedrooms: number;
  bathrooms: number;
  image_url?: string;
}

export function LandingPage() {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedProperty, setSelectedProperty] = useState<string>('all');
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkInDate, setCheckInDate] = useState<string | null>(null);
  const [checkOutDate, setCheckOutDate] = useState<string | null>(null);
  const [showBookingForm, setShowBookingForm] = useState(false);

  const [availabilityData, setAvailabilityData] = useState<{
    blockedDates: Record<string, boolean>;
    events: any[];
  }>({ blockedDates: {}, events: [] });

  useEffect(() => {
    loadAvailability();
  }, [currentDate, selectedProperty]);

  // Auto-select property if there's only one
  useEffect(() => {
    if (properties.length === 1 && selectedProperty === 'all') {
      setSelectedProperty(properties[0].id);
    }
  }, [properties]);

  const loadAvailability = async () => {
    try {
      setLoading(true);
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth() + 1;

      const url = new URL('/api/calendar/availability', window.location.origin);
      url.searchParams.set('year', year.toString());
      url.searchParams.set('month', month.toString());
      url.searchParams.set('_t', Date.now().toString()); // Cache buster
      if (selectedProperty !== 'all') {
        url.searchParams.set('property_id', selectedProperty);
      }

      const response = await fetch(url.toString(), {
        cache: 'no-store', // Force fresh data
      });
      if (response.ok) {
        const data = await response.json();
        console.log('[Calendar] Loaded availability:', {
          year,
          month,
          blockedDates: data.blockedDates,
          eventCount: data.events?.length || 0
        });
        setAvailabilityData({
          blockedDates: data.blockedDates || {},
          events: data.events || [],
        });
        if (data.properties) {
          setProperties(data.properties);
        }
      }
    } catch (err) {
      console.error('Failed to load availability:', err);
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = (date: Date): CalendarDay[] => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days: CalendarDay[] = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Add empty days for the start of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      const prevMonthDay = new Date(year, month, -startingDayOfWeek + i + 1);
      days.push({
        date: prevMonthDay.toISOString().split('T')[0],
        isAvailable: false,
        isToday: false,
        isCurrentMonth: false,
      });
    }

    // Add days of the current month
    for (let day = 1; day <= daysInMonth; day++) {
      const currentDay = new Date(year, month, day);
      const dateStr = currentDay.toISOString().split('T')[0];
      const isToday = currentDay.getTime() === today.getTime();

      // Check availability: future date AND not blocked
      const isFuture = currentDay >= today;
      const isBlocked = availabilityData.blockedDates[dateStr] || false;
      const isAvailable = isFuture && !isBlocked;

      days.push({
        date: dateStr,
        isAvailable,
        isToday,
        isCurrentMonth: true,
      });
    }

    // Fill remaining days to complete the week grid
    const remainingDays = 42 - days.length; // 6 weeks * 7 days
    for (let i = 1; i <= remainingDays; i++) {
      const nextMonthDay = new Date(year, month + 1, i);
      days.push({
        date: nextMonthDay.toISOString().split('T')[0],
        isAvailable: false,
        isToday: false,
        isCurrentMonth: false,
      });
    }

    return days;
  };

  const navigateMonth = (direction: number) => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + direction, 1));
  };

  const monthName = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const calendarDays = getDaysInMonth(currentDate);
  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Find next available dates after check-in (up to next blocked date)
  const getAvailableCheckoutDates = (checkInDateStr: string): string[] => {
    const checkInDate = new Date(checkInDateStr);
    const availableDates: string[] = [];

    // Check each subsequent day until we hit a blocked date
    let currentDate = new Date(checkInDate);
    currentDate.setDate(currentDate.getDate() + 1); // Start with day after check-in

    // Limit to 30 days ahead
    for (let i = 0; i < 30; i++) {
      const dateStr = currentDate.toISOString().split('T')[0];
      const isBlocked = availabilityData.blockedDates[dateStr];

      // IMPORTANT: Allow the FIRST blocked date as a valid checkout
      // This enables same-day turnovers: your guest checks out morning,
      // next guest checks in afternoon of the same day
      if (isBlocked && availableDates.length > 0) {
        // Already found some available dates, now hit a blocked date
        // Allow this blocked date as final checkout option
        availableDates.push(dateStr);
        break;
      } else if (isBlocked && availableDates.length === 0) {
        // First date after check-in is blocked AND it's a check-in date
        // This means same-day checkout is possible
        availableDates.push(dateStr);
        break;
      } else if (!isBlocked) {
        // Date is available
        availableDates.push(dateStr);
      }

      currentDate.setDate(currentDate.getDate() + 1);
    }

    return availableDates;
  };

  const handleDateClick = (dateStr: string, day: CalendarDay) => {
    console.log('[Calendar] Date clicked:', {
      date: dateStr,
      isAvailable: day.isAvailable,
      isBlocked: availabilityData.blockedDates[dateStr],
      checkInDate,
      checkOutDate
    });

    if (!checkInDate) {
      // First selection: set check-in date
      setCheckInDate(dateStr);
      setCheckOutDate(null);

      // Auto-select checkout if only one night available
      const availableCheckouts = getAvailableCheckoutDates(dateStr);
      console.log('[Calendar] Available checkouts:', availableCheckouts);
      if (availableCheckouts.length === 1) {
        console.log('[Calendar] Auto-selecting checkout:', availableCheckouts[0]);
        setCheckOutDate(availableCheckouts[0]);
      }
    } else if (!checkOutDate) {
      // Second selection: set check-out date
      const checkIn = new Date(checkInDate);
      const checkOut = new Date(dateStr);

      if (checkOut > checkIn) {
        // Valid check-out (after check-in)
        setCheckOutDate(dateStr);
      } else {
        // Reset and start over with new check-in
        setCheckInDate(dateStr);
        setCheckOutDate(null);

        // Auto-select checkout if only one night available
        const availableCheckouts = getAvailableCheckoutDates(dateStr);
        if (availableCheckouts.length === 1) {
          setCheckOutDate(availableCheckouts[0]);
        }
      }
    } else {
      // Both dates selected, start over
      setCheckInDate(dateStr);
      setCheckOutDate(null);

      // Auto-select checkout if only one night available
      const availableCheckouts = getAvailableCheckoutDates(dateStr);
      if (availableCheckouts.length === 1) {
        setCheckOutDate(availableCheckouts[0]);
      }
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const calculateNights = () => {
    if (!checkInDate || !checkOutDate) return 0;
    const checkIn = new Date(checkInDate);
    const checkOut = new Date(checkOutDate);
    const diffTime = checkOut.getTime() - checkIn.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <div className="text-3xl">🏠</div>
                <span className="text-xl font-bold text-gray-900">OpenBNB</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/login" className="text-gray-700 hover:text-gray-900 font-medium">
                Owner Login
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Text */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Check Availability
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Select your dates to check availability for our Fayetteville, NC short-term rentals
          </p>
          <div className="mt-4 inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-4 py-2">
            <span className="text-2xl">📍</span>
            <span className="font-medium text-blue-900">Fayetteville, NC</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Calendar Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-xl p-6 md:p-8">
              {/* Calendar Header */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                <div className="flex items-center gap-4 w-full sm:w-auto">
                  <h2 className="text-2xl font-bold text-gray-900">{monthName}</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={() => navigateMonth(-1)}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                      </svg>
                    </button>
                    <button
                      onClick={() => navigateMonth(1)}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Property Filter - Only show if multiple properties */}
                {properties.length > 1 && (
                  <div className="w-full sm:w-auto">
                    <select
                      value={selectedProperty}
                      onChange={(e) => setSelectedProperty(e.target.value)}
                      className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Properties</option>
                      {properties.map((property) => (
                        <option key={property.id} value={property.id}>
                          {property.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Week Day Headers */}
              <div className="grid grid-cols-7 gap-2 mb-2">
                {weekDays.map((day) => (
                  <div key={day} className="text-center text-sm font-semibold text-gray-600 py-2">
                    {day}
                  </div>
                ))}
              </div>

              {/* Calendar Grid */}
              {loading ? (
                <div className="flex justify-center items-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="grid grid-cols-7 gap-2">
                  {calendarDays.map((day, idx) => {
                    const dayNum = new Date(day.date).getDate();
                    const isCheckIn = checkInDate === day.date;
                    const isCheckOut = checkOutDate === day.date;

                    // Get valid checkout dates if check-in is selected
                    const availableCheckouts = checkInDate && !checkOutDate
                      ? getAvailableCheckoutDates(checkInDate)
                      : [];
                    const isValidCheckout = availableCheckouts.includes(day.date);

                    // Check if date is in selected range
                    const isInRange = checkInDate && checkOutDate &&
                      new Date(day.date) > new Date(checkInDate) &&
                      new Date(day.date) < new Date(checkOutDate);

                    // Date is clickable if: available for check-in OR valid checkout option
                    const isClickable = (day.isAvailable && day.isCurrentMonth) || isValidCheckout;

                    return (
                      <button
                        key={idx}
                        onClick={() => isClickable && handleDateClick(day.date, day)}
                        disabled={!isClickable}
                        className={`
                          aspect-square p-2 rounded-lg text-center transition-all relative
                          ${!day.isCurrentMonth ? 'opacity-30' : ''}
                          ${day.isToday ? 'ring-2 ring-blue-500' : ''}
                          ${isCheckIn ? 'ring-2 ring-purple-600 bg-purple-500 text-white hover:bg-purple-600' : ''}
                          ${isCheckOut ? 'ring-2 ring-purple-600 bg-purple-500 text-white hover:bg-purple-600' : ''}
                          ${isInRange && !isCheckIn && !isCheckOut ? 'bg-purple-100 text-purple-900' : ''}
                          ${isValidCheckout && !isCheckOut ? 'bg-blue-50 hover:bg-blue-100 text-blue-900 font-semibold cursor-pointer ring-1 ring-blue-300' : ''}
                          ${day.isAvailable && day.isCurrentMonth && !isCheckIn && !isCheckOut && !isValidCheckout
                            ? 'bg-green-50 hover:bg-green-100 text-green-900 font-semibold cursor-pointer'
                            : ''
                          }
                          ${!isClickable ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : ''}
                        `}
                      >
                        <div className="text-sm">{dayNum}</div>
                        {isCheckIn && <div className="text-xs mt-0.5">Check-in</div>}
                        {isCheckOut && <div className="text-xs mt-0.5">Check-out</div>}
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Legend */}
              <div className="flex flex-wrap gap-4 mt-8 pt-6 border-t border-gray-200">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-50 border border-green-200 rounded"></div>
                  <span className="text-sm text-gray-600">Available</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-purple-500 rounded"></div>
                  <span className="text-sm text-gray-600">Selected</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-purple-100 border border-purple-200 rounded"></div>
                  <span className="text-sm text-gray-600">Date Range</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-100 rounded"></div>
                  <span className="text-sm text-gray-600">Blocked/Past</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar - Selected Date Info */}
          <div className="space-y-6">
            {checkInDate || checkOutDate ? (
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  {checkInDate && checkOutDate ? 'Your Stay' : 'Select Dates'}
                </h3>

                {/* Check-in Date */}
                {checkInDate && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-3">
                    <p className="text-sm text-purple-600 font-medium mb-1">Check-In</p>
                    <p className="text-lg font-bold text-purple-900">{formatDate(checkInDate)}</p>
                  </div>
                )}

                {/* Check-out Date */}
                {checkOutDate && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-3">
                    <p className="text-sm text-purple-600 font-medium mb-1">Check-Out</p>
                    <p className="text-lg font-bold text-purple-900">{formatDate(checkOutDate)}</p>
                  </div>
                )}

                {/* Stay Duration */}
                {checkInDate && checkOutDate && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <p className="text-center text-2xl font-bold text-blue-900">
                      {calculateNights()} {calculateNights() === 1 ? 'Night' : 'Nights'}
                    </p>
                  </div>
                )}

                {/* Instructions or Action */}
                {!checkOutDate ? (
                  <p className="text-sm text-gray-600 mb-6">
                    {checkInDate
                      ? 'Now select your check-out date from the calendar'
                      : 'Select a check-in date from the calendar'}
                  </p>
                ) : (
                  <>
                    <p className="text-sm text-gray-600 mb-6">
                      These dates are available! Ready to request your booking?
                    </p>
                    {selectedProperty === 'all' ? (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-3">
                        <p className="text-sm text-yellow-800">
                          Please select a specific property from the filter above to request a booking.
                        </p>
                      </div>
                    ) : (
                      <button
                        onClick={() => setShowBookingForm(true)}
                        className="block w-full text-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all mb-3"
                      >
                        Request Booking (No Login Required!)
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setCheckInDate(null);
                        setCheckOutDate(null);
                      }}
                      className="block w-full text-center px-4 py-2 text-gray-600 hover:text-gray-900 font-medium"
                    >
                      Clear Dates
                    </button>
                  </>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">How to Book</h3>
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold">
                      1
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">Select Dates</p>
                      <p className="text-sm text-gray-600">Choose your check-in date from the calendar</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold">
                      2
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">View Properties</p>
                      <p className="text-sm text-gray-600">Browse available Fayetteville rentals</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold">
                      3
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">Request Booking</p>
                      <p className="text-sm text-gray-600">Submit your booking request directly</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Contact Info */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-xl p-6 text-white">
              <h3 className="text-xl font-bold mb-3">Need Help?</h3>
              <p className="text-sm text-blue-100 mb-4">
                Have questions about availability or our properties? Get in touch!
              </p>
              <div className="space-y-2 text-sm">
                <p className="flex items-center gap-2">
                  <span>📧</span> Contact us for inquiries
                </p>
                <p className="flex items-center gap-2">
                  <span>📍</span> Fayetteville, NC
                </p>
              </div>
            </div>

            {/* Property Owner Login */}
            <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6">
              <h3 className="font-semibold text-gray-900 mb-2">Property Owner?</h3>
              <p className="text-sm text-gray-600 mb-4">
                Manage your properties, bookings, and calendar
              </p>
              <Link
                to="/login"
                className="block w-full text-center px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-white transition-colors"
              >
                Owner Login
              </Link>
            </div>
          </div>
        </div>

        {/* Why Choose Us Section */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow p-6 text-center">
            <div className="text-4xl mb-3">💰</div>
            <h3 className="font-bold text-gray-900 mb-2">Best Rates</h3>
            <p className="text-sm text-gray-600">
              Book directly and save 15-20% compared to booking platforms
            </p>
          </div>
          <div className="bg-white rounded-xl shadow p-6 text-center">
            <div className="text-4xl mb-3">🏡</div>
            <h3 className="font-bold text-gray-900 mb-2">Local Properties</h3>
            <p className="text-sm text-gray-600">
              Carefully managed short-term rentals in Fayetteville, NC
            </p>
          </div>
          <div className="bg-white rounded-xl shadow p-6 text-center">
            <div className="text-4xl mb-3">⚡</div>
            <h3 className="font-bold text-gray-900 mb-2">Quick Response</h3>
            <p className="text-sm text-gray-600">
              Direct communication with property owners for faster bookings
            </p>
          </div>
        </div>
      </div>

      {/* Guest Booking Flow Modal */}
      {showBookingForm && selectedProperty !== 'all' && checkInDate && checkOutDate && (() => {
        const property = properties.find(p => p.id === selectedProperty);
        if (!property) return null;

        return (
          <GuestBookingFlow
            property={{
              id: property.id,
              name: property.name,
              address: property.address,
              city: property.city,
              state: 'NC',
              nightly_rate: 150, // Default - actual pricing calculated server-side
              cleaning_fee: 75,  // Default - actual pricing calculated server-side
              bedrooms: property.bedrooms,
              bathrooms: property.bathrooms,
            }}
            isOpen={showBookingForm}
            onClose={() => setShowBookingForm(false)}
            preselectedDates={{
              checkIn: checkInDate,
              checkOut: checkOutDate,
            }}
          />
        );
      })()}
    </div>
  );
}
