import { Calendar, dateFnsLocalizer, View } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { enUS } from 'date-fns/locale';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { useState } from 'react';

const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

export interface CalendarEvent {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  source: string;
  guest_name?: string;
  guest_count?: number;
  booking_amount?: number;
  booking_status?: string;
  platform_name?: string;
}

interface CalendarGridProps {
  events: CalendarEvent[];
  onEventSelect: (event: CalendarEvent) => void;
  loading?: boolean;
}

export function CalendarGrid({ events, onEventSelect, loading }: CalendarGridProps) {
  const [view, setView] = useState<View>('month');
  const [date, setDate] = useState(new Date());

  // Transform API events to calendar format
  const calendarEvents = events.map((event) => ({
    id: event.id,
    title: event.guest_name || event.title || 'Booking',
    start: new Date(event.start_date),
    end: new Date(event.end_date),
    resource: event, // Store full event data
  }));

  // Color code events by status
  const eventStyleGetter = (event: any) => {
    const status = event.resource?.booking_status?.toLowerCase();
    let backgroundColor = '#3182ce'; // Default blue

    switch (status) {
      case 'confirmed':
        backgroundColor = '#38a169'; // Green
        break;
      case 'pending':
        backgroundColor = '#d69e2e'; // Yellow
        break;
      case 'cancelled':
        backgroundColor = '#e53e3e'; // Red
        break;
      case 'blocked':
        backgroundColor = '#718096'; // Gray
        break;
    }

    return {
      style: {
        backgroundColor,
        borderRadius: '4px',
        opacity: 0.8,
        color: 'white',
        border: '0px',
        display: 'block',
      },
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4" style={{ height: '700px' }}>
      <Calendar
        localizer={localizer}
        events={calendarEvents}
        startAccessor="start"
        endAccessor="end"
        view={view}
        onView={setView}
        date={date}
        onNavigate={setDate}
        onSelectEvent={(event) => onEventSelect(event.resource)}
        eventPropGetter={eventStyleGetter}
        popup
        tooltipAccessor={(event: any) => {
          const evt = event.resource;
          return `${evt.guest_name || evt.title}\n${evt.platform_name || evt.source || ''}`;
        }}
      />

      <div className="mt-4 flex gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#38a169' }}></div>
          <span>Confirmed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#d69e2e' }}></div>
          <span>Pending</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#e53e3e' }}></div>
          <span>Cancelled</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#718096' }}></div>
          <span>Blocked</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3182ce' }}></div>
          <span>Other</span>
        </div>
      </div>
    </div>
  );
}
