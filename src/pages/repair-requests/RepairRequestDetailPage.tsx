/**
 * Repair Request Detail Page
 * View and manage individual repair request
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { repairRequestsApi, RepairRequest } from '../../services/repairRequestsApi';
import { workersApi, Worker } from '../../services/workersApi';

export function RepairRequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [request, setRequest] = useState<RepairRequest | null>(null);
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewStatus, setReviewStatus] = useState<'approved' | 'rejected'>('approved');
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewing, setReviewing] = useState(false);

  const [showConvertModal, setShowConvertModal] = useState(false);
  const [assignedToId, setAssignedToId] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [priority, setPriority] = useState('');
  const [converting, setConverting] = useState(false);

  useEffect(() => {
    if (id) {
      loadRequest();
      loadWorkers();
    }
  }, [id]);

  const loadRequest = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await repairRequestsApi.getRepairRequest(id!);
      setRequest(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadWorkers = async () => {
    try {
      const data = await workersApi.getWorkers();
      setWorkers(data);
    } catch (err) {
      console.error('Failed to load workers:', err);
    }
  };

  const handleReview = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setReviewing(true);
      setError(null);
      await repairRequestsApi.reviewRepairRequest(id!, {
        status: reviewStatus,
        review_notes: reviewNotes,
      });
      setShowReviewModal(false);
      setReviewNotes('');
      await loadRequest();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setReviewing(false);
    }
  };

  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setConverting(true);
      setError(null);
      const task = await repairRequestsApi.convertToTask(id!, {
        assigned_to_id: assignedToId || undefined,
        due_date: dueDate || undefined,
        priority: priority || undefined,
      });
      setShowConvertModal(false);
      // Navigate to the created task
      navigate(`/tasks`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setConverting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this repair request?')) return;

    try {
      setError(null);
      await repairRequestsApi.deleteRepairRequest(id!);
      navigate('/repair-requests');
    } catch (err: any) {
      setError(err.message);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'urgent':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'converted':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-2 text-gray-600">Loading repair request...</p>
        </div>
      </div>
    );
  }

  if (!request) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Repair request not found
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/repair-requests')}
          className="text-blue-500 hover:text-blue-700 mb-2"
        >
          ← Back to Repair Requests
        </button>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold mb-2">{request.title}</h1>
            <p className="text-gray-600">
              {request.property_name} - {request.property_address}
            </p>
          </div>
          <div className="flex gap-2">
            {request.status === 'pending' && (
              <>
                <button
                  onClick={() => setShowReviewModal(true)}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Review
                </button>
                <button
                  onClick={() => setShowConvertModal(true)}
                  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  Convert to Task
                </button>
              </>
            )}
            {request.status === 'approved' && (
              <button
                onClick={() => setShowConvertModal(true)}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              >
                Convert to Task
              </button>
            )}
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Delete
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Status Badges */}
      <div className="flex gap-3 mb-6">
        <span className={`px-4 py-2 text-sm font-bold rounded-lg border-2 ${getSeverityColor(request.severity)}`}>
          {request.severity.toUpperCase()} PRIORITY
        </span>
        <span className={`px-4 py-2 text-sm font-bold rounded-lg border-2 ${getStatusColor(request.status)}`}>
          {request.status.toUpperCase()}
        </span>
      </div>

      {/* Request Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-3">Description</h2>
            <p className="text-gray-700 whitespace-pre-wrap">{request.description}</p>
          </div>

          {/* Images */}
          {request.images && request.images.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold mb-3">Photos</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {request.images.map((image, idx) => (
                  <img
                    key={idx}
                    src={image.image_url}
                    alt={`Issue photo ${idx + 1}`}
                    className="w-full h-48 object-cover rounded border hover:scale-105 transition-transform cursor-pointer"
                    onClick={() => window.open(image.image_url, '_blank')}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Review Information */}
          {request.status !== 'pending' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold mb-3">Review</h2>
              <div className="space-y-2">
                <p>
                  <span className="font-medium">Reviewed by:</span>{' '}
                  {request.reviewed_by_name || 'Unknown'}
                </p>
                {request.reviewed_at && (
                  <p>
                    <span className="font-medium">Reviewed at:</span>{' '}
                    {new Date(request.reviewed_at).toLocaleString()}
                  </p>
                )}
                {request.review_notes && (
                  <div className="mt-3 p-3 bg-gray-50 rounded border">
                    <p className="text-sm font-medium text-gray-700 mb-1">Notes:</p>
                    <p className="text-gray-700">{request.review_notes}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Request Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-bold mb-4">Request Information</h2>
            <div className="space-y-3 text-sm">
              {request.location && (
                <div>
                  <p className="text-gray-600">Location</p>
                  <p className="font-medium">📍 {request.location}</p>
                </div>
              )}
              <div>
                <p className="text-gray-600">Reported By</p>
                <p className="font-medium">{request.reported_by_name}</p>
                <p className="text-gray-500 text-xs">{request.reported_by_email}</p>
              </div>
              <div>
                <p className="text-gray-600">Created</p>
                <p className="font-medium">{new Date(request.created_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-gray-600">Last Updated</p>
                <p className="font-medium">{new Date(request.updated_at).toLocaleString()}</p>
              </div>
              {request.converted_task_id && (
                <div>
                  <p className="text-gray-600">Converted to Task</p>
                  <button
                    onClick={() => navigate(`/tasks`)}
                    className="text-blue-500 hover:text-blue-700 font-medium"
                  >
                    View Task →
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Review Modal */}
      {showReviewModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Review Request</h2>
              <button
                onClick={() => setShowReviewModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleReview} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Decision
                </label>
                <select
                  value={reviewStatus}
                  onChange={(e) => setReviewStatus(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  <option value="approved">Approve</option>
                  <option value="rejected">Reject</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                  placeholder="Add any notes about your decision..."
                />
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowReviewModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                  disabled={reviewing}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                  disabled={reviewing}
                >
                  {reviewing ? 'Submitting...' : 'Submit Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Convert to Task Modal */}
      {showConvertModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Convert to Task</h2>
              <button
                onClick={() => setShowConvertModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleConvert} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assign to Worker (optional)
                </label>
                <select
                  value={assignedToId}
                  onChange={(e) => setAssignedToId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  <option value="">Unassigned</option>
                  {workers.map((worker) => (
                    <option key={worker.id} value={worker.id}>
                      {worker.first_name} {worker.last_name} ({worker.role})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Due Date (optional)
                </label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority (optional)
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  <option value="">Use severity mapping</option>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>

              <div className="bg-blue-50 border border-blue-200 p-3 rounded text-sm">
                <p className="text-blue-800">
                  This will create a new task and mark this repair request as converted.
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowConvertModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                  disabled={converting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
                  disabled={converting}
                >
                  {converting ? 'Converting...' : 'Convert to Task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
