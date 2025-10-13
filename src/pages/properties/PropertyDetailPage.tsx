import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { propertiesApi } from '../../services/api';
import { GuestPreviewModal } from '../../components/property/GuestPreviewModal';
import { PropertyImageGallery } from '../../components/property/PropertyImageGallery';
import { PropertyRoomManager } from '../../components/property/PropertyRoomManager';
import { PropertyShareCard } from '../../components/property/PropertyShareCard';
import { CalendarManagement } from '../../components/property/CalendarManagement';
import { CalendarView } from '../../components/property/CalendarView';
import type { Property } from '../../types';

type TabId = 'overview' | 'calendar' | 'details' | 'guest' | 'operations';

const tabs = [
  { id: 'overview' as TabId, name: 'Overview', icon: '🏠' },
  { id: 'calendar' as TabId, name: 'Calendar & Bookings', icon: '📅' },
  { id: 'details' as TabId, name: 'Details', icon: '📋' },
  { id: 'guest' as TabId, name: 'Guest Portal', icon: '👤' },
  { id: 'operations' as TabId, name: 'Operations', icon: '🔧' },
];

export function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [property, setProperty] = useState<Property | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditForm, setShowEditForm] = useState(false);
  const [showGuestPreview, setShowGuestPreview] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    street_address: '',
    city: '',
    state: '',
    zip_code: '',
    country: '',
    property_type: 'house',
    bedrooms: '',
    bathrooms: '',
    square_feet: '',
    year_built: '',
    total_beds: '',
    bed_sizes: '',
    number_of_showers: '',
    number_of_tubs: '',
    number_of_tvs: '',
    description: '',
    // WiFi
    wifi_network: '',
    wifi_password: '',
    // Trash & Recycling
    trash_day: '',
    trash_schedule_type: '',
    trash_schedule_details: '',
    recycling_day: '',
    recycling_schedule_type: '',
    recycling_schedule_details: '',
    recycling_notes: '',
    // Utilities
    internet_provider: '',
    internet_account: '',
    internet_contact: '',
    electric_provider: '',
    electric_account: '',
    electric_contact: '',
    water_provider: '',
    water_account: '',
    water_contact: '',
    trash_provider: '',
    trash_account: '',
    trash_contact: '',
    // Instructions & Access
    cleaning_supplies_location: '',
    entry_instructions: '',
    special_instructions: '',
    checkin_time: '',
    checkout_time: '',
    // Guest Information
    guest_access_enabled: false,
    guest_access_token: '',
    guest_rules: '',
    guest_checkin_instructions: '',
    guest_checkout_instructions: '',
    guest_wifi_instructions: '',
    local_attractions: '',
    emergency_contact: '',
    guest_faq: '',
    // Other
    ical_url: '',
    color: '',
  });

  useEffect(() => {
    if (id) {
      loadProperty(id);
    }
  }, [id]);

  const loadProperty = async (propertyId: string) => {
    try {
      const data = await propertiesApi.get(propertyId);
      setProperty(data.property);
      // Set form data for editing
      const p = data.property;
      setFormData({
        name: p.name || '',
        address: p.address || '',
        street_address: p.street_address || '',
        city: p.city || '',
        state: p.state || '',
        zip_code: p.zip_code || '',
        country: p.country || '',
        property_type: p.property_type || 'house',
        bedrooms: p.bedrooms?.toString() || '',
        bathrooms: p.bathrooms?.toString() || '',
        square_feet: p.square_feet?.toString() || '',
        year_built: p.year_built?.toString() || '',
        total_beds: p.total_beds?.toString() || '',
        bed_sizes: p.bed_sizes || '',
        number_of_showers: p.number_of_showers?.toString() || '',
        number_of_tubs: p.number_of_tubs?.toString() || '',
        number_of_tvs: p.number_of_tvs?.toString() || '',
        description: p.description || '',
        wifi_network: p.wifi_network || '',
        wifi_password: p.wifi_password || '',
        trash_day: p.trash_day || '',
        trash_schedule_type: p.trash_schedule_type || '',
        trash_schedule_details: p.trash_schedule_details || '',
        recycling_day: p.recycling_day || '',
        recycling_schedule_type: p.recycling_schedule_type || '',
        recycling_schedule_details: p.recycling_schedule_details || '',
        recycling_notes: p.recycling_notes || '',
        internet_provider: p.internet_provider || '',
        internet_account: p.internet_account || '',
        internet_contact: p.internet_contact || '',
        electric_provider: p.electric_provider || '',
        electric_account: p.electric_account || '',
        electric_contact: p.electric_contact || '',
        water_provider: p.water_provider || '',
        water_account: p.water_account || '',
        water_contact: p.water_contact || '',
        trash_provider: p.trash_provider || '',
        trash_account: p.trash_account || '',
        trash_contact: p.trash_contact || '',
        cleaning_supplies_location: p.cleaning_supplies_location || '',
        entry_instructions: p.entry_instructions || '',
        special_instructions: p.special_instructions || '',
        checkin_time: p.checkin_time || '',
        checkout_time: p.checkout_time || '',
        guest_access_enabled: p.guest_access_enabled || false,
        guest_access_token: p.guest_access_token || '',
        guest_rules: p.guest_rules || '',
        guest_checkin_instructions: p.guest_checkin_instructions || '',
        guest_checkout_instructions: p.guest_checkout_instructions || '',
        guest_wifi_instructions: p.guest_wifi_instructions || '',
        local_attractions: p.local_attractions || '',
        emergency_contact: p.emergency_contact || '',
        guest_faq: p.guest_faq || '',
        ical_url: p.ical_url || '',
        color: p.color || '',
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load property');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;

    try {
      // Auto-generate full address from structured fields
      const fullAddress = [
        formData.street_address,
        formData.city,
        formData.state,
        formData.zip_code
      ].filter(Boolean).join(', ');

      await propertiesApi.update(id, {
        ...formData,
        address: fullAddress || formData.address, // Use generated address or fallback
      });
      setShowEditForm(false);
      loadProperty(id); // Reload property data
    } catch (error: any) {
      alert(error.message || 'Failed to update property');
    }
  };

  const handleDeleteProperty = async () => {
    if (!id || !property) return;

    if (!confirm(`Are you sure you want to delete "${property.name || 'this property'}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await propertiesApi.delete(id);
      navigate('/properties');
    } catch (error: any) {
      alert(error.message || 'Failed to delete property');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="card text-center py-12">
        <div className="text-5xl mb-4">❌</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Property Not Found</h3>
        <p className="text-gray-600 mb-6">{error}</p>
        <Link to="/app/properties" className="btn-secondary">
          Back to Properties
        </Link>
      </div>
    );
  }

  return (
    <div>
      <Link to="/app/properties" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">
        ← Back to Properties
      </Link>

      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {property.name || 'Unnamed Property'}
          </h1>
          <p className="text-gray-600">{property.address}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowGuestPreview(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            👁️ Guest View
          </button>
          <button
            onClick={() => setShowEditForm(!showEditForm)}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            {showEditForm ? 'Cancel' : 'Edit'}
          </button>
          <button
            onClick={handleDeleteProperty}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </div>

      {showEditForm && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Edit Property</h2>
          <form onSubmit={handleUpdateProperty} className="space-y-6">
            {/* Basic Information */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Property Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input"
                    placeholder="e.g., Beach House"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Property Type
                  </label>
                  <select
                    value={formData.property_type}
                    onChange={(e) => setFormData({ ...formData, property_type: e.target.value })}
                    className="input"
                  >
                    <optgroup label="Houses & Apartments">
                      <option value="house">House</option>
                      <option value="apartment">Apartment</option>
                      <option value="condo">Condo</option>
                      <option value="townhouse">Townhouse</option>
                      <option value="loft">Loft</option>
                      <option value="studio">Studio</option>
                    </optgroup>
                    <optgroup label="Secondary Units">
                      <option value="suite">Suite</option>
                      <option value="guesthouse">Guesthouse</option>
                      <option value="guest-suite">Guest Suite</option>
                      <option value="in-law-unit">In-Law Unit</option>
                    </optgroup>
                    <optgroup label="Luxury & Unique">
                      <option value="villa">Villa</option>
                      <option value="cottage">Cottage</option>
                      <option value="bungalow">Bungalow</option>
                      <option value="cabin">Cabin</option>
                      <option value="chalet">Chalet</option>
                      <option value="castle">Castle</option>
                    </optgroup>
                    <optgroup label="Unique Spaces">
                      <option value="treehouse">Treehouse</option>
                      <option value="yurt">Yurt</option>
                      <option value="tiny-house">Tiny House</option>
                      <option value="barn">Barn</option>
                      <option value="farm-stay">Farm Stay</option>
                      <option value="houseboat">Houseboat</option>
                    </optgroup>
                    <optgroup label="Commercial">
                      <option value="bed-and-breakfast">Bed & Breakfast</option>
                      <option value="boutique-hotel">Boutique Hotel</option>
                      <option value="hostel">Hostel</option>
                    </optgroup>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="input"
                    rows={3}
                    placeholder="Property description..."
                  />
                </div>
              </div>
            </div>

            {/* Location */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">Location</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Address *
                  </label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    className="input"
                    placeholder="Full address"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Street Address
                  </label>
                  <input
                    type="text"
                    value={formData.street_address}
                    onChange={(e) => setFormData({ ...formData, street_address: e.target.value })}
                    className="input"
                    placeholder="123 Main St"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="input"
                    placeholder="City"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    State
                  </label>
                  <input
                    type="text"
                    value={formData.state}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    className="input"
                    placeholder="CA"
                    maxLength={2}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ZIP Code
                  </label>
                  <input
                    type="text"
                    value={formData.zip_code}
                    onChange={(e) => setFormData({ ...formData, zip_code: e.target.value })}
                    className="input"
                    placeholder="90210"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    className="input"
                    placeholder="USA"
                  />
                </div>
              </div>
            </div>

            {/* Property Features */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">Property Features</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bedrooms
                  </label>
                  <input
                    type="number"
                    value={formData.bedrooms}
                    onChange={(e) => setFormData({ ...formData, bedrooms: e.target.value })}
                    className="input"
                    placeholder="3"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bathrooms
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={formData.bathrooms}
                    onChange={(e) => setFormData({ ...formData, bathrooms: e.target.value })}
                    className="input"
                    placeholder="2"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Square Feet
                  </label>
                  <input
                    type="number"
                    value={formData.square_feet}
                    onChange={(e) => setFormData({ ...formData, square_feet: e.target.value })}
                    className="input"
                    placeholder="1500"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Year Built
                  </label>
                  <input
                    type="number"
                    value={formData.year_built}
                    onChange={(e) => setFormData({ ...formData, year_built: e.target.value })}
                    className="input"
                    placeholder="2020"
                    min="1800"
                    max="2100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Total Beds
                  </label>
                  <input
                    type="number"
                    value={formData.total_beds}
                    onChange={(e) => setFormData({ ...formData, total_beds: e.target.value })}
                    className="input"
                    placeholder="4"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bed Sizes
                  </label>
                  <input
                    type="text"
                    value={formData.bed_sizes}
                    onChange={(e) => setFormData({ ...formData, bed_sizes: e.target.value })}
                    className="input"
                    placeholder="1 King, 2 Queen"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Showers
                  </label>
                  <input
                    type="number"
                    value={formData.number_of_showers}
                    onChange={(e) => setFormData({ ...formData, number_of_showers: e.target.value })}
                    className="input"
                    placeholder="2"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bathtubs
                  </label>
                  <input
                    type="number"
                    value={formData.number_of_tubs}
                    onChange={(e) => setFormData({ ...formData, number_of_tubs: e.target.value })}
                    className="input"
                    placeholder="1"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    TVs
                  </label>
                  <input
                    type="number"
                    value={formData.number_of_tvs}
                    onChange={(e) => setFormData({ ...formData, number_of_tvs: e.target.value })}
                    className="input"
                    placeholder="3"
                    min="0"
                  />
                </div>
              </div>
            </div>

            {/* WiFi & Network */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">WiFi & Network</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    WiFi Network Name
                  </label>
                  <input
                    type="text"
                    value={formData.wifi_network}
                    onChange={(e) => setFormData({ ...formData, wifi_network: e.target.value })}
                    className="input"
                    placeholder="BeachHouse_WiFi"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    WiFi Password
                  </label>
                  <input
                    type="text"
                    value={formData.wifi_password}
                    onChange={(e) => setFormData({ ...formData, wifi_password: e.target.value })}
                    className="input"
                    placeholder="Password123!"
                  />
                </div>
              </div>
            </div>

            {/* Trash & Recycling Schedule */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">Trash & Recycling Schedule</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trash Day
                  </label>
                  <select
                    value={formData.trash_day}
                    onChange={(e) => setFormData({ ...formData, trash_day: e.target.value })}
                    className="input"
                  >
                    <option value="">Select day</option>
                    <option value="Monday">Monday</option>
                    <option value="Tuesday">Tuesday</option>
                    <option value="Wednesday">Wednesday</option>
                    <option value="Thursday">Thursday</option>
                    <option value="Friday">Friday</option>
                    <option value="Saturday">Saturday</option>
                    <option value="Sunday">Sunday</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trash Schedule Type
                  </label>
                  <select
                    value={formData.trash_schedule_type}
                    onChange={(e) => setFormData({ ...formData, trash_schedule_type: e.target.value })}
                    className="input"
                  >
                    <option value="">Select type</option>
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Bi-weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trash Schedule Details
                  </label>
                  <textarea
                    value={formData.trash_schedule_details}
                    onChange={(e) => setFormData({ ...formData, trash_schedule_details: e.target.value })}
                    className="input"
                    rows={2}
                    placeholder="Additional trash pickup details..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recycling Day
                  </label>
                  <select
                    value={formData.recycling_day}
                    onChange={(e) => setFormData({ ...formData, recycling_day: e.target.value })}
                    className="input"
                  >
                    <option value="">Select day</option>
                    <option value="Monday">Monday</option>
                    <option value="Tuesday">Tuesday</option>
                    <option value="Wednesday">Wednesday</option>
                    <option value="Thursday">Thursday</option>
                    <option value="Friday">Friday</option>
                    <option value="Saturday">Saturday</option>
                    <option value="Sunday">Sunday</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recycling Schedule Type
                  </label>
                  <select
                    value={formData.recycling_schedule_type}
                    onChange={(e) => setFormData({ ...formData, recycling_schedule_type: e.target.value })}
                    className="input"
                  >
                    <option value="">Select type</option>
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Bi-weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recycling Schedule Details
                  </label>
                  <textarea
                    value={formData.recycling_schedule_details}
                    onChange={(e) => setFormData({ ...formData, recycling_schedule_details: e.target.value })}
                    className="input"
                    rows={2}
                    placeholder="Additional recycling details..."
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recycling Notes
                  </label>
                  <textarea
                    value={formData.recycling_notes}
                    onChange={(e) => setFormData({ ...formData, recycling_notes: e.target.value })}
                    className="input"
                    rows={2}
                    placeholder="Special recycling instructions..."
                  />
                </div>
              </div>
            </div>

            {/* Utilities & Services */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">Utilities & Services</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Internet Provider
                  </label>
                  <input
                    type="text"
                    value={formData.internet_provider}
                    onChange={(e) => setFormData({ ...formData, internet_provider: e.target.value })}
                    className="input"
                    placeholder="Comcast"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Internet Account #
                  </label>
                  <input
                    type="text"
                    value={formData.internet_account}
                    onChange={(e) => setFormData({ ...formData, internet_account: e.target.value })}
                    className="input"
                    placeholder="Account number"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Internet Contact
                  </label>
                  <input
                    type="text"
                    value={formData.internet_contact}
                    onChange={(e) => setFormData({ ...formData, internet_contact: e.target.value })}
                    className="input"
                    placeholder="800-123-4567"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Electric Provider
                  </label>
                  <input
                    type="text"
                    value={formData.electric_provider}
                    onChange={(e) => setFormData({ ...formData, electric_provider: e.target.value })}
                    className="input"
                    placeholder="PG&E"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Electric Account #
                  </label>
                  <input
                    type="text"
                    value={formData.electric_account}
                    onChange={(e) => setFormData({ ...formData, electric_account: e.target.value })}
                    className="input"
                    placeholder="Account number"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Electric Contact
                  </label>
                  <input
                    type="text"
                    value={formData.electric_contact}
                    onChange={(e) => setFormData({ ...formData, electric_contact: e.target.value })}
                    className="input"
                    placeholder="800-123-4567"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Water Provider
                  </label>
                  <input
                    type="text"
                    value={formData.water_provider}
                    onChange={(e) => setFormData({ ...formData, water_provider: e.target.value })}
                    className="input"
                    placeholder="City Water"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Water Account #
                  </label>
                  <input
                    type="text"
                    value={formData.water_account}
                    onChange={(e) => setFormData({ ...formData, water_account: e.target.value })}
                    className="input"
                    placeholder="Account number"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Water Contact
                  </label>
                  <input
                    type="text"
                    value={formData.water_contact}
                    onChange={(e) => setFormData({ ...formData, water_contact: e.target.value })}
                    className="input"
                    placeholder="800-123-4567"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trash Provider
                  </label>
                  <input
                    type="text"
                    value={formData.trash_provider}
                    onChange={(e) => setFormData({ ...formData, trash_provider: e.target.value })}
                    className="input"
                    placeholder="Waste Management"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trash Account #
                  </label>
                  <input
                    type="text"
                    value={formData.trash_account}
                    onChange={(e) => setFormData({ ...formData, trash_account: e.target.value })}
                    className="input"
                    placeholder="Account number"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trash Contact
                  </label>
                  <input
                    type="text"
                    value={formData.trash_contact}
                    onChange={(e) => setFormData({ ...formData, trash_contact: e.target.value })}
                    className="input"
                    placeholder="800-123-4567"
                  />
                </div>
              </div>
            </div>

            {/* Check-in Times */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">Check-in Times</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Check-in Time
                  </label>
                  <input
                    type="time"
                    value={formData.checkin_time}
                    onChange={(e) => setFormData({ ...formData, checkin_time: e.target.value })}
                    className="input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Check-out Time
                  </label>
                  <input
                    type="time"
                    value={formData.checkout_time}
                    onChange={(e) => setFormData({ ...formData, checkout_time: e.target.value })}
                    className="input"
                  />
                </div>
              </div>
            </div>

            {/* Operations (Staff) Information */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">Operations (Staff) Information</h3>
              <p className="text-sm text-gray-600 mb-4">Information for cleaning staff, maintenance workers, and property managers.</p>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entry Instructions (for Staff)
                  </label>
                  <textarea
                    value={formData.entry_instructions}
                    onChange={(e) => setFormData({ ...formData, entry_instructions: e.target.value })}
                    className="input"
                    rows={3}
                    placeholder="How staff should enter the property (keypad code, lockbox location, etc.)..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cleaning Supplies Location
                  </label>
                  <input
                    type="text"
                    value={formData.cleaning_supplies_location}
                    onChange={(e) => setFormData({ ...formData, cleaning_supplies_location: e.target.value })}
                    className="input"
                    placeholder="Under kitchen sink, garage shelf, etc."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Special Instructions (for Staff)
                  </label>
                  <textarea
                    value={formData.special_instructions}
                    onChange={(e) => setFormData({ ...formData, special_instructions: e.target.value })}
                    className="input"
                    rows={3}
                    placeholder="Special notes about maintenance, quirks, or operational details..."
                  />
                </div>
              </div>
            </div>

            {/* Guest Portal Information */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">Guest Portal Information</h3>
              <p className="text-sm text-gray-600 mb-4">Information that will be shown to guests via the guest portal.</p>
              <div className="grid grid-cols-1 gap-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.guest_access_enabled}
                    onChange={(e) => setFormData({ ...formData, guest_access_enabled: e.target.checked })}
                    className="mr-2"
                  />
                  <label className="text-sm font-medium text-gray-700">
                    Enable Guest Access Portal
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Guest Rules (House Rules)
                  </label>
                  <textarea
                    value={formData.guest_rules}
                    onChange={(e) => setFormData({ ...formData, guest_rules: e.target.value })}
                    className="input"
                    rows={3}
                    placeholder="House rules for guests (no smoking, quiet hours, etc.)..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Guest Check-in Instructions
                  </label>
                  <textarea
                    value={formData.guest_checkin_instructions}
                    onChange={(e) => setFormData({ ...formData, guest_checkin_instructions: e.target.value })}
                    className="input"
                    rows={3}
                    placeholder="Instructions for guests on how to check in and access the property..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Guest Check-out Instructions
                  </label>
                  <textarea
                    value={formData.guest_checkout_instructions}
                    onChange={(e) => setFormData({ ...formData, guest_checkout_instructions: e.target.value })}
                    className="input"
                    rows={3}
                    placeholder="Instructions for guests on check-out procedures..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Guest WiFi Instructions
                  </label>
                  <textarea
                    value={formData.guest_wifi_instructions}
                    onChange={(e) => setFormData({ ...formData, guest_wifi_instructions: e.target.value })}
                    className="input"
                    rows={2}
                    placeholder="How guests can connect to WiFi (network name and password will be shown separately)..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Local Attractions
                  </label>
                  <textarea
                    value={formData.local_attractions}
                    onChange={(e) => setFormData({ ...formData, local_attractions: e.target.value })}
                    className="input"
                    rows={3}
                    placeholder="Nearby restaurants, activities, points of interest..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Emergency Contact
                  </label>
                  <input
                    type="text"
                    value={formData.emergency_contact}
                    onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
                    className="input"
                    placeholder="Emergency contact name and phone number"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Guest FAQ
                  </label>
                  <textarea
                    value={formData.guest_faq}
                    onChange={(e) => setFormData({ ...formData, guest_faq: e.target.value })}
                    className="input"
                    rows={4}
                    placeholder="Frequently asked questions and answers..."
                  />
                </div>
              </div>
            </div>

            {/* Additional Settings */}
            <div>
              <h3 className="text-md font-semibold text-gray-800 mb-4">Additional Settings</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    iCal URL
                  </label>
                  <input
                    type="url"
                    value={formData.ical_url}
                    onChange={(e) => setFormData({ ...formData, ical_url: e.target.value })}
                    className="input"
                    placeholder="https://..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Calendar Color
                  </label>
                  <input
                    type="color"
                    value={formData.color || '#3B82F6'}
                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                    className="input"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3 justify-end pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={() => setShowEditForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Property Images Section */}
            <div>
              <PropertyImageGallery propertyId={id!} />
            </div>

            {/* Share Property Section */}
            <div>
              <PropertyShareCard
                propertyId={id!}
                propertyName={property.name || 'Property'}
                guestAccessToken={property.guest_access_token || ''}
                guestAccessEnabled={property.guest_access_enabled || false}
              />
            </div>

            {/* Basic Info & Quick Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="space-y-6">
                <div className="card">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm font-medium text-gray-600">Type</dt>
                      <dd className="text-gray-900 capitalize">{property.property_type}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-600">Status</dt>
                      <dd>
                        <span className="badge badge-completed">{property.status || 'active'}</span>
                      </dd>
                    </div>
                    {property.description && (
                      <div>
                        <dt className="text-sm font-medium text-gray-600">Description</dt>
                        <dd className="text-gray-900">{property.description}</dd>
                      </div>
                    )}
                  </dl>
                </div>

                <div className="card">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
                  <div className="space-y-2">
                    <button
                      onClick={() => setActiveTab('calendar')}
                      className="w-full block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left"
                    >
                      📅 View Calendar
                    </button>
                    <Link
                      to={`/tasks?property=${property.id}`}
                      className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      ✓ View Tasks
                    </Link>
                    <Link
                      to={`/cleaning?property=${property.id}`}
                      className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      🧹 Cleaning History
                    </Link>
                  </div>
                </div>
              </div>

              {/* Location */}
              <div className="lg:col-span-2">
                <div className="card">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Location</h2>
                  <dl className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                      <dt className="text-sm font-medium text-gray-600">Address</dt>
                      <dd className="text-gray-900">{property.address}</dd>
                    </div>
                    {property.city && (
                      <div>
                        <dt className="text-sm font-medium text-gray-600">City</dt>
                        <dd className="text-gray-900">{property.city}</dd>
                      </div>
                    )}
                    {property.state && (
                      <div>
                        <dt className="text-sm font-medium text-gray-600">State</dt>
                        <dd className="text-gray-900">{property.state}</dd>
                      </div>
                    )}
                    {property.zip_code && (
                      <div>
                        <dt className="text-sm font-medium text-gray-600">ZIP Code</dt>
                        <dd className="text-gray-900">{property.zip_code}</dd>
                      </div>
                    )}
                    {property.country && (
                      <div>
                        <dt className="text-sm font-medium text-gray-600">Country</dt>
                        <dd className="text-gray-900">{property.country}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Calendar & Bookings Tab */}
        {activeTab === 'calendar' && (
          <div className="space-y-6">
            <div>
              <CalendarView propertyId={id!} />
            </div>
            <div>
              <CalendarManagement propertyId={id!} />
            </div>
          </div>
        )}

        {/* Details Tab */}
        {activeTab === 'details' && (
          <div className="space-y-6">
            {/* Property Rooms Section */}
            <div>
              <PropertyRoomManager propertyId={id!} />
            </div>

            {/* Property Features */}
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Features</h2>
              <dl className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {property.bedrooms && (
                  <div>
                    <dt className="text-sm font-medium text-gray-600">Bedrooms</dt>
                    <dd className="text-gray-900">{property.bedrooms}</dd>
                  </div>
                )}
                {property.bathrooms && (
                  <div>
                    <dt className="text-sm font-medium text-gray-600">Bathrooms</dt>
                    <dd className="text-gray-900">{property.bathrooms}</dd>
                  </div>
                )}
                {property.square_feet && (
                  <div>
                    <dt className="text-sm font-medium text-gray-600">Square Feet</dt>
                    <dd className="text-gray-900">{property.square_feet}</dd>
                  </div>
                )}
                {property.year_built && (
                  <div>
                    <dt className="text-sm font-medium text-gray-600">Year Built</dt>
                    <dd className="text-gray-900">{property.year_built}</dd>
                  </div>
                )}
                {property.total_beds && (
                  <div>
                    <dt className="text-sm font-medium text-gray-600">Total Beds</dt>
                    <dd className="text-gray-900">{property.total_beds}</dd>
                  </div>
                )}
                {property.bed_sizes && (
                  <div>
                    <dt className="text-sm font-medium text-gray-600">Bed Sizes</dt>
                    <dd className="text-gray-900">{property.bed_sizes}</dd>
                  </div>
                )}
                {property.number_of_showers && (
                  <div>
                    <dt className="text-sm font-medium text-gray-600">Showers</dt>
                    <dd className="text-gray-900">{property.number_of_showers}</dd>
                  </div>
                )}
                {property.number_of_tubs && (
                  <div>
                    <dt className="text-sm font-medium text-gray-600">Bathtubs</dt>
                    <dd className="text-gray-900">{property.number_of_tubs}</dd>
                  </div>
                )}
                {property.number_of_tvs && (
                  <div>
                    <dt className="text-sm font-medium text-gray-600">TVs</dt>
                    <dd className="text-gray-900">{property.number_of_tvs}</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* WiFi */}
            {(property.wifi_network || property.wifi_password) && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">WiFi & Network</h2>
                <dl className="grid grid-cols-2 gap-4">
                  {property.wifi_network && (
                    <div>
                      <dt className="text-sm font-medium text-gray-600">Network Name</dt>
                      <dd className="text-gray-900">{property.wifi_network}</dd>
                    </div>
                  )}
                  {property.wifi_password && (
                    <div>
                      <dt className="text-sm font-medium text-gray-600">Password</dt>
                      <dd className="text-gray-900 font-mono">{property.wifi_password}</dd>
                    </div>
                  )}
                </dl>
              </div>
            )}

            {/* Check-in Times */}
            {(property.checkin_time || property.checkout_time) && (
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Check-in Times</h2>
                <dl className="grid grid-cols-2 gap-4">
                  {property.checkin_time && (
                    <div>
                      <dt className="text-sm font-medium text-gray-600">Check-in Time</dt>
                      <dd className="text-gray-900">{property.checkin_time}</dd>
                    </div>
                  )}
                  {property.checkout_time && (
                    <div>
                      <dt className="text-sm font-medium text-gray-600">Check-out Time</dt>
                      <dd className="text-gray-900">{property.checkout_time}</dd>
                    </div>
                  )}
                </dl>
              </div>
            )}
          </div>
        )}

        {/* Guest Portal Tab */}
        {activeTab === 'guest' && (
          <div className="space-y-6">
            <div className="card bg-purple-50 border-purple-200">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">👤</span>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Guest Portal Information</h2>
                  <p className="text-sm text-gray-600">Information shown to guests via the guest portal</p>
                </div>
              </div>
              {property.guest_access_enabled ? (
                <div className="text-green-600 font-medium">✓ Guest Portal Enabled</div>
              ) : (
                <div className="text-gray-600">Guest Portal Disabled</div>
              )}
            </div>

            {/* House Rules */}
            {property.guest_rules && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">House Rules</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{property.guest_rules}</p>
              </div>
            )}

            {/* Check-in Instructions for Guests */}
            {property.guest_checkin_instructions && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Check-in Instructions</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{property.guest_checkin_instructions}</p>
              </div>
            )}

            {/* Check-out Instructions for Guests */}
            {property.guest_checkout_instructions && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Check-out Instructions</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{property.guest_checkout_instructions}</p>
              </div>
            )}

            {/* WiFi Instructions */}
            {property.guest_wifi_instructions && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">WiFi Instructions</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{property.guest_wifi_instructions}</p>
                {(property.wifi_network || property.wifi_password) && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    {property.wifi_network && (
                      <div className="text-sm">
                        <span className="font-medium">Network:</span> {property.wifi_network}
                      </div>
                    )}
                    {property.wifi_password && (
                      <div className="text-sm">
                        <span className="font-medium">Password:</span> <span className="font-mono">{property.wifi_password}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Local Attractions */}
            {property.local_attractions && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Local Attractions</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{property.local_attractions}</p>
              </div>
            )}

            {/* Emergency Contact */}
            {property.emergency_contact && (
              <div className="card bg-red-50 border-red-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Emergency Contact</h3>
                <p className="text-gray-900">{property.emergency_contact}</p>
              </div>
            )}

            {/* Guest FAQ */}
            {property.guest_faq && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Frequently Asked Questions</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{property.guest_faq}</p>
              </div>
            )}

            {/* Empty State */}
            {!property.guest_rules &&
             !property.guest_checkin_instructions &&
             !property.guest_checkout_instructions &&
             !property.guest_wifi_instructions &&
             !property.local_attractions &&
             !property.emergency_contact &&
             !property.guest_faq && (
              <div className="card text-center py-12">
                <div className="text-5xl mb-4">👤</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Guest Information</h3>
                <p className="text-gray-600 mb-6">
                  Add guest portal information to help your guests have a great stay.
                </p>
                <button
                  onClick={() => setShowEditForm(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Guest Information
                </button>
              </div>
            )}
          </div>
        )}

        {/* Operations Tab */}
        {activeTab === 'operations' && (
          <div className="space-y-6">
            <div className="card bg-orange-50 border-orange-200">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">🔧</span>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Operations Information</h2>
                  <p className="text-sm text-gray-600">Staff-facing information for cleaners, maintenance, and property managers</p>
                </div>
              </div>
            </div>

            {/* Entry Instructions for Staff */}
            {property.entry_instructions && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Entry Instructions (Staff)</h3>
                <p className="text-sm text-gray-600 mb-2">How staff should access the property</p>
                <p className="text-gray-900 whitespace-pre-wrap">{property.entry_instructions}</p>
              </div>
            )}

            {/* Cleaning Supplies */}
            {property.cleaning_supplies_location && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Cleaning Supplies Location</h3>
                <p className="text-gray-900">{property.cleaning_supplies_location}</p>
              </div>
            )}

            {/* Special Instructions */}
            {property.special_instructions && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Special Instructions (Staff)</h3>
                <p className="text-sm text-gray-600 mb-2">Maintenance notes, quirks, and operational details</p>
                <p className="text-gray-900 whitespace-pre-wrap">{property.special_instructions}</p>
              </div>
            )}

            {/* Trash & Recycling */}
            {(property.trash_day || property.recycling_day) && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Trash & Recycling Schedule</h3>
                <dl className="space-y-4">
                  {property.trash_day && (
                    <div className="border-b border-gray-200 pb-3">
                      <dt className="text-sm font-medium text-gray-600 mb-2">Trash Collection</dt>
                      <div className="space-y-1">
                        <dd className="text-gray-900">Day: {property.trash_day}</dd>
                        {property.trash_schedule_type && (
                          <dd className="text-gray-900">Frequency: {property.trash_schedule_type}</dd>
                        )}
                        {property.trash_schedule_details && (
                          <dd className="text-gray-700 text-sm">{property.trash_schedule_details}</dd>
                        )}
                      </div>
                    </div>
                  )}
                  {property.recycling_day && (
                    <div>
                      <dt className="text-sm font-medium text-gray-600 mb-2">Recycling Collection</dt>
                      <div className="space-y-1">
                        <dd className="text-gray-900">Day: {property.recycling_day}</dd>
                        {property.recycling_schedule_type && (
                          <dd className="text-gray-900">Frequency: {property.recycling_schedule_type}</dd>
                        )}
                        {property.recycling_schedule_details && (
                          <dd className="text-gray-700 text-sm">{property.recycling_schedule_details}</dd>
                        )}
                        {property.recycling_notes && (
                          <dd className="text-gray-700 text-sm mt-2">Notes: {property.recycling_notes}</dd>
                        )}
                      </div>
                    </div>
                  )}
                </dl>
              </div>
            )}

            {/* Utilities */}
            {(property.internet_provider || property.electric_provider || property.water_provider || property.trash_provider) && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Utilities & Services</h3>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {property.internet_provider && (
                    <div className="border-b border-gray-200 pb-3">
                      <dt className="text-sm font-medium text-gray-600">Internet</dt>
                      <dd className="text-gray-900">{property.internet_provider}</dd>
                      {property.internet_account && (
                        <dd className="text-sm text-gray-600">Account: {property.internet_account}</dd>
                      )}
                      {property.internet_contact && (
                        <dd className="text-sm text-gray-600">Contact: {property.internet_contact}</dd>
                      )}
                    </div>
                  )}
                  {property.electric_provider && (
                    <div className="border-b border-gray-200 pb-3">
                      <dt className="text-sm font-medium text-gray-600">Electric</dt>
                      <dd className="text-gray-900">{property.electric_provider}</dd>
                      {property.electric_account && (
                        <dd className="text-sm text-gray-600">Account: {property.electric_account}</dd>
                      )}
                      {property.electric_contact && (
                        <dd className="text-sm text-gray-600">Contact: {property.electric_contact}</dd>
                      )}
                    </div>
                  )}
                  {property.water_provider && (
                    <div className="border-b border-gray-200 pb-3">
                      <dt className="text-sm font-medium text-gray-600">Water</dt>
                      <dd className="text-gray-900">{property.water_provider}</dd>
                      {property.water_account && (
                        <dd className="text-sm text-gray-600">Account: {property.water_account}</dd>
                      )}
                      {property.water_contact && (
                        <dd className="text-sm text-gray-600">Contact: {property.water_contact}</dd>
                      )}
                    </div>
                  )}
                  {property.trash_provider && (
                    <div className="border-b border-gray-200 pb-3">
                      <dt className="text-sm font-medium text-gray-600">Trash Service</dt>
                      <dd className="text-gray-900">{property.trash_provider}</dd>
                      {property.trash_account && (
                        <dd className="text-sm text-gray-600">Account: {property.trash_account}</dd>
                      )}
                      {property.trash_contact && (
                        <dd className="text-sm text-gray-600">Contact: {property.trash_contact}</dd>
                      )}
                    </div>
                  )}
                </dl>
              </div>
            )}

            {/* Empty State */}
            {!property.entry_instructions &&
             !property.cleaning_supplies_location &&
             !property.special_instructions &&
             !property.trash_day &&
             !property.recycling_day &&
             !property.internet_provider &&
             !property.electric_provider &&
             !property.water_provider &&
             !property.trash_provider && (
              <div className="card text-center py-12">
                <div className="text-5xl mb-4">🔧</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Operations Information</h3>
                <p className="text-gray-600 mb-6">
                  Add operational details to help staff manage this property effectively.
                </p>
                <button
                  onClick={() => setShowEditForm(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Operations Information
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Guest Preview Modal */}
      <GuestPreviewModal
        property={property}
        isOpen={showGuestPreview}
        onClose={() => setShowGuestPreview(false)}
      />
    </div>
  );
}
