/**
 * Repair Requests API Service
 */

export interface RepairRequest {
  id: string;
  property_id: string;
  reported_by_id: string;
  title: string;
  description: string;
  location: string | null;
  severity: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'approved' | 'rejected' | 'converted';
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  converted_task_id: string | null;
  created_at: string;
  updated_at: string;
  // Joined fields
  property_name?: string;
  property_address?: string;
  reported_by_name?: string;
  reported_by_email?: string;
  reviewed_by_name?: string;
  images?: RepairRequestImage[];
}

export interface RepairRequestImage {
  id: string;
  repair_request_id: string;
  image_url: string;
  uploaded_at: string;
}

class RepairRequestsApi {
  private baseUrl = '/api';

  private getAuthToken(): string {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('Not authenticated');
    }
    return token;
  }

  async getRepairRequests(filters?: {
    property_id?: string;
    status?: string;
  }): Promise<RepairRequest[]> {
    const token = this.getAuthToken();
    const params = new URLSearchParams();
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.status) params.append('status', filters.status);

    const url = `${this.baseUrl}/repair-requests${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch repair requests');
    }

    const data = await response.json();
    return data.requests;
  }

  async getRepairRequest(requestId: string): Promise<RepairRequest> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/repair-requests/${requestId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch repair request');
    }

    const data = await response.json();
    return data.request;
  }

  async createRepairRequest(requestData: {
    property_id: string;
    title: string;
    description: string;
    location?: string;
    severity?: 'low' | 'medium' | 'high' | 'urgent';
    image_urls?: string[];
  }): Promise<RepairRequest> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/repair-requests`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create repair request');
    }

    const data = await response.json();
    return data.request;
  }

  async reviewRepairRequest(
    requestId: string,
    review: {
      status: 'approved' | 'rejected';
      review_notes?: string;
    }
  ): Promise<RepairRequest> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/repair-requests/${requestId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(review),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to review repair request');
    }

    const data = await response.json();
    return data.request;
  }

  async convertToTask(
    requestId: string,
    conversion: {
      assigned_to_id?: string;
      due_date?: string;
      priority?: string;
    }
  ): Promise<any> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/repair-requests/${requestId}/convert`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(conversion),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to convert repair request');
    }

    const data = await response.json();
    return data.task;
  }

  async deleteRepairRequest(requestId: string): Promise<void> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/repair-requests/${requestId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete repair request');
    }
  }
}

export const repairRequestsApi = new RepairRequestsApi();
