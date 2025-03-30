import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { TextInput, PasswordInput, Button, Text, Paper, Title, Alert } from '@mantine/core';
import { useAuth } from '../contexts/AuthContext';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { login, error } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!email.trim()) {
      return;
    }
    
    if (!password.trim()) {
      return;
    }

    try {
      setSubmitting(true);
      await login(email, password);
      // Successful login will redirect via App.tsx routes
    } catch (err) {
      // Error is handled in the auth context
      console.error('Login submission error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container py-12">
      <Paper className="auth-card" p="md" radius="md" withBorder>
        <Title order={2} mb="md" ta="center">Log In</Title>
        
        {error && (
          <Alert color="red" mb="md" title="Authentication Error">
            {error}
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
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
            mb="xl"
          />
          
          <Button 
            fullWidth 
            type="submit" 
            loading={submitting}
            disabled={!email.trim() || !password.trim()}
          >
            Log In
          </Button>
        </form>
        
        <Text ta="center" mt="md">
          Don't have an account? <Link to="/register" className="text-blue-600">Register</Link>
        </Text>
      </Paper>
    </div>
  );
}

export default Login;