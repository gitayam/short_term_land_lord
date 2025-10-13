/**
 * Property Share Card Component
 * Generate shareable links and QR codes for property
 */

import { useState, useEffect } from 'react';
import QRCode from 'qrcode';

interface PropertyShareCardProps {
  propertyId: string;
  propertyName: string;
  guestAccessToken: string;
  guestAccessEnabled: boolean;
}

export function PropertyShareCard({
  propertyId,
  propertyName,
  guestAccessToken,
  guestAccessEnabled,
}: PropertyShareCardProps) {
  const [qrCodeDataUrl, setQrCodeDataUrl] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [showQR, setShowQR] = useState(false);

  // Generate shareable URL
  const shareUrl = guestAccessToken
    ? `${window.location.origin}/p/${propertyId}?token=${guestAccessToken}`
    : `${window.location.origin}/p/${propertyId}`;

  useEffect(() => {
    // Generate QR code
    if (showQR) {
      QRCode.toDataURL(shareUrl, {
        width: 300,
        margin: 2,
        color: {
          dark: '#1F2937',
          light: '#FFFFFF',
        },
      })
        .then((url) => setQrCodeDataUrl(url))
        .catch((err) => console.error('QR Code generation failed:', err));
    }
  }, [shareUrl, showQR]);

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownloadQR = () => {
    if (!qrCodeDataUrl) return;

    const link = document.createElement('a');
    link.href = qrCodeDataUrl;
    link.download = `${propertyName.replace(/\s+/g, '-')}-QR-Code.png`;
    link.click();
  };

  if (!guestAccessEnabled) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🔗 Share Property</h2>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            <strong>Guest Access Disabled</strong>
          </p>
          <p className="text-sm text-yellow-700 mt-1">
            Enable guest access in the property settings to share this property with potential guests.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">🔗 Share Property</h2>
      <p className="text-sm text-gray-600 mb-4">
        Share this link with potential guests to showcase your property
      </p>

      {/* Shareable Link */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Shareable Link
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={shareUrl}
            readOnly
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm font-mono"
          />
          <button
            onClick={handleCopyLink}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              copied
                ? 'bg-green-600 text-white'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {copied ? '✓ Copied!' : '📋 Copy'}
          </button>
        </div>
      </div>

      {/* QR Code Section */}
      <div className="border-t border-gray-200 pt-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">QR Code</h3>
          <button
            onClick={() => setShowQR(!showQR)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {showQR ? 'Hide QR Code' : 'Show QR Code'}
          </button>
        </div>

        {showQR && (
          <div className="space-y-4">
            {qrCodeDataUrl ? (
              <>
                <div className="flex justify-center bg-gray-50 rounded-lg p-6">
                  <img src={qrCodeDataUrl} alt="QR Code" className="rounded" />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleDownloadQR}
                    className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
                  >
                    📥 Download QR Code
                  </button>
                </div>
                <p className="text-xs text-gray-500 text-center">
                  Print this QR code on flyers, business cards, or post it at your property
                </p>
              </>
            ) : (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Share Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
        <h4 className="font-semibold text-blue-900 mb-2">💡 Sharing Tips</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Share the link via email, text, or social media</li>
          <li>• Add the QR code to your business cards or flyers</li>
          <li>• Post the link on your website or social profiles</li>
          <li>• Send it to past guests who might want to rebook</li>
        </ul>
      </div>

      {/* Security Note */}
      {guestAccessToken && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
          <p className="text-xs text-gray-600">
            <strong>🔒 Security:</strong> This link includes a private access token. Only share it
            with people you trust to view your property details.
          </p>
        </div>
      )}
    </div>
  );
}
