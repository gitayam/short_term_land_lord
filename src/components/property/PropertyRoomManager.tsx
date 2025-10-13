/**
 * Property Room Manager Component
 * Manage property rooms - bedrooms, bathrooms, kitchen, living areas
 */

import { useState, useEffect } from 'react';
import { propertyRoomsApi, PropertyRoom } from '../../services/propertyRoomsApi';

interface PropertyRoomManagerProps {
  propertyId: string;
}

const ROOM_TYPES = [
  { value: 'bedroom', label: 'Bedroom', icon: '🛏️' },
  { value: 'bathroom', label: 'Bathroom', icon: '🚿' },
  { value: 'kitchen', label: 'Kitchen', icon: '🍳' },
  { value: 'living_room', label: 'Living Room', icon: '🛋️' },
  { value: 'other', label: 'Other', icon: '📦' },
];

const BED_TYPES = ['Twin', 'Full', 'Queen', 'King', 'California King', 'Bunk Bed', 'Sofa Bed'];

export function PropertyRoomManager({ propertyId }: PropertyRoomManagerProps) {
  const [rooms, setRooms] = useState<PropertyRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingRoom, setEditingRoom] = useState<string | null>(null);

  // New room form state
  const [newRoom, setNewRoom] = useState({
    room_type: 'bedroom' as const,
    name: '',
    bed_type: '',
    bed_count: 1,
    has_ensuite: 0,
    amenities: '',
    notes: '',
  });

  // Edit room form state
  const [editForm, setEditForm] = useState({
    room_type: 'bedroom' as const,
    name: '',
    bed_type: '',
    bed_count: 1,
    has_ensuite: 0,
    amenities: '',
    notes: '',
  });

  useEffect(() => {
    loadRooms();
  }, [propertyId]);

  const loadRooms = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await propertyRoomsApi.getRooms(propertyId);
      setRooms(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      await propertyRoomsApi.createRoom(propertyId, newRoom);
      setNewRoom({
        room_type: 'bedroom',
        name: '',
        bed_type: '',
        bed_count: 1,
        has_ensuite: 0,
        amenities: '',
        notes: '',
      });
      setShowAddForm(false);
      await loadRooms();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleEditRoom = (room: PropertyRoom) => {
    setEditingRoom(room.id);
    setEditForm({
      room_type: room.room_type,
      name: room.name || '',
      bed_type: room.bed_type || '',
      bed_count: room.bed_count || 1,
      has_ensuite: room.has_ensuite || 0,
      amenities: room.amenities || '',
      notes: room.notes || '',
    });
  };

  const handleUpdateRoom = async (roomId: string) => {
    try {
      setError(null);
      await propertyRoomsApi.updateRoom(propertyId, roomId, editForm);
      setEditingRoom(null);
      await loadRooms();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteRoom = async (roomId: string) => {
    if (!confirm('Are you sure you want to delete this room?')) return;

    try {
      setError(null);
      await propertyRoomsApi.deleteRoom(propertyId, roomId);
      await loadRooms();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const getRoomIcon = (roomType: string) => {
    return ROOM_TYPES.find((t) => t.value === roomType)?.icon || '📦';
  };

  const getRoomLabel = (roomType: string) => {
    return ROOM_TYPES.find((t) => t.value === roomType)?.label || 'Other';
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <p className="mt-2 text-gray-600">Loading rooms...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Property Rooms</h2>
          <p className="text-sm text-gray-600 mt-1">
            Define bedrooms, bathrooms, and other spaces ({rooms.length} rooms)
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          {showAddForm ? 'Cancel' : '+ Add Room'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Add Room Form */}
      {showAddForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-lg mb-4">Add New Room</h3>
          <form onSubmit={handleAddRoom} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Room Type *
                </label>
                <select
                  value={newRoom.room_type}
                  onChange={(e) => setNewRoom({ ...newRoom, room_type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                  required
                >
                  {ROOM_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.icon} {type.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Room Name
                </label>
                <input
                  type="text"
                  value={newRoom.name}
                  onChange={(e) => setNewRoom({ ...newRoom, name: e.target.value })}
                  placeholder="e.g., Master Bedroom, Guest Bath"
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                />
              </div>
            </div>

            {/* Bedroom-specific fields */}
            {newRoom.room_type === 'bedroom' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border-t border-gray-200 pt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bed Type
                  </label>
                  <select
                    value={newRoom.bed_type}
                    onChange={(e) => setNewRoom({ ...newRoom, bed_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                  >
                    <option value="">Select bed type</option>
                    {BED_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Number of Beds
                  </label>
                  <input
                    type="number"
                    value={newRoom.bed_count}
                    onChange={(e) => setNewRoom({ ...newRoom, bed_count: parseInt(e.target.value) })}
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                  />
                </div>
                <div>
                  <label className="flex items-center space-x-2 mt-7">
                    <input
                      type="checkbox"
                      checked={newRoom.has_ensuite === 1}
                      onChange={(e) => setNewRoom({ ...newRoom, has_ensuite: e.target.checked ? 1 : 0 })}
                      className="rounded"
                    />
                    <span className="text-sm font-medium text-gray-700">Has Ensuite Bathroom</span>
                  </label>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Amenities
              </label>
              <input
                type="text"
                value={newRoom.amenities}
                onChange={(e) => setNewRoom({ ...newRoom, amenities: e.target.value })}
                placeholder="e.g., TV, Mini Fridge, Balcony"
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                value={newRoom.notes}
                onChange={(e) => setNewRoom({ ...newRoom, notes: e.target.value })}
                placeholder="Additional information about this room..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>

            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Add Room
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Rooms List */}
      {rooms.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <p className="text-gray-600 text-lg">No rooms defined yet</p>
          <p className="text-gray-500 text-sm mt-2">Add rooms to showcase your property layout</p>
        </div>
      ) : (
        <div className="space-y-4">
          {rooms.map((room) => (
            <div key={room.id} className="bg-white rounded-lg shadow p-6">
              {editingRoom === room.id ? (
                // Edit Mode
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleUpdateRoom(room.id);
                  }}
                  className="space-y-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Room Type *
                      </label>
                      <select
                        value={editForm.room_type}
                        onChange={(e) => setEditForm({ ...editForm, room_type: e.target.value as any })}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                        required
                      >
                        {ROOM_TYPES.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.icon} {type.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Room Name
                      </label>
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        placeholder="e.g., Master Bedroom"
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                  </div>

                  {editForm.room_type === 'bedroom' && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border-t border-gray-200 pt-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Bed Type
                        </label>
                        <select
                          value={editForm.bed_type}
                          onChange={(e) => setEditForm({ ...editForm, bed_type: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded"
                        >
                          <option value="">Select bed type</option>
                          {BED_TYPES.map((type) => (
                            <option key={type} value={type}>
                              {type}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Number of Beds
                        </label>
                        <input
                          type="number"
                          value={editForm.bed_count}
                          onChange={(e) => setEditForm({ ...editForm, bed_count: parseInt(e.target.value) })}
                          min="0"
                          className="w-full px-3 py-2 border border-gray-300 rounded"
                        />
                      </div>
                      <div>
                        <label className="flex items-center space-x-2 mt-7">
                          <input
                            type="checkbox"
                            checked={editForm.has_ensuite === 1}
                            onChange={(e) => setEditForm({ ...editForm, has_ensuite: e.target.checked ? 1 : 0 })}
                            className="rounded"
                          />
                          <span className="text-sm font-medium text-gray-700">Has Ensuite</span>
                        </label>
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Amenities
                    </label>
                    <input
                      type="text"
                      value={editForm.amenities}
                      onChange={(e) => setEditForm({ ...editForm, amenities: e.target.value })}
                      placeholder="e.g., TV, Mini Fridge"
                      className="w-full px-3 py-2 border border-gray-300 rounded"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Notes
                    </label>
                    <textarea
                      value={editForm.notes}
                      onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                      placeholder="Additional notes..."
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded"
                    />
                  </div>

                  <div className="flex gap-2 justify-end">
                    <button
                      type="button"
                      onClick={() => setEditingRoom(null)}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                      Save Changes
                    </button>
                  </div>
                </form>
              ) : (
                // View Mode
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {getRoomIcon(room.room_type)} {room.name || getRoomLabel(room.room_type)}
                      </h3>
                      <p className="text-sm text-gray-600">{getRoomLabel(room.room_type)}</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEditRoom(room)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                        title="Edit"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDeleteRoom(room.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    {room.room_type === 'bedroom' && room.bed_type && (
                      <div>
                        <span className="text-gray-600">Bed:</span>
                        <span className="ml-2 font-medium">
                          {room.bed_count > 1 ? `${room.bed_count}x ` : ''}
                          {room.bed_type}
                        </span>
                      </div>
                    )}
                    {room.room_type === 'bedroom' && room.has_ensuite === 1 && (
                      <div>
                        <span className="inline-block px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                          ✓ Ensuite
                        </span>
                      </div>
                    )}
                    {room.amenities && (
                      <div className="col-span-2">
                        <span className="text-gray-600">Amenities:</span>
                        <span className="ml-2 font-medium">{room.amenities}</span>
                      </div>
                    )}
                  </div>

                  {room.notes && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-sm text-gray-700">{room.notes}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Room Summary */}
      {rooms.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">📊 Room Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div>
              <span className="text-blue-800">Bedrooms:</span>
              <span className="ml-2 font-bold">
                {rooms.filter((r) => r.room_type === 'bedroom').length}
              </span>
            </div>
            <div>
              <span className="text-blue-800">Bathrooms:</span>
              <span className="ml-2 font-bold">
                {rooms.filter((r) => r.room_type === 'bathroom').length}
              </span>
            </div>
            <div>
              <span className="text-blue-800">Total Beds:</span>
              <span className="ml-2 font-bold">
                {rooms
                  .filter((r) => r.room_type === 'bedroom')
                  .reduce((sum, r) => sum + r.bed_count, 0)}
              </span>
            </div>
            <div>
              <span className="text-blue-800">Ensuites:</span>
              <span className="ml-2 font-bold">
                {rooms.filter((r) => r.has_ensuite === 1).length}
              </span>
            </div>
            <div>
              <span className="text-blue-800">Total Rooms:</span>
              <span className="ml-2 font-bold">{rooms.length}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
