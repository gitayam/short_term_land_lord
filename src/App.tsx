import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Layout } from './components/layout/Layout';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { PropertiesPage } from './pages/properties/PropertiesPage';
import { PropertyDetailPage } from './pages/properties/PropertyDetailPage';
import { TasksPage } from './pages/tasks/TasksPage';
import { CalendarPage } from './pages/calendar/CalendarPage';
import { CleaningSessionsPage } from './pages/cleaning/CleaningSessionsPage';
import { VerifyEmailPage } from './pages/auth/VerifyEmailPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="properties" element={<PropertiesPage />} />
          <Route path="properties/:id" element={<PropertyDetailPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="cleaning" element={<CleaningSessionsPage />} />
        </Route>

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
