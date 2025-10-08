import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { authApi } from '../../services/api';

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('Invalid verification link');
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token: string) => {
    try {
      const response = await authApi.verifyEmail(token);
      setStatus('success');
      setMessage(response.message || 'Email verified successfully');
    } catch (error: any) {
      setStatus('error');
      setMessage(error.message || 'Failed to verify email');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full">
        <div className="card text-center">
          {status === 'loading' && (
            <div>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Verifying your email...</p>
            </div>
          )}

          {status === 'success' && (
            <div>
              <div className="text-5xl mb-4">✅</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Verified!</h2>
              <p className="text-gray-600 mb-6">{message}</p>
              <Link to="/login" className="btn-primary inline-block">
                Continue to Login
              </Link>
            </div>
          )}

          {status === 'error' && (
            <div>
              <div className="text-5xl mb-4">❌</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Verification Failed</h2>
              <p className="text-gray-600 mb-6">{message}</p>
              <Link to="/login" className="btn-secondary inline-block">
                Back to Login
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
