/**
 * Service Worker Registration Utility
 * Registers the service worker and handles updates
 */

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | undefined> {
  if (!('serviceWorker' in navigator)) {
    console.log('[SW] Service workers are not supported in this browser');
    return undefined;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });

    console.log('[SW] Service worker registered successfully:', registration.scope);

    // Check for updates periodically
    setInterval(() => {
      registration.update();
    }, 60 * 60 * 1000); // Check every hour

    // Handle updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (!newWorker) return;

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New service worker available, show update prompt
          console.log('[SW] New version available! Please refresh.');

          // Dispatch custom event that can be caught by React
          window.dispatchEvent(new CustomEvent('sw-update-available'));
        }
      });
    });

    return registration;
  } catch (error) {
    console.error('[SW] Service worker registration failed:', error);
    return undefined;
  }
}

export async function unregisterServiceWorker(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration) {
      const unregistered = await registration.unregister();
      console.log('[SW] Service worker unregistered:', unregistered);
      return unregistered;
    }
    return false;
  } catch (error) {
    console.error('[SW] Service worker unregistration failed:', error);
    return false;
  }
}

/**
 * Check if the app is running in standalone mode (installed as PWA)
 */
export function isPWAInstalled(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true || // iOS
    document.referrer.includes('android-app://') // Android
  );
}

/**
 * Request persistent storage for offline data
 */
export async function requestPersistentStorage(): Promise<boolean> {
  if ('storage' in navigator && 'persist' in navigator.storage) {
    try {
      const isPersisted = await navigator.storage.persist();
      console.log('[SW] Persistent storage:', isPersisted ? 'granted' : 'denied');
      return isPersisted;
    } catch (error) {
      console.error('[SW] Persistent storage request failed:', error);
      return false;
    }
  }
  return false;
}

/**
 * Get storage quota information
 */
export async function getStorageQuota(): Promise<{ usage: number; quota: number } | null> {
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    try {
      const estimate = await navigator.storage.estimate();
      return {
        usage: estimate.usage || 0,
        quota: estimate.quota || 0,
      };
    } catch (error) {
      console.error('[SW] Storage quota check failed:', error);
      return null;
    }
  }
  return null;
}
