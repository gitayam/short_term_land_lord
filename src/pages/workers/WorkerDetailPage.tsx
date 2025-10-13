/**
 * Worker Detail Page
 * View and manage individual worker details and assignments
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { workersApi, Worker, PropertyAssignment } from '../../services/workersApi';
import { propertiesApi } from '../../services/api';

interface Property {
  id: string;
  name: string;
  address: string;
}

export function WorkerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [worker, setWorker] = useState<Worker | null>(null);
  const [assignments, setAssignments] = useState<PropertyAssignment[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedPropertyId, setSelectedPropertyId] = useState('');
  const [assignNotes, setAssignNotes] = useState('');

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    role: 'service_staff' as 'service_staff' | 'property_manager',
    is_active: 1,
  });

  useEffect(() => {
    if (id) {
      loadWorkerData();
      loadProperties();
    }
  }, [id]);

  const loadWorkerData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await workersApi.getWorker(id!);
      setWorker(data.worker);
      setAssignments(data.assignments);
      setFormData({
        first_name: data.worker.first_name || '',
        last_name: data.worker.last_name || '',
        phone: data.worker.phone || '',
        role: data.worker.role as any,
        is_active: data.worker.is_active,
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadProperties = async () => {
    try {
      const response = await propertiesApi.list();
      setProperties(response.properties || []);
    } catch (err) {
      console.error('Failed to load properties:', err);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      await workersApi.updateWorker(id!, formData);
      setIsEditing(false);
      await loadWorkerData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async () => {
    if (!confirm('Are you sure you want to deactivate this worker?')) return;

    try {
      setError(null);
      await workersApi.deactivateWorker(id!);
      await loadWorkerData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAssignProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      await workersApi.assignProperty(selectedPropertyId, id!, assignNotes);
      setShowAssignModal(false);
      setSelectedPropertyId('');
      setAssignNotes('');
      await loadWorkerData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleRemoveAssignment = async (assignmentId: string) => {
    if (!confirm('Are you sure you want to remove this property assignment?')) return;

    try {
      setError(null);
      await workersApi.removePropertyAssignment(assignmentId);
      await loadWorkerData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-2 text-gray-600">Loading worker...</p>
        </div>
      </div>
    );
  }

  if (!worker) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Worker not found
        </div>
      </div>
    );
  }

  const availableProperties = properties.filter(
    (p) => !assignments.some((a) => a.property_id === p.id)
  );

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <button
            onClick={() => navigate('/workers')}
            className="text-blue-500 hover:text-blue-700 mb-2"
          >
            ← Back to Workers
          </button>
          <h1 className="text-3xl font-bold">
            {worker.first_name} {worker.last_name}
          </h1>
          <p className="text-gray-600">{worker.email}</p>
        </div>
        <div className="flex gap-2">
          {!isEditing && (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Edit
              </button>
              {worker.is_active === 1 && (
                <button
                  onClick={handleDeactivate}
                  className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                >
                  Deactivate
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Worker Info */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">Worker Information</h2>

        {isEditing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) =>
                    setFormData({ ...formData, first_name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) =>
                    setFormData({ ...formData, last_name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                value={formData.role}
                onChange={(e) =>
                  setFormData({ ...formData, role: e.target.value as any })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded"
              >
                <option value="service_staff">Service Staff</option>
                <option value="property_manager">Property Manager</option>
              </select>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Phone</p>
              <p className="font-medium">{worker.phone || 'Not provided'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Role</p>
              <p className="font-medium capitalize">{worker.role.replace('_', ' ')}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className="font-medium">
                {worker.is_active ? (
                  <span className="text-green-600">Active</span>
                ) : (
                  <span className="text-gray-600">Inactive</span>
                )}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Last Login</p>
              <p className="font-medium">
                {worker.last_login
                  ? new Date(worker.last_login).toLocaleString()
                  : 'Never'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Property Assignments */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Property Assignments</h2>
          <button
            onClick={() => setShowAssignModal(true)}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            + Assign Property
          </button>
        </div>

        {assignments.length === 0 ? (
          <p className="text-gray-600">No properties assigned yet</p>
        ) : (
          <div className="space-y-3">
            {assignments.map((assignment) => (
              <div
                key={assignment.id}
                className="flex justify-between items-center border border-gray-200 rounded p-4"
              >
                <div>
                  <h3 className="font-medium">{assignment.property_name}</h3>
                  <p className="text-sm text-gray-600">{assignment.property_address}</p>
                  {assignment.notes && (
                    <p className="text-sm text-gray-500 mt-1">{assignment.notes}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    Assigned {new Date(assignment.assigned_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => handleRemoveAssignment(assignment.id)}
                  className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Assign Property Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Assign Property</h2>
              <button
                onClick={() => setShowAssignModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAssignProperty} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Property
                </label>
                <select
                  value={selectedPropertyId}
                  onChange={(e) => setSelectedPropertyId(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  <option value="">Select a property...</option>
                  {availableProperties.map((property) => (
                    <option key={property.id} value={property.id}>
                      {property.name} - {property.address}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={assignNotes}
                  onChange={(e) => setAssignNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                  placeholder="Any special instructions or notes..."
                />
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowAssignModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  Assign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
