/**
 * Property Rooms API Service
 */

export interface PropertyRoom {
  id: string;
  property_id: string;
  room_type: 'bedroom' | 'bathroom' | 'kitchen' | 'living_room' | 'other';
  name: string | null;
  bed_type: string | null;
  bed_count: number;
  has_ensuite: number;
  amenities: string | null;
  notes: string | null;
  display_order: number;
}

class PropertyRoomsApi {
  private baseUrl = '/api';

  private getAuthToken(): string {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('Not authenticated');
    }
    return token;
  }

  async getRooms(propertyId: string): Promise<PropertyRoom[]> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/rooms`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch rooms');
    }

    const data = await response.json();
    return data.rooms;
  }

  async createRoom(
    propertyId: string,
    room: {
      room_type: 'bedroom' | 'bathroom' | 'kitchen' | 'living_room' | 'other';
      name?: string;
      bed_type?: string;
      bed_count?: number;
      has_ensuite?: number;
      amenities?: string;
      notes?: string;
    }
  ): Promise<PropertyRoom> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/rooms`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(room),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create room');
    }

    const data = await response.json();
    return data.room;
  }

  async updateRoom(
    propertyId: string,
    roomId: string,
    updates: {
      room_type?: 'bedroom' | 'bathroom' | 'kitchen' | 'living_room' | 'other';
      name?: string;
      bed_type?: string;
      bed_count?: number;
      has_ensuite?: number;
      amenities?: string;
      notes?: string;
      display_order?: number;
    }
  ): Promise<PropertyRoom> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/rooms/${roomId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update room');
    }

    const data = await response.json();
    return data.room;
  }

  async deleteRoom(propertyId: string, roomId: string): Promise<void> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/rooms/${roomId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete room');
    }
  }
}

export const propertyRoomsApi = new PropertyRoomsApi();
