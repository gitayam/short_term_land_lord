import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { TextInput, PasswordInput, Button, Text, Paper, Title, Alert } from '@mantine/core';
import axios from 'axios';

function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!name || !email || !password) {
      setError('All fields are required');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    try {
      setSubmitting(true);
      setError(null);
      
      await axios.post('/api/auth/register', {
        name,
        email,
        password
      });
      
      // Registration successful, redirect to login
      navigate('/login');
    } catch (err: any) {
      console.error('Registration error:', err);
      setError(err.response?.data?.msg || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container py-12">
      <Paper className="auth-card" p="md" radius="md" withBorder>
        <Title order={2} mb="md" ta="center">Create Account</Title>
        
        {error && (
          <Alert color="red" mb="md">
            {error}
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <TextInput
            label="Name"
            placeholder="John Doe"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            mb="md"
          />
          
          <TextInput
            label="Email"
            placeholder="your@email.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            mb="md"
          />
          
          <PasswordInput
            label="Password"
            placeholder="Your password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            mb="md"
          />
          
          <PasswordInput
            label="Confirm Password"
            placeholder="Confirm your password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            mb="xl"
          />
          
          <Button 
            fullWidth 
            type="submit" 
            loading={submitting}
          >
            Register
          </Button>
        </form>
        
        <Text ta="center" mt="md">
          Already have an account? <Link to="/login" className="text-blue-600">Log In</Link>
        </Text>
      </Paper>
    </div>
  );
}

export default Register; 