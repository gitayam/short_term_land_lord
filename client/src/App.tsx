import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import { useAuth } from './contexts/AuthContext';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Calendar from './pages/Calendar';

// Components
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';
import LoadingSpinner from './components/LoadingSpinner';

function App() {
  const { loading, isAuthenticated } = useAuth();
  
  // Add debugging information
  useEffect(() => {
    console.log("App loaded", {
      origin: window.location.origin,
      loading,
      isAuthenticated
    });
    
    // Add debug element to DOM
    const debugDiv = document.createElement('div');
    debugDiv.style.position = 'fixed';
    debugDiv.style.bottom = '10px';
    debugDiv.style.right = '10px';
    debugDiv.style.background = 'rgba(0,0,0,0.7)';
    debugDiv.style.color = 'white';
    debugDiv.style.padding = '10px';
    debugDiv.style.borderRadius = '5px';
    debugDiv.style.zIndex = '9999';
    debugDiv.style.fontSize = '12px';
    debugDiv.innerText = `React App Loaded: ${new Date().toISOString()}`;
    document.body.appendChild(debugDiv);
  }, [loading, isAuthenticated]);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <MantineProvider theme={{ colorScheme: 'light' }}>
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/login" element={
              isAuthenticated ? <Navigate to="/dashboard" /> : <Login />
            } />
            <Route path="/register" element={
              isAuthenticated ? <Navigate to="/dashboard" /> : <Register />
            } />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/calendar" element={
              <ProtectedRoute>
                <Calendar />
              </ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} />
          </Routes>
        </main>
      </div>
    </MantineProvider>
  );
}

export default App; 