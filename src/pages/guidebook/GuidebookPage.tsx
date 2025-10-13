import { useEffect, useState } from 'react';
import { guidebookApi, propertiesApi } from '../../services/api';

interface Guidebook {
  id: string;
  property_id: string;
  welcome_message?: string;
  checkin_time: string;
  checkout_time: string;
  checkin_instructions?: string;
  checkout_instructions?: string;
  wifi_network?: string;
  wifi_password?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  host_phone?: string;
  host_email?: string;
  parking_info?: string;
  parking_instructions?: string;
  house_rules?: string;
  quiet_hours?: string;
  max_guests?: number;
  smoking_allowed: boolean;
  pets_allowed: boolean;
  parties_allowed: boolean;
  is_published: boolean;
}

export function GuidebookPage() {
  const [properties, setProperties] = useState<any[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<string>('');
  const [guidebook, setGuidebook] = useState<Guidebook | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    welcome_message: '',
    checkin_time: '3:00 PM',
    checkout_time: '11:00 AM',
    checkin_instructions: '',
    checkout_instructions: '',
    wifi_network: '',
    wifi_password: '',
    emergency_contact: '',
    emergency_phone: '',
    host_phone: '',
    host_email: '',
    parking_info: '',
    parking_instructions: '',
    house_rules: '',
    quiet_hours: '',
    max_guests: '',
    smoking_allowed: false,
    pets_allowed: false,
    parties_allowed: false,
    is_published: false,
  });

  useEffect(() => {
    loadProperties();
  }, []);

  useEffect(() => {
    if (selectedProperty) {
      loadGuidebook();
    }
  }, [selectedProperty]);

  const loadProperties = async () => {
    try {
      const data = await propertiesApi.list();
      setProperties(data.properties || []);
      if (data.properties?.length > 0) {
        setSelectedProperty(data.properties[0].id);
      }
    } catch (error) {
      console.error('Failed to load properties:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadGuidebook = async () => {
    if (!selectedProperty) return;

    try {
      setLoading(true);
      const response = await guidebookApi.get(selectedProperty);
      if (response.guidebook) {
        setGuidebook(response.guidebook);
        setFormData({
          welcome_message: response.guidebook.welcome_message || '',
          checkin_time: response.guidebook.checkin_time || '3:00 PM',
          checkout_time: response.guidebook.checkout_time || '11:00 AM',
          checkin_instructions: response.guidebook.checkin_instructions || '',
          checkout_instructions: response.guidebook.checkout_instructions || '',
          wifi_network: response.guidebook.wifi_network || '',
          wifi_password: response.guidebook.wifi_password || '',
          emergency_contact: response.guidebook.emergency_contact || '',
          emergency_phone: response.guidebook.emergency_phone || '',
          host_phone: response.guidebook.host_phone || '',
          host_email: response.guidebook.host_email || '',
          parking_info: response.guidebook.parking_info || '',
          parking_instructions: response.guidebook.parking_instructions || '',
          house_rules: response.guidebook.house_rules || '',
          quiet_hours: response.guidebook.quiet_hours || '',
          max_guests: response.guidebook.max_guests?.toString() || '',
          smoking_allowed: !!response.guidebook.smoking_allowed,
          pets_allowed: !!response.guidebook.pets_allowed,
          parties_allowed: !!response.guidebook.parties_allowed,
          is_published: !!response.guidebook.is_published,
        });
      } else {
        setGuidebook(null);
        // Reset to defaults
        setFormData({
          welcome_message: '',
          checkin_time: '3:00 PM',
          checkout_time: '11:00 AM',
          checkin_instructions: '',
          checkout_instructions: '',
          wifi_network: '',
          wifi_password: '',
          emergency_contact: '',
          emergency_phone: '',
          host_phone: '',
          host_email: '',
          parking_info: '',
          parking_instructions: '',
          house_rules: '',
          quiet_hours: '',
          max_guests: '',
          smoking_allowed: false,
          pets_allowed: false,
          parties_allowed: false,
          is_published: false,
        });
      }
    } catch (error) {
      console.error('Failed to load guidebook:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProperty) return;

    try {
      const payload = {
        ...formData,
        max_guests: formData.max_guests ? parseInt(formData.max_guests) : null,
      };

      if (guidebook) {
        await guidebookApi.update(selectedProperty, payload);
      } else {
        await guidebookApi.create(selectedProperty, payload);
      }

      setEditing(false);
      loadGuidebook();
    } catch (error: any) {
      alert(error.message || 'Failed to save guidebook');
    }
  };

  const handleDelete = async () => {
    if (!selectedProperty || !guidebook) return;

    const propertyName = properties.find(p => p.id === selectedProperty)?.name || 'this property';
    if (!confirm(`Are you sure you want to delete the guidebook for ${propertyName}?`)) {
      return;
    }

    try {
      await guidebookApi.delete(selectedProperty);
      loadGuidebook();
    } catch (error: any) {
      alert(error.message || 'Failed to delete guidebook');
    }
  };

  if (loading && !selectedProperty) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (properties.length === 0) {
    return (
      <div className="card text-center py-12">
        <div className="text-5xl mb-4">🏠</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No properties found</h3>
        <p className="text-gray-600">Create a property first to add a guidebook</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Property Guidebook</h1>
        {guidebook && !editing && (
          <div className="flex gap-3">
            <button
              onClick={() => setEditing(true)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Edit Guidebook
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      <div className="card mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Property
        </label>
        <select
          value={selectedProperty}
          onChange={(e) => setSelectedProperty(e.target.value)}
          className="input max-w-md"
        >
          {properties.map((property) => (
            <option key={property.id} value={property.id}>
              {property.name || property.address}
            </option>
          ))}
        </select>
      </div>

      {guidebook && !editing ? (
        // View Mode
        <div className="card">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Guidebook Details</h2>
            <span className={`badge ${guidebook.is_published ? 'badge-completed' : 'badge-pending'}`}>
              {guidebook.is_published ? 'Published' : 'Draft'}
            </span>
          </div>

          <div className="space-y-6">
            {formData.welcome_message && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Welcome Message</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{formData.welcome_message}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Check-in Time</h3>
                <p className="text-gray-900">{formData.checkin_time}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Check-out Time</h3>
                <p className="text-gray-900">{formData.checkout_time}</p>
              </div>
            </div>

            {formData.checkin_instructions && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Check-in Instructions</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{formData.checkin_instructions}</p>
              </div>
            )}

            {formData.checkout_instructions && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Check-out Instructions</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{formData.checkout_instructions}</p>
              </div>
            )}

            {(formData.wifi_network || formData.wifi_password) && (
              <div className="grid grid-cols-2 gap-6">
                {formData.wifi_network && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">WiFi Network</h3>
                    <p className="text-gray-900">{formData.wifi_network}</p>
                  </div>
                )}
                {formData.wifi_password && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">WiFi Password</h3>
                    <p className="text-gray-900">{formData.wifi_password}</p>
                  </div>
                )}
              </div>
            )}

            {formData.house_rules && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">House Rules</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{formData.house_rules}</p>
              </div>
            )}

            {formData.parking_info && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Parking Information</h3>
                <p className="text-gray-900 whitespace-pre-wrap">{formData.parking_info}</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        // Create/Edit Form
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            {guidebook ? 'Edit Guidebook' : 'Create Guidebook'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Welcome Message
              </label>
              <textarea
                value={formData.welcome_message}
                onChange={(e) => setFormData({ ...formData, welcome_message: e.target.value })}
                className="input"
                rows={4}
                placeholder="Welcome your guests..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Check-in Time *
                </label>
                <input
                  type="text"
                  value={formData.checkin_time}
                  onChange={(e) => setFormData({ ...formData, checkin_time: e.target.value })}
                  className="input"
                  placeholder="3:00 PM"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Check-out Time *
                </label>
                <input
                  type="text"
                  value={formData.checkout_time}
                  onChange={(e) => setFormData({ ...formData, checkout_time: e.target.value })}
                  className="input"
                  placeholder="11:00 AM"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Check-in Instructions
              </label>
              <textarea
                value={formData.checkin_instructions}
                onChange={(e) => setFormData({ ...formData, checkin_instructions: e.target.value })}
                className="input"
                rows={3}
                placeholder="How to check in..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Check-out Instructions
              </label>
              <textarea
                value={formData.checkout_instructions}
                onChange={(e) => setFormData({ ...formData, checkout_instructions: e.target.value })}
                className="input"
                rows={3}
                placeholder="How to check out..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  WiFi Network
                </label>
                <input
                  type="text"
                  value={formData.wifi_network}
                  onChange={(e) => setFormData({ ...formData, wifi_network: e.target.value })}
                  className="input"
                  placeholder="Network name"
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
                  placeholder="Password"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Emergency Contact
                </label>
                <input
                  type="text"
                  value={formData.emergency_contact}
                  onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
                  className="input"
                  placeholder="Contact name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Emergency Phone
                </label>
                <input
                  type="tel"
                  value={formData.emergency_phone}
                  onChange={(e) => setFormData({ ...formData, emergency_phone: e.target.value })}
                  className="input"
                  placeholder="Phone number"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Host Phone
                </label>
                <input
                  type="tel"
                  value={formData.host_phone}
                  onChange={(e) => setFormData({ ...formData, host_phone: e.target.value })}
                  className="input"
                  placeholder="Host phone"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Host Email
                </label>
                <input
                  type="email"
                  value={formData.host_email}
                  onChange={(e) => setFormData({ ...formData, host_email: e.target.value })}
                  className="input"
                  placeholder="host@example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Parking Information
              </label>
              <textarea
                value={formData.parking_info}
                onChange={(e) => setFormData({ ...formData, parking_info: e.target.value })}
                className="input"
                rows={2}
                placeholder="Parking details..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                House Rules
              </label>
              <textarea
                value={formData.house_rules}
                onChange={(e) => setFormData({ ...formData, house_rules: e.target.value })}
                className="input"
                rows={4}
                placeholder="House rules..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quiet Hours
                </label>
                <input
                  type="text"
                  value={formData.quiet_hours}
                  onChange={(e) => setFormData({ ...formData, quiet_hours: e.target.value })}
                  className="input"
                  placeholder="10 PM - 8 AM"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Guests
                </label>
                <input
                  type="number"
                  value={formData.max_guests}
                  onChange={(e) => setFormData({ ...formData, max_guests: e.target.value })}
                  className="input"
                  min="1"
                  placeholder="4"
                />
              </div>
            </div>

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.smoking_allowed}
                  onChange={(e) => setFormData({ ...formData, smoking_allowed: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Smoking allowed</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.pets_allowed}
                  onChange={(e) => setFormData({ ...formData, pets_allowed: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Pets allowed</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.parties_allowed}
                  onChange={(e) => setFormData({ ...formData, parties_allowed: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Parties/events allowed</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_published}
                  onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Publish guidebook</span>
              </label>
            </div>

            <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
              {guidebook && (
                <button
                  type="button"
                  onClick={() => setEditing(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                {guidebook ? 'Update Guidebook' : 'Create Guidebook'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
