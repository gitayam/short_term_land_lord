import React, { useState, useEffect } from 'react';
import { Card, Text, Select, Title, Group, Button, Alert } from '@mantine/core';
import axios from 'axios';
import { Calendar as BigCalendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import LoadingSpinner from '../components/LoadingSpinner';

interface Property {
  _id: string;
  name: string;
}

interface Reservation {
  _id: string;
  propertyId: string;
  checkInDate: string;
  checkOutDate: string;
  guestName: string;
}

// Setup the localizer for BigCalendar
const localizer = momentLocalizer(moment);

/**
 * Calendar component for displaying property reservations
 * 
 * This component fetches properties owned by the authenticated user and allows
 * them to view reservations for each property in a calendar format.
 * 
 * Features:
 * - Property selection dropdown
 * - Calendar view with month, week, and day views
 * - Reservation details on hover
 * - Loading states and error handling
 */
function Calendar() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<string | null>(null);
  const [reservations, setReservations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch properties owned by the authenticated user
  useEffect(() => {
    const fetchProperties = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/properties');
        setProperties(response.data);
        
        // Set first property as selected if available
        if (response.data.length > 0) {
          setSelectedProperty(response.data[0]._id);
        } else {
          setError('No properties found. Please add a property first.');
        }
      } catch (err) {
        console.error('Error fetching properties:', err);
        setError('Failed to load properties. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchProperties();
  }, []);

  // Fetch reservations for the selected property
  useEffect(() => {
    const fetchReservations = async () => {
      if (!selectedProperty) return;
      
      try {
        setLoading(true);
        setError(null);
        
        const response = await axios.get(`/api/calendar/reservations/${selectedProperty}`);
        
        // Format reservations for the calendar
        const formattedReservations = response.data.map((res: Reservation) => ({
          id: res._id,
          title: `Guest: ${res.guestName}`,
          start: new Date(res.checkInDate),
          end: new Date(res.checkOutDate),
          resource: res,
          allDay: true
        }));
        
        setReservations(formattedReservations);
      } catch (err) {
        console.error('Error fetching reservations:', err);
        setError('Failed to load reservations. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchReservations();
  }, [selectedProperty]);

  // Handle property selection change in the dropdown
  const handlePropertyChange = (value: string | null) => {
    setSelectedProperty(value);
  };

  return (
    <div className="container py-8">
      <Title order={2} mb="xl">Reservation Calendar</Title>
      
      {error && (
        <Alert color="red" mb="md">
          {error}
        </Alert>
      )}
      
      <Card p="md" radius="md" withBorder mb="md">
        <div className="flex justify-between items-center mb-4">
          <Text size="lg" fw={500}>View Reservations</Text>
          
          {properties.length > 0 ? (
            <Select
              placeholder="Select property"
              value={selectedProperty}
              onChange={handlePropertyChange}
              data={properties.map((prop: Property) => ({ value: prop._id, label: prop.name }))}
              style={{ width: 250 }}
              searchable
              clearable={false}
            />
          ) : (
            <Text color="dimmed">No properties available</Text>
          )}
        </div>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner fullPage={false} size="md" />
          </div>
        ) : (
          <div style={{ height: 600 }}>
            {reservations.length > 0 ? (
              <BigCalendar
                localizer={localizer}
                events={reservations}
                startAccessor="start"
                endAccessor="end"
                style={{ height: '100%' }}
                views={['month', 'week', 'day']}
                defaultView="month"
                tooltipAccessor={(event) => `${event.title} (${moment(event.start).format('MMM D')} - ${moment(event.end).format('MMM D')})`}
                eventPropGetter={(event) => ({
                  style: {
                    backgroundColor: '#3182ce',
                    borderRadius: '4px',
                    color: 'white',
                    border: 'none',
                    display: 'block'
                  }
                })}
              />
            ) : (
              <div className="p-4 border rounded bg-gray-100 text-center">
                No reservations found for this property.
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

export default Calendar;