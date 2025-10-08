import { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { authApi } from '../../services/api';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const token = searchParams.get('token');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError('Invalid reset link');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      await authApi.resetPassword(token, password);
      navigate('/login?reset=success');
    } catch (err: any) {
      setError(err.message || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="max-w-md w-full">
          <div className="card text-center">
            <div className="text-5xl mb-4">❌</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Invalid Reset Link</h2>
            <p className="text-gray-600 mb-6">
              This password reset link is invalid or has expired.
            </p>
            <Link to="/forgot-password" className="btn-secondary inline-block">
              Request New Link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full">
        <div className="card">
          <h2 className="text-2xl font-bold text-center text-gray-900 mb-2">
            Reset your password
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Choose a new password for your account
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                New password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
              />
              <p className="mt-1 text-xs text-gray-500">
                Must be at least 8 characters with uppercase, lowercase, and numbers
              </p>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                Confirm password
              </label>
              <input
                id="confirmPassword"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Resetting password...' : 'Reset password'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-600">
            Remember your password?{' '}
            <Link to="/login" className="text-blue-600 hover:text-blue-500 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
