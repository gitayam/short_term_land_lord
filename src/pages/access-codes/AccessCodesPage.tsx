import { useEffect, useState } from 'react';
import { accessCodesApi, propertiesApi } from '../../services/api';

interface AccessCode {
  id: string;
  access_code: string;
  guest_name: string;
  guest_email?: string;
  property_id: string;
  property_name: string;
  property_address: string;
  valid_from: string;
  valid_until: string;
  access_count: number;
  last_accessed?: string;
  is_active: boolean;
  created_at: string;
}

export function AccessCodesPage() {
  const [codes, setCodes] = useState<AccessCode[]>([]);
  const [properties, setProperties] = useState<any[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [propertyFilter, setPropertyFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    property_id: '',
    guest_name: '',
    guest_email: '',
    guest_phone: '',
    valid_from: '',
    valid_until: '',
    notes: '',
  });

  useEffect(() => {
    loadCodes();
    loadProperties();
  }, [filter, propertyFilter]);

  const loadCodes = async () => {
    try {
      const filters: any = {};
      if (filter !== 'all') {
        filters.status = filter;
      }
      if (propertyFilter !== 'all') {
        filters.property_id = propertyFilter;
      }

      const data = await accessCodesApi.list(filters);
      setCodes(data.codes || []);
    } catch (error) {
      console.error('Failed to load access codes:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadProperties = async () => {
    try {
      const data = await propertiesApi.list();
      setProperties(data.properties || []);
    } catch (error) {
      console.error('Failed to load properties:', error);
    }
  };

  const handleCreateCode = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await accessCodesApi.create(formData);
      alert(`Access code created: ${response.code.access_code}\n\nPortal URL:\n${response.portal_url}`);
      setShowCreateForm(false);
      setFormData({
        property_id: '',
        guest_name: '',
        guest_email: '',
        guest_phone: '',
        valid_from: '',
        valid_until: '',
        notes: '',
      });
      loadCodes();
    } catch (error: any) {
      alert(error.message || 'Failed to create access code');
    }
  };

  const getStatusInfo = (code: AccessCode) => {
    const now = new Date().toISOString().split('T')[0];

    if (!code.is_active) {
      return { label: 'Disabled', className: 'badge-failed' };
    }
    if (now < code.valid_from) {
      return { label: 'Future', className: 'badge-pending' };
    }
    if (now > code.valid_until) {
      return { label: 'Expired', className: 'badge-failed' };
    }
    return { label: 'Active', className: 'badge-completed' };
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  const getPortalUrl = (accessCode: string) => {
    return `${window.location.origin}/guest/${accessCode}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Guest Access Codes</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showCreateForm ? 'Cancel' : '+ Create Access Code'}
        </button>
      </div>

      {showCreateForm && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Create Access Code</h2>
          <form onSubmit={handleCreateCode} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Property *
              </label>
              <select
                value={formData.property_id}
                onChange={(e) => setFormData({ ...formData, property_id: e.target.value })}
                className="input"
                required
              >
                <option value="">Select a property</option>
                {properties.map((prop) => (
                  <option key={prop.id} value={prop.id}>
                    {prop.name || prop.address}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Guest Name *
              </label>
              <input
                type="text"
                value={formData.guest_name}
                onChange={(e) => setFormData({ ...formData, guest_name: e.target.value })}
                className="input"
                placeholder="John Doe"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Guest Email
                </label>
                <input
                  type="email"
                  value={formData.guest_email}
                  onChange={(e) => setFormData({ ...formData, guest_email: e.target.value })}
                  className="input"
                  placeholder="guest@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Guest Phone
                </label>
                <input
                  type="tel"
                  value={formData.guest_phone}
                  onChange={(e) => setFormData({ ...formData, guest_phone: e.target.value })}
                  className="input"
                  placeholder="+1 (555) 123-4567"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valid From *
                </label>
                <input
                  type="date"
                  value={formData.valid_from}
                  onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valid Until *
                </label>
                <input
                  type="date"
                  value={formData.valid_until}
                  onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                  className="input"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes (optional)
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="input"
                rows={2}
                placeholder="Internal notes..."
              />
            </div>

            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Access Code
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-4">
        <div className="flex gap-2">
          {['all', 'active', 'expired', 'future', 'disabled'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        {properties.length > 1 && (
          <select
            value={propertyFilter}
            onChange={(e) => setPropertyFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="all">All Properties</option>
            {properties.map((prop) => (
              <option key={prop.id} value={prop.id}>
                {prop.name || prop.address}
              </option>
            ))}
          </select>
        )}
      </div>

      {codes.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">🔑</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No access codes</h3>
          <p className="text-gray-600 mb-6">
            {filter === 'all'
              ? 'Create your first guest access code'
              : `No ${filter} access codes`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {codes.map((code) => {
            const status = getStatusInfo(code);
            return (
              <div key={code.id} className="card hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{code.guest_name}</h3>
                      <span className={`badge ${status.className}`}>{status.label}</span>
                    </div>
                    <p className="text-sm text-gray-600">{code.property_name}</p>
                    <p className="text-xs text-gray-500">{code.property_address}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-mono font-bold text-blue-600 mb-1">
                      {code.access_code}
                    </div>
                    <button
                      onClick={() => copyToClipboard(code.access_code)}
                      className="text-xs text-blue-600 hover:text-blue-700"
                    >
                      Copy Code
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
                  <div>
                    <span className="font-medium">Valid From:</span>{' '}
                    {new Date(code.valid_from).toLocaleDateString()}
                  </div>
                  <div>
                    <span className="font-medium">Valid Until:</span>{' '}
                    {new Date(code.valid_until).toLocaleDateString()}
                  </div>
                  {code.guest_email && (
                    <div>
                      <span className="font-medium">Email:</span> {code.guest_email}
                    </div>
                  )}
                  <div>
                    <span className="font-medium">Access Count:</span> {code.access_count}
                  </div>
                  {code.last_accessed && (
                    <div className="col-span-2">
                      <span className="font-medium">Last Accessed:</span>{' '}
                      {new Date(code.last_accessed).toLocaleString()}
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t border-gray-200 flex gap-2">
                  <button
                    onClick={() => copyToClipboard(getPortalUrl(code.access_code))}
                    className="btn-secondary text-sm flex-1"
                  >
                    Copy Portal URL
                  </button>
                  <button
                    onClick={() => window.open(getPortalUrl(code.access_code), '_blank')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                  >
                    Open Portal
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
