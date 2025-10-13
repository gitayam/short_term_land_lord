import type { Property } from '../../types';
import { WifiQRCode } from './WifiQRCode';

interface GuestPreviewModalProps {
  property: Property;
  isOpen: boolean;
  onClose: () => void;
}

export function GuestPreviewModal({ property, isOpen, onClose }: GuestPreviewModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-8 rounded-t-lg">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold mb-2">{property.name || 'Welcome to Your Stay'}</h1>
              <p className="text-blue-100 text-lg">{property.address}</p>
              <div className="flex gap-2 mt-3">
                {property.property_type && (
                  <div className="inline-block bg-white bg-opacity-20 px-4 py-1 rounded-full">
                    <span className="text-sm font-medium capitalize">{property.property_type.replace('_', ' ')}</span>
                  </div>
                )}
                {property.city && property.state && (
                  <div className="inline-block bg-white bg-opacity-20 px-4 py-1 rounded-full">
                    <span className="text-sm font-medium">{property.city}, {property.state}</span>
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition-colors"
              aria-label="Close"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-8 space-y-8">
          {/* Welcome Message */}
          {property.description && (
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border-l-4 border-blue-600">
              <h2 className="text-xl font-bold text-gray-900 mb-3">Welcome! 🎉</h2>
              <p className="text-gray-700 text-lg leading-relaxed">{property.description}</p>
            </div>
          )}

          {/* Property At-a-Glance */}
          <div className="border-t pt-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">🏠 Your Space</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {property.bedrooms && (
                <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border-2 border-blue-200">
                  <div className="text-4xl mb-2">🛏️</div>
                  <div className="font-bold text-2xl text-gray-900">{property.bedrooms}</div>
                  <div className="text-sm text-gray-600 font-medium">Bedrooms</div>
                </div>
              )}
              {property.bathrooms && (
                <div className="text-center p-4 bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-lg border-2 border-cyan-200">
                  <div className="text-4xl mb-2">🚿</div>
                  <div className="font-bold text-2xl text-gray-900">{property.bathrooms}</div>
                  <div className="text-sm text-gray-600 font-medium">Bathrooms</div>
                </div>
              )}
              {property.total_beds && (
                <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border-2 border-purple-200">
                  <div className="text-4xl mb-2">🛌</div>
                  <div className="font-bold text-2xl text-gray-900">{property.total_beds}</div>
                  <div className="text-sm text-gray-600 font-medium">Total Beds</div>
                </div>
              )}
              {property.square_feet && (
                <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border-2 border-green-200">
                  <div className="text-4xl mb-2">📐</div>
                  <div className="font-bold text-2xl text-gray-900">{property.square_feet}</div>
                  <div className="text-sm text-gray-600 font-medium">Sq Ft</div>
                </div>
              )}
            </div>
            {property.bed_sizes && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-start gap-2">
                  <span className="text-2xl">🛏️</span>
                  <div>
                    <div className="font-semibold text-gray-900 mb-1">Sleeping Arrangements</div>
                    <div className="text-gray-700">{property.bed_sizes}</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* CHECK-IN INFORMATION - MOST CRITICAL */}
          <div className="border-t pt-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">🔑 Check-In Information</h2>

            {/* Check-in/Check-out Times */}
            {(property.checkin_time || property.checkout_time) && (
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                {property.checkin_time && (
                  <div className="flex items-center gap-3 p-5 bg-green-50 rounded-lg border-2 border-green-300">
                    <div className="text-3xl">✅</div>
                    <div>
                      <div className="text-sm text-green-700 font-medium uppercase">Check-In</div>
                      <div className="text-2xl font-bold text-green-900">{property.checkin_time}</div>
                    </div>
                  </div>
                )}
                {property.checkout_time && (
                  <div className="flex items-center gap-3 p-5 bg-orange-50 rounded-lg border-2 border-orange-300">
                    <div className="text-3xl">🚪</div>
                    <div>
                      <div className="text-sm text-orange-700 font-medium uppercase">Check-Out</div>
                      <div className="text-2xl font-bold text-orange-900">{property.checkout_time}</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Check-in Instructions */}
            {property.guest_checkin_instructions && (
              <div className="mb-4 p-6 bg-green-50 rounded-lg border-2 border-green-300">
                <h3 className="font-bold text-lg text-green-900 mb-3 flex items-center gap-2">
                  <span>📋</span> Check-In Instructions
                </h3>
                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{property.guest_checkin_instructions}</p>
              </div>
            )}

            {/* Entry/Access Instructions */}
            {property.entry_instructions && (
              <div className="p-6 bg-blue-50 rounded-lg border-2 border-blue-300">
                <h3 className="font-bold text-lg text-blue-900 mb-3 flex items-center gap-2">
                  <span>🚪</span> How to Enter the Property
                </h3>
                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{property.entry_instructions}</p>
              </div>
            )}
          </div>

          {/* WiFi - CRITICAL with QR CODE */}
          {(property.wifi_network || property.wifi_password) && (
            <div className="border-t pt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">📶 WiFi Connection</h2>
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-lg border-2 border-blue-300">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    {property.wifi_network && (
                      <div>
                        <div className="text-sm text-blue-700 font-semibold uppercase mb-1">Network Name (SSID)</div>
                        <div className="text-2xl font-bold font-mono text-blue-900 bg-white p-3 rounded border-2 border-blue-200">
                          {property.wifi_network}
                        </div>
                      </div>
                    )}
                    {property.wifi_password && (
                      <div>
                        <div className="text-sm text-blue-700 font-semibold uppercase mb-1">Password</div>
                        <div className="text-2xl font-bold font-mono text-blue-900 bg-white p-3 rounded border-2 border-blue-200 break-all">
                          {property.wifi_password}
                        </div>
                      </div>
                    )}
                    {property.guest_wifi_instructions && (
                      <div className="pt-3 border-t border-blue-200">
                        <p className="text-sm text-gray-700 leading-relaxed">{property.guest_wifi_instructions}</p>
                      </div>
                    )}
                  </div>

                  {/* QR Code */}
                  {property.wifi_network && property.wifi_password && (
                    <div className="flex flex-col items-center justify-center bg-white p-6 rounded-lg border-2 border-blue-200">
                      <WifiQRCode
                        ssid={property.wifi_network}
                        password={property.wifi_password}
                      />
                      <div className="mt-3 text-center">
                        <p className="text-sm font-semibold text-gray-900">📱 Scan to Connect</p>
                        <p className="text-xs text-gray-600 mt-1">Point your phone camera at this code</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* House Rules - IMPORTANT */}
          {property.guest_rules && (
            <div className="border-t pt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">📜 House Rules</h2>
              <div className="bg-yellow-50 p-6 rounded-lg border-2 border-yellow-300">
                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{property.guest_rules}</p>
              </div>
            </div>
          )}

          {/* What's Included - Amenities */}
          <div className="border-t pt-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">✨ What's Included</h2>
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {property.wifi_network && (
                  <div className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-2xl">📶</span>
                    <div>
                      <div className="font-semibold text-gray-900">WiFi</div>
                      <div className="text-xs text-gray-600">High-speed internet</div>
                    </div>
                  </div>
                )}
                {property.number_of_tvs && property.number_of_tvs > 0 && (
                  <div className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-2xl">📺</span>
                    <div>
                      <div className="font-semibold text-gray-900">{property.number_of_tvs} TV{property.number_of_tvs > 1 ? 's' : ''}</div>
                      <div className="text-xs text-gray-600">Entertainment</div>
                    </div>
                  </div>
                )}
                {property.number_of_showers && property.number_of_showers > 0 && (
                  <div className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-2xl">🚿</span>
                    <div>
                      <div className="font-semibold text-gray-900">{property.number_of_showers} Shower{property.number_of_showers > 1 ? 's' : ''}</div>
                      <div className="text-xs text-gray-600">Private bathrooms</div>
                    </div>
                  </div>
                )}
                {property.number_of_tubs && property.number_of_tubs > 0 && (
                  <div className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-2xl">🛁</span>
                    <div>
                      <div className="font-semibold text-gray-900">{property.number_of_tubs} Bathtub{property.number_of_tubs > 1 ? 's' : ''}</div>
                      <div className="text-xs text-gray-600">Relaxation</div>
                    </div>
                  </div>
                )}
                {property.cleaning_supplies_location && (
                  <div className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-2xl">🧹</span>
                    <div>
                      <div className="font-semibold text-gray-900">Cleaning Supplies</div>
                      <div className="text-xs text-gray-600">{property.cleaning_supplies_location}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Trash & Recycling Schedule - IMPORTANT FOR GUESTS */}
          {(property.trash_day || property.recycling_day) && (
            <div className="border-t pt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span>🗑️</span> Trash & Recycling Schedule
              </h2>
              <p className="text-gray-600 mb-4">Please help us keep the property clean by following these guidelines:</p>
              <div className="grid md:grid-cols-2 gap-4">
                {property.trash_day && (
                  <div className="border-2 border-gray-400 bg-gray-50 p-6 rounded-lg">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-3xl">🗑️</span>
                      <h3 className="font-bold text-xl text-gray-900">Trash Day</h3>
                    </div>
                    <div className="space-y-3 text-gray-800">
                      <div className="bg-white p-4 rounded-lg border-2 border-gray-300">
                        <div className="text-sm text-gray-600 uppercase font-semibold">Collection Day</div>
                        <div className="text-3xl font-bold text-blue-600 mt-1">{property.trash_day}</div>
                      </div>
                      {property.trash_schedule_type && (
                        <div className="flex items-center gap-2 text-lg">
                          <span className="font-semibold">Frequency:</span>
                          <span className="capitalize font-medium">{property.trash_schedule_type}</span>
                        </div>
                      )}
                      {property.trash_schedule_details && (
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                          <p className="text-sm font-medium text-gray-800">{property.trash_schedule_details}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                {property.recycling_day && (
                  <div className="border-2 border-green-400 bg-green-50 p-6 rounded-lg">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-3xl">♻️</span>
                      <h3 className="font-bold text-xl text-green-900">Recycling Day</h3>
                    </div>
                    <div className="space-y-3 text-gray-800">
                      <div className="bg-white p-4 rounded-lg border-2 border-green-300">
                        <div className="text-sm text-green-700 uppercase font-semibold">Collection Day</div>
                        <div className="text-3xl font-bold text-green-600 mt-1">{property.recycling_day}</div>
                      </div>
                      {property.recycling_schedule_type && (
                        <div className="flex items-center gap-2 text-lg">
                          <span className="font-semibold">Frequency:</span>
                          <span className="capitalize font-medium">{property.recycling_schedule_type}</span>
                        </div>
                      )}
                      {property.recycling_schedule_details && (
                        <div className="p-4 bg-green-100 rounded-lg border border-green-300">
                          <p className="text-sm font-medium text-gray-800">{property.recycling_schedule_details}</p>
                        </div>
                      )}
                      {property.recycling_notes && (
                        <div className="p-4 bg-green-200 rounded-lg border-2 border-green-400">
                          <p className="text-sm font-bold text-green-900">📝 Important: {property.recycling_notes}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Special Instructions */}
          {property.special_instructions && (
            <div className="border-t pt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">💡 Important Notes</h2>
              <div className="bg-purple-50 p-6 rounded-lg border-2 border-purple-300">
                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{property.special_instructions}</p>
              </div>
            </div>
          )}

          {/* Local Attractions & Recommendations */}
          {property.local_attractions && (
            <div className="border-t pt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">🎯 Things to Do Nearby</h2>
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-lg border-2 border-purple-300">
                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{property.local_attractions}</p>
              </div>
            </div>
          )}

          {/* Check-out Instructions */}
          {property.guest_checkout_instructions && (
            <div className="border-t pt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">🧳 Check-Out Instructions</h2>
              <div className="bg-orange-50 p-6 rounded-lg border-2 border-orange-300">
                <h3 className="font-semibold text-orange-900 mb-3">Before you leave, please:</h3>
                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{property.guest_checkout_instructions}</p>
              </div>
            </div>
          )}

          {/* Emergency Contact */}
          {property.emergency_contact && (
            <div className="border-t pt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">🚨 Emergency Contact</h2>
              <div className="bg-red-50 p-6 rounded-lg border-2 border-red-400">
                <div className="flex items-start gap-3">
                  <span className="text-3xl">📞</span>
                  <div>
                    <p className="text-lg font-bold text-red-900 mb-2">For emergencies or urgent issues:</p>
                    <p className="text-gray-800 font-semibold text-xl">{property.emergency_contact}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* FAQ */}
          {property.guest_faq && (
            <div className="border-t pt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">❓ Frequently Asked Questions</h2>
              <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{property.guest_faq}</p>
              </div>
            </div>
          )}

          {/* Property Address */}
          <div className="border-t pt-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">📍 Property Address</h2>
            <div className="bg-blue-50 p-6 rounded-lg border-2 border-blue-300">
              <div className="space-y-2">
                <div className="text-2xl font-bold text-gray-900">{property.name || 'Property'}</div>
                <div className="text-lg font-semibold text-gray-800">{property.address}</div>
                {(property.city || property.state || property.zip_code) && (
                  <div className="text-lg text-gray-700">
                    {property.city && <span>{property.city}</span>}
                    {property.state && <span>, {property.state}</span>}
                    {property.zip_code && <span> {property.zip_code}</span>}
                    {property.country && <span>, {property.country}</span>}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-6 rounded-b-lg border-t">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-white text-center md:text-left">
              <p className="font-semibold">Enjoy your stay! 🌟</p>
              <p className="text-sm text-blue-100">We're here if you need anything</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => window.print()}
                className="px-6 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition-colors flex items-center gap-2"
              >
                <span>🖨️</span> Print Guide
              </button>
              <button
                onClick={onClose}
                className="px-6 py-3 bg-white bg-opacity-20 text-white font-semibold rounded-lg hover:bg-opacity-30 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
