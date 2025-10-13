/**
 * Workers API Service
 */

export interface Worker {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'service_staff' | 'property_manager' | 'admin';
  phone: string | null;
  is_active: number;
  created_at: string;
  last_login?: string;
}

export interface WorkerInvitation {
  email: string;
  role: string;
  token: string;
  invitationUrl: string;
  expiresAt: string;
}

export interface PropertyAssignment {
  id: string;
  property_id: string;
  worker_id: string;
  assigned_by_id: string;
  assigned_at: string;
  notes: string | null;
  property_name?: string;
  property_address?: string;
  worker_name?: string;
  worker_email?: string;
  worker_role?: string;
  assigned_by_name?: string;
}

class WorkersApi {
  private baseUrl = '/api';

  // Get auth token from local storage
  private getAuthToken(): string {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('Not authenticated');
    }
    return token;
  }

  // Workers endpoints
  async getWorkers(): Promise<Worker[]> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/workers`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch workers');
    }

    const data = await response.json();
    return data.workers;
  }

  async getWorker(workerId: string): Promise<{ worker: Worker; assignments: PropertyAssignment[] }> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/workers/${workerId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch worker');
    }

    const data = await response.json();
    return { worker: data.worker, assignments: data.assignments };
  }

  async inviteWorker(email: string, role: 'service_staff' | 'property_manager'): Promise<WorkerInvitation> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/workers`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, role }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to invite worker');
    }

    const data = await response.json();
    return data.invitation;
  }

  async updateWorker(
    workerId: string,
    updates: Partial<Pick<Worker, 'first_name' | 'last_name' | 'phone' | 'role' | 'is_active'>>
  ): Promise<Worker> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/workers/${workerId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update worker');
    }

    const data = await response.json();
    return data.worker;
  }

  async deactivateWorker(workerId: string): Promise<void> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/workers/${workerId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to deactivate worker');
    }
  }

  // Property Assignment endpoints
  async getPropertyAssignments(filters?: {
    property_id?: string;
    worker_id?: string;
  }): Promise<PropertyAssignment[]> {
    const token = this.getAuthToken();
    const params = new URLSearchParams();
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.worker_id) params.append('worker_id', filters.worker_id);

    const url = `${this.baseUrl}/property-assignments${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch property assignments');
    }

    const data = await response.json();
    return data.assignments;
  }

  async assignProperty(propertyId: string, workerId: string, notes?: string): Promise<PropertyAssignment> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/property-assignments`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        property_id: propertyId,
        worker_id: workerId,
        notes,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to assign property');
    }

    const data = await response.json();
    return data.assignment;
  }

  async removePropertyAssignment(assignmentId: string): Promise<void> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/property-assignments/${assignmentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to remove property assignment');
    }
  }

  // Worker Invitation endpoints
  async getInvitation(token: string): Promise<{ email: string; role: string; invited_by_name: string }> {
    const response = await fetch(`${this.baseUrl}/worker-invitations/${token}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch invitation');
    }

    const data = await response.json();
    return data.invitation;
  }

  async acceptInvitation(
    token: string,
    userData: {
      first_name: string;
      last_name: string;
      password: string;
      phone?: string;
    }
  ): Promise<void> {
    const response = await fetch(`${this.baseUrl}/worker-invitations/${token}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to accept invitation');
    }
  }
}

export const workersApi = new WorkersApi();
