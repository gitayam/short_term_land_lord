import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, Text, Title, Grid, Badge, Button, Group } from '@mantine/core';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface Property {
  _id: string;
  name: string;
  address: string;
  description: string;
  type: string;
}

interface ReservationStats {
  upcoming: number;
  total: number;
}

function Dashboard() {
  const { user } = useAuth();
  const [properties, setProperties] = useState<Property[]>([]);
  const [reservationStats, setReservationStats] = useState<ReservationStats>({ upcoming: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch properties
        const propertiesResponse = await axios.get('/api/properties');
        setProperties(propertiesResponse.data);
        
        // For simplicity, we're mocking reservation stats
        // In a real app, you'd fetch this from an API
        setReservationStats({
          upcoming: 5,
          total: 12
        });
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return <div className="container py-8">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="container py-8">Error: {error}</div>;
  }

  return (
    <div className="container py-8">
      <Title order={2} mb="xl">Dashboard</Title>
      
      <Grid>
        {/* Stats Cards */}
        <Grid.Col span={6}>
          <Card p="lg" radius="md" withBorder mb="md">
            <Text size="lg" weight={500} mb="xs">Properties</Text>
            <Text size="xl" weight={700}>{properties.length}</Text>
            <Text size="sm" color="dimmed">Total properties managed</Text>
          </Card>
        </Grid.Col>
        
        <Grid.Col span={6}>
          <Card p="lg" radius="md" withBorder mb="md">
            <Text size="lg" weight={500} mb="xs">Upcoming Reservations</Text>
            <Text size="xl" weight={700}>{reservationStats.upcoming}</Text>
            <Text size="sm" color="dimmed">Out of {reservationStats.total} total</Text>
          </Card>
        </Grid.Col>
        
        {/* Calendar Link Card */}
        <Grid.Col span={12}>
          <Card p="lg" radius="md" withBorder mb="xl">
            <Group position="apart">
              <div>
                <Text size="lg" weight={500} mb="xs">Reservation Calendar</Text>
                <Text size="sm" color="dimmed">Manage all your property reservations in one place</Text>
              </div>
              <Button component={Link} to="/calendar">View Calendar</Button>
            </Group>
          </Card>
        </Grid.Col>
        
        {/* Properties List */}
        <Grid.Col span={12}>
          <Title order={3} mb="md">Your Properties</Title>
          
          {properties.length === 0 ? (
            <Card p="lg" radius="md" withBorder>
              <Text align="center">No properties found. Add your first property to get started.</Text>
            </Card>
          ) : (
            <Grid>
              {properties.map(property => (
                <Grid.Col span={4} key={property._id}>
                  <Card p="lg" radius="md" withBorder>
                    <Text size="lg" weight={500} mb="xs">{property.name}</Text>
                    <Badge mb="md">{property.type}</Badge>
                    <Text size="sm" mb="md">{property.address}</Text>
                    <Text size="sm" color="dimmed" mb="md" lineClamp={2}>
                      {property.description}
                    </Text>
                    <Button variant="light" fullWidth>
                      View Details
                    </Button>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          )}
        </Grid.Col>
      </Grid>
    </div>
  );
}

export default Dashboard; 