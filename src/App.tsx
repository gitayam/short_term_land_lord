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
import { ConvertGuestPage } from './pages/auth/ConvertGuestPage';
import { FinancialPage } from './pages/financial/FinancialPage';
import { ExpensesPage } from './pages/financial/ExpensesPage';
import { RevenuePage } from './pages/financial/RevenuePage';
import { InvoicesPage } from './pages/financial/InvoicesPage';
import { InventoryCatalogPage } from './pages/inventory/InventoryCatalogPage';
import { InventoryItemsPage } from './pages/inventory/InventoryItemsPage';
import { GuidebookPage } from './pages/guidebook/GuidebookPage';
import { AccessCodesPage } from './pages/access-codes/AccessCodesPage';
import { GuestPortalPage } from './pages/guest/GuestPortalPage';
import { GuestStayVerificationPage } from './pages/guest/GuestStayVerificationPage';
import { GuestStayDetailsPage } from './pages/guest/GuestStayDetailsPage';
import { BookingsPage } from './pages/bookings/BookingsPage';
import { MessagesPage } from './pages/messages/MessagesPage';
import { WorkersPage } from './pages/workers/WorkersPage';
import { WorkerDetailPage } from './pages/workers/WorkerDetailPage';
import { RepairRequestsPage } from './pages/repair-requests/RepairRequestsPage';
import { RepairRequestDetailPage } from './pages/repair-requests/RepairRequestDetailPage';
import { StaffDashboardPage } from './pages/staff/StaffDashboardPage';
import { PublicPropertyPage } from './pages/public/PublicPropertyPage';
import { LandingPage } from './pages/LandingPage';
import { BookingRequestsPage } from './pages/booking-requests/BookingRequestsPage';
import { BookingConfirmationPage } from './pages/bookings/BookingConfirmationPage';
import { InstallPrompt, IOSInstallInstructions } from './components/pwa/InstallPrompt';
import { OfflineIndicator } from './components/pwa/OfflineIndicator';

function App() {
  return (
    <AuthProvider>
      <OfflineIndicator />
      <InstallPrompt />
      <IOSInstallInstructions />
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/convert-guest" element={<ConvertGuestPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/guest/:accessCode" element={<GuestPortalPage />} />
        <Route path="/guest-stay/verify" element={<GuestStayVerificationPage />} />
        <Route path="/guest-stay/details" element={<GuestStayDetailsPage />} />
        <Route path="/p/:id" element={<PublicPropertyPage />} />
        <Route path="/booking/:id/confirmation" element={<BookingConfirmationPage />} />

        {/* Protected routes */}
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/app/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="properties" element={<PropertiesPage />} />
          <Route path="properties/:id" element={<PropertyDetailPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="cleaning" element={<CleaningSessionsPage />} />
          <Route path="financial" element={<FinancialPage />} />
          <Route path="financial/expenses" element={<ExpensesPage />} />
          <Route path="financial/revenue" element={<RevenuePage />} />
          <Route path="financial/invoices" element={<InvoicesPage />} />
          <Route path="inventory/catalog" element={<InventoryCatalogPage />} />
          <Route path="inventory/items" element={<InventoryItemsPage />} />
          <Route path="guidebook" element={<GuidebookPage />} />
          <Route path="access-codes" element={<AccessCodesPage />} />
          <Route path="bookings" element={<BookingsPage />} />
          <Route path="booking-requests" element={<BookingRequestsPage />} />
          <Route path="messages" element={<MessagesPage />} />
          <Route path="workers" element={<WorkersPage />} />
          <Route path="workers/:id" element={<WorkerDetailPage />} />
          <Route path="repair-requests" element={<RepairRequestsPage />} />
          <Route path="repair-requests/:id" element={<RepairRequestDetailPage />} />
          <Route path="staff" element={<StaffDashboardPage />} />
        </Route>

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
