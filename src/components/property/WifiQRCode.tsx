import { useEffect, useRef, useState } from 'react';
import QRCode from 'qrcode';

interface WifiQRCodeProps {
  ssid: string;
  password: string;
  encryption?: 'WPA' | 'WEP' | 'nopass';
  hidden?: boolean;
}

export function WifiQRCode({
  ssid,
  password,
  encryption = 'WPA',
  hidden = false
}: WifiQRCodeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canvasRef.current || !ssid) return;

    // WiFi QR code format: WIFI:T:WPA;S:MyNetwork;P:MyPassword;H:false;;
    const wifiString = `WIFI:T:${encryption};S:${ssid};P:${password};H:${hidden};;`;

    QRCode.toCanvas(
      canvasRef.current,
      wifiString,
      {
        width: 200,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF',
        },
      },
      (err) => {
        if (err) {
          setError('Failed to generate QR code');
          console.error(err);
        }
      }
    );
  }, [ssid, password, encryption, hidden]);

  if (!ssid) return null;

  return (
    <div className="flex flex-col items-center">
      {error ? (
        <div className="text-red-600 text-sm">{error}</div>
      ) : (
        <>
          <canvas ref={canvasRef} className="border-4 border-white shadow-lg rounded-lg" />
          <p className="text-xs text-gray-600 mt-2 text-center">
            Scan to connect automatically
          </p>
        </>
      )}
    </div>
  );
}
