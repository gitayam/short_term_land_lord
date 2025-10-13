/**
 * Offline Indicator Component
 * Shows a banner when the user loses internet connection
 */

import { useState, useEffect } from 'react';

export function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [wasOffline, setWasOffline] = useState(false);
  const [showReconnected, setShowReconnected] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);

      // Show "reconnected" message briefly if user was offline
      if (wasOffline) {
        setShowReconnected(true);
        setTimeout(() => {
          setShowReconnected(false);
          setWasOffline(false);
        }, 3000);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setWasOffline(true);
      setShowReconnected(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [wasOffline]);

  // Show reconnected message
  if (showReconnected) {
    return (
      <div className="fixed top-0 left-0 right-0 z-50 bg-green-600 text-white px-4 py-2 text-center animate-slide-down">
        <div className="flex items-center justify-center gap-2">
          <span className="text-lg">✓</span>
          <span className="text-sm font-medium">Back online</span>
        </div>
      </div>
    );
  }

  // Show offline banner
  if (!isOnline) {
    return (
      <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-500 text-white px-4 py-2 text-center animate-slide-down">
        <div className="flex items-center justify-center gap-2">
          <span className="text-lg">⚠️</span>
          <span className="text-sm font-medium">
            You're offline. Changes will sync when connection is restored.
          </span>
        </div>
      </div>
    );
  }

  return null;
}
