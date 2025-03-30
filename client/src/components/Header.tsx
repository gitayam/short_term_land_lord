import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Group, Text } from '@mantine/core';
import { useAuth } from '../contexts/AuthContext';

function Header() {
  const { isAuthenticated, logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="bg-blue-600 py-4">
      <div className="container mx-auto flex justify-between items-center">
        <Text component={Link} to="/" style={{ color: 'white', textDecoration: 'none', fontWeight: 'bold', fontSize: '1.2rem' }}>
          Short-Term LandLord
        </Text>

        {isAuthenticated ? (
          <div className="flex items-center">
            <Group gap="md">
              <Link to="/dashboard" className="text-white hover:text-gray-200">
                Dashboard
              </Link>
              <Link to="/calendar" className="text-white hover:text-gray-200">
                Calendar
              </Link>
              <Text size="sm" color="white" mr="md">
                Welcome, {user?.name}
              </Text>
              <Button variant="white" color="blue" onClick={handleLogout}>
                Logout
              </Button>
            </Group>
          </div>
        ) : (
          <Group>
            <Button variant="filled" component={Link} to="/login">
              Login
            </Button>
            <Button variant="white" component={Link} to="/register">
              Register
            </Button>
          </Group>
        )}
      </div>
    </div>
  );
}

export default Header; 