/**
 * Flexible Dates Component
 * Allows guests to search with flexible date ranges (+/- 1-3 days)
 */

import { useState } from 'react';

interface FlexibleDatesProps {
  onFlexibleSearch: (checkIn: string, checkOut: string, flexibility: number) => void;
}

export function FlexibleDates({ onFlexibleSearch }: FlexibleDatesProps) {
  const [isFlexible, setIsFlexible] = useState(false);
  const [flexibility, setFlexibility] = useState(1); // +/- days
  const [approximateCheckIn, setApproximateCheckIn] = useState('');
  const [approximateCheckOut, setApproximateCheckOut] = useState('');

  const handleFlexibleToggle = () => {
    setIsFlexible(!isFlexible);
  };

  const handleSearch = () => {
    if (approximateCheckIn && approximateCheckOut) {
      onFlexibleSearch(approximateCheckIn, approximateCheckOut, flexibility);
    }
  };

  if (!isFlexible) {
    return (
      <div className="mb-4">
        <button
          onClick={handleFlexibleToggle}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          <span>📅</span>
          <span>I'm flexible with dates</span>
        </button>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">Flexible Dates Search</h3>
        <button
          onClick={handleFlexibleToggle}
          className="text-gray-500 hover:text-gray-700 text-sm"
        >
          ✕ Cancel
        </button>
      </div>

      <p className="text-xs text-gray-600 mb-3">
        Find properties available around your preferred dates. We'll show options within your flexibility range.
      </p>

      {/* Approximate Dates */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Approximate Check-in
          </label>
          <input
            type="date"
            value={approximateCheckIn}
            onChange={(e) => setApproximateCheckIn(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            min={new Date().toISOString().split('T')[0]}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Approximate Check-out
          </label>
          <input
            type="date"
            value={approximateCheckOut}
            onChange={(e) => setApproximateCheckOut(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            min={approximateCheckIn || new Date().toISOString().split('T')[0]}
          />
        </div>
      </div>

      {/* Flexibility Slider */}
      <div className="mb-4">
        <label className="block text-xs font-medium text-gray-700 mb-2">
          Date Flexibility: <span className="text-blue-600">±{flexibility} day{flexibility !== 1 ? 's' : ''}</span>
        </label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min="1"
            max="3"
            value={flexibility}
            onChange={(e) => setFlexibility(parseInt(e.target.value))}
            className="flex-1 h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((flexibility - 1) / 2) * 100}%, #dbeafe ${((flexibility - 1) / 2) * 100}%, #dbeafe 100%)`
            }}
          />
          <div className="flex gap-1 text-xs text-gray-500">
            <span className={flexibility === 1 ? 'text-blue-600 font-semibold' : ''}>1</span>
            <span className={flexibility === 2 ? 'text-blue-600 font-semibold' : ''}>2</span>
            <span className={flexibility === 3 ? 'text-blue-600 font-semibold' : ''}>3</span>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          We'll search from {new Date(new Date(approximateCheckIn).getTime() - flexibility * 24 * 60 * 60 * 1000).toLocaleDateString()}
          {' to '}
          {new Date(new Date(approximateCheckOut).getTime() + flexibility * 24 * 60 * 60 * 1000).toLocaleDateString()}
        </p>
      </div>

      {/* Search Button */}
      <button
        onClick={handleSearch}
        disabled={!approximateCheckIn || !approximateCheckOut}
        className={`w-full py-2 rounded-lg font-medium text-sm transition-colors ${
          approximateCheckIn && approximateCheckOut
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        }`}
      >
        🔍 Search with Flexible Dates
      </button>

      {/* Info Box */}
      <div className="mt-3 bg-white rounded-lg p-3 text-xs text-gray-600">
        <p className="flex items-start gap-2">
          <span className="text-blue-500">ℹ️</span>
          <span>
            <strong>Tip:</strong> Increasing flexibility gives you more options and may help you find better rates!
          </span>
        </p>
      </div>
    </div>
  );
}
