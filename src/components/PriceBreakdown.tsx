/**
 * Price Breakdown Component
 * Shows detailed price breakdown in a tooltip on hover
 */

import { useState } from 'react';

interface PriceBreakdownProps {
  nights: number;
  nightlyRate: number;
  cleaningFee?: number;
  petFee?: number;
  earlyCheckinFee?: number;
  lateCheckoutFee?: number;
  serviceFee?: number;
  total: number;
}

export function PriceBreakdown({
  nights,
  nightlyRate,
  cleaningFee = 0,
  petFee = 0,
  earlyCheckinFee = 0,
  lateCheckoutFee = 0,
  serviceFee = 0,
  total,
}: PriceBreakdownProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const subtotal = nightlyRate * nights;

  return (
    <div className="relative inline-block">
      <button
        type="button"
        className="text-lg font-bold text-gray-900 underline decoration-dotted cursor-help hover:text-blue-600 transition-colors"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip(!showTooltip)}
      >
        ${total.toFixed(2)}
      </button>

      {showTooltip && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 bg-gray-900 text-white text-sm rounded-lg shadow-xl p-4 z-50">
          {/* Arrow */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-px">
            <div className="border-8 border-transparent border-t-gray-900"></div>
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold border-b border-gray-700 pb-2 mb-2">
              Price Breakdown
            </h4>

            {/* Nightly rate */}
            <div className="flex justify-between text-xs">
              <span className="text-gray-300">
                ${nightlyRate.toFixed(2)} × {nights} {nights === 1 ? 'night' : 'nights'}
              </span>
              <span className="font-medium">${subtotal.toFixed(2)}</span>
            </div>

            {/* Cleaning fee */}
            {cleaningFee > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-300">Cleaning fee</span>
                <span className="font-medium">${cleaningFee.toFixed(2)}</span>
              </div>
            )}

            {/* Pet fee */}
            {petFee > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-300">Pet fee</span>
                <span className="font-medium">${petFee.toFixed(2)}</span>
              </div>
            )}

            {/* Early check-in */}
            {earlyCheckinFee > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-300">Early check-in</span>
                <span className="font-medium">${earlyCheckinFee.toFixed(2)}</span>
              </div>
            )}

            {/* Late checkout */}
            {lateCheckoutFee > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-300">Late checkout</span>
                <span className="font-medium">${lateCheckoutFee.toFixed(2)}</span>
              </div>
            )}

            {/* Service fee */}
            {serviceFee > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-300">Service fee</span>
                <span className="font-medium">${serviceFee.toFixed(2)}</span>
              </div>
            )}

            {/* Total */}
            <div className="flex justify-between text-sm font-bold border-t border-gray-700 pt-2 mt-2">
              <span>Total</span>
              <span>${total.toFixed(2)}</span>
            </div>
          </div>

          <p className="text-xs text-gray-400 mt-3 text-center">
            Hover to view details
          </p>
        </div>
      )}
    </div>
  );
}
