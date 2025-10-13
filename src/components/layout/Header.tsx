import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export function Header() {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/app/dashboard" className="flex items-center">
              <h1 className="text-xl font-bold text-blue-600">
                Short Term Land Lord
              </h1>
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.firstName} {user?.lastName}
            </span>
            <span className="text-xs text-gray-500 badge badge-pending">
              {user?.role.replace('_', ' ')}
            </span>
            {!user?.email_verified && (
              <span className="text-xs text-yellow-600 badge bg-yellow-50">
                Email not verified
              </span>
            )}
            <button
              onClick={handleLogout}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
