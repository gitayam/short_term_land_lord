import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { calendarApi, propertiesApi } from '../../services/api';
import { CalendarGrid, CalendarEvent } from '../../components/calendar/CalendarGrid';
import { CalendarEventModal } from '../../components/calendar/CalendarEventModal';
import { MultiPropertyCalendar } from '../../components/calendar/MultiPropertyCalendar';
import type { Property } from '../../types';

type ViewMode = 'single' | 'multi';

export function CalendarPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [properties, setProperties] = useState<Property[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [allEvents, setAllEvents] = useState<Record<string, CalendarEvent[]>>({});
  const [loading, setLoading] = useState(true);
  const [multiLoading, setMultiLoading] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<string>('');
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('multi');

  useEffect(() => {
    loadProperties();
  }, []);

  useEffect(() => {
    // Check for property filter from URL params
    const propertyParam = searchParams.get('property');
    if (propertyParam && properties.length > 0) {
      setSelectedProperty(propertyParam);
    } else if (properties.length > 0 && !selectedProperty && viewMode === 'single') {
      // Auto-select first property if none selected in single mode
      setSelectedProperty(properties[0].id);
    }
  }, [properties, searchParams, viewMode]);

  useEffect(() => {
    if (viewMode === 'single' && selectedProperty) {
      loadEvents(selectedProperty);
    } else if (viewMode === 'multi' && properties.length > 0) {
      loadAllEvents();
    }
  }, [selectedProperty, viewMode, properties]);

  const loadProperties = async () => {
    try {
      const data = await propertiesApi.list();
      setProperties(data.properties || []);
    } catch (error) {
      console.error('Failed to load properties:', error);
    }
  };

  const loadEvents = async (propertyId: string) => {
    setLoading(true);
    try {
      const data = await calendarApi.getEvents(propertyId);
      setEvents(data.events || []);
    } catch (error) {
      console.error('Failed to load calendar events:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAllEvents = async () => {
    setMultiLoading(true);
    try {
      const eventsMap: Record<string, CalendarEvent[]> = {};
      await Promise.all(
        properties.map(async (property) => {
          try {
            const data = await calendarApi.getEvents(property.id);
            eventsMap[property.id] = data.events || [];
          } catch (error) {
            console.error(`Failed to load events for property ${property.id}:`, error);
            eventsMap[property.id] = [];
          }
        })
      );
      setAllEvents(eventsMap);
    } catch (error) {
      console.error('Failed to load calendar events:', error);
    } finally {
      setMultiLoading(false);
    }
  };

  const handlePropertyChange = (propertyId: string) => {
    setSelectedProperty(propertyId);
    // Update URL params
    if (propertyId) {
      setSearchParams({ property: propertyId });
    } else {
      setSearchParams({});
    }
  };

  const handleEventSelect = (event: CalendarEvent) => {
    setSelectedEvent(event);
    setShowEventModal(true);
  };

  const handleCloseModal = () => {
    setShowEventModal(false);
    setSelectedEvent(null);
  };

  if (!loading && properties.length === 0) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Calendar</h1>
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">🏠</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No properties found</h3>
          <p className="text-gray-600 mb-6">
            You need to add properties before viewing the calendar.
          </p>
          <a href="/properties" className="btn-primary">
            Add a Property
          </a>
        </div>
      </div>
    );
  }

  const selectedPropertyData = properties.find((p) => p.id === selectedProperty);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Calendar</h1>
        <div className="flex items-center gap-4">
          {/* View Mode Selector */}
          <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('multi')}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                viewMode === 'multi'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Multi-Property
            </button>
            <button
              onClick={() => setViewMode('single')}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                viewMode === 'single'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Single Property
            </button>
          </div>

          {/* Property selector for single view */}
          {viewMode === 'single' && (
            <select
              value={selectedProperty}
              onChange={(e) => handlePropertyChange(e.target.value)}
              className="input max-w-xs"
            >
              <option value="">Select a property</option>
              {properties.map((property) => (
                <option key={property.id} value={property.id}>
                  {property.name || property.address}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Multi-Property View */}
      {viewMode === 'multi' && (
        <>
          <MultiPropertyCalendar
            properties={properties}
            allEvents={allEvents}
            onEventSelect={handleEventSelect}
            loading={multiLoading}
          />

          <CalendarEventModal
            event={selectedEvent}
            isOpen={showEventModal}
            onClose={handleCloseModal}
          />
        </>
      )}

      {/* Single Property View */}
      {viewMode === 'single' && (
        <>
          {selectedPropertyData && (
            <div className="mb-4 p-4 bg-blue-50 rounded-lg">
              <h2 className="font-semibold text-blue-900">
                {selectedPropertyData.name || 'Unnamed Property'}
              </h2>
              <p className="text-sm text-blue-700">{selectedPropertyData.address}</p>
              {events.length > 0 && (
                <p className="text-sm text-blue-600 mt-2">
                  {events.length} event{events.length !== 1 ? 's' : ''} scheduled
                </p>
              )}
            </div>
          )}

          {!selectedProperty ? (
            <div className="card text-center py-12">
              <div className="text-5xl mb-4">📅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select a property to view calendar
              </h3>
              <p className="text-gray-600">
                Choose a property from the dropdown above to see bookings and events.
              </p>
            </div>
          ) : (
            <>
              <CalendarGrid
                events={events}
                onEventSelect={handleEventSelect}
                loading={loading}
              />

              {!loading && events.length === 0 && (
                <div className="card text-center py-8 mt-4">
                  <div className="text-4xl mb-3">📭</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No events yet</h3>
                  <p className="text-gray-600">
                    Calendar events will appear here once you sync with booking platforms.
                  </p>
                </div>
              )}

              <CalendarEventModal
                event={selectedEvent}
                isOpen={showEventModal}
                onClose={handleCloseModal}
              />
            </>
          )}
        </>
      )}
    </div>
  );
}
