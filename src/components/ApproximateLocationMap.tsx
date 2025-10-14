/**
 * Approximate Location Map Component
 * Shows a circular area on OpenStreetMap around approximate coordinates
 * Similar to Airbnb's approach - shows neighborhood without exact address
 */

import { useEffect, useRef } from 'react';

interface ApproximateLocationMapProps {
  latitude: number;
  longitude: number;
  locationName: string;
}

export function ApproximateLocationMap({
  latitude,
  longitude,
  locationName,
}: ApproximateLocationMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);

  useEffect(() => {
    // Only initialize map once
    if (mapInstanceRef.current || !mapRef.current) return;

    // Dynamically import Leaflet to avoid SSR issues
    import('leaflet').then((L) => {
      if (!mapRef.current) return;

      // Initialize map
      const map = L.map(mapRef.current, {
        center: [latitude, longitude],
        zoom: 13,
        zoomControl: true,
        scrollWheelZoom: false,
      });

      // Add OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      // Add circular area (radius in meters)
      const circle = L.circle([latitude, longitude], {
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.2,
        radius: 500, // 500 meters radius
        weight: 2,
      }).addTo(map);

      // Add popup with location name
      circle.bindPopup(
        `<div style="text-align: center; padding: 4px;">
          <strong>${locationName}</strong><br/>
          <span style="font-size: 12px; color: #666;">Approximate area</span>
        </div>`
      );

      mapInstanceRef.current = map;
    });

    // Cleanup
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [latitude, longitude, locationName]);

  return (
    <div className="relative">
      <div
        ref={mapRef}
        className="w-full h-48 rounded-lg border border-gray-300 overflow-hidden"
        style={{ zIndex: 0 }}
      />
      <div className="mt-2 text-xs text-gray-500 text-center">
        Approximate location • Exact address shown after booking
      </div>
    </div>
  );
}
