/**
 * API Service Layer
 * Handles all HTTP requests to the backend API
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('auth_token');

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new ApiError(response.status, data.error || data.message || 'An error occurred');
  }

  return data;
}

// Authentication API
export const authApi = {
  async login(email: string, password: string) {
    const data = await fetchApi<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (data.token) {
      localStorage.setItem('auth_token', data.token);
    }
    return data;
  },

  async register(userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role?: string;
  }) {
    const data = await fetchApi<any>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    if (data.token) {
      localStorage.setItem('auth_token', data.token);
    }
    return data;
  },

  async logout() {
    await fetchApi('/auth/logout', { method: 'POST' });
    localStorage.removeItem('auth_token');
  },

  async refreshToken() {
    const data = await fetchApi<any>('/auth/refresh', { method: 'POST' });
    if (data.token) {
      localStorage.setItem('auth_token', data.token);
    }
    return data;
  },

  async sendVerificationEmail() {
    return fetchApi('/auth/send-verification', { method: 'POST' });
  },

  async verifyEmail(token: string) {
    return fetchApi('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  },

  async requestPasswordReset(email: string) {
    return fetchApi('/auth/request-password-reset', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },

  async resetPassword(token: string, password: string) {
    return fetchApi('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password }),
    });
  },
};

// Properties API
export const propertiesApi = {
  async list() {
    return fetchApi<any>('/properties');
  },

  async get(id: string) {
    return fetchApi<any>(`/properties/${id}`);
  },

  async create(propertyData: any) {
    return fetchApi<any>('/properties', {
      method: 'POST',
      body: JSON.stringify(propertyData),
    });
  },

  async update(id: string, propertyData: any) {
    return fetchApi<any>(`/properties/${id}`, {
      method: 'PUT',
      body: JSON.stringify(propertyData),
    });
  },

  async delete(id: string) {
    return fetchApi<any>(`/properties/${id}`, {
      method: 'DELETE',
    });
  },

  async uploadImage(propertyId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('property_id', propertyId);

    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${API_BASE_URL}/upload/property-image`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new ApiError(response.status, data.error || 'Upload failed');
    }
    return data;
  },
};

// Tasks API
export const tasksApi = {
  async list(filters?: { status?: string; property_id?: string }) {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.property_id) params.append('property_id', filters.property_id);

    const queryString = params.toString();
    return fetchApi<any>(`/tasks${queryString ? `?${queryString}` : ''}`);
  },

  async create(taskData: any) {
    return fetchApi<any>('/tasks', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  },
};

// Calendar API
export const calendarApi = {
  async getEvents(propertyId: string, startDate?: string, endDate?: string) {
    const params = new URLSearchParams({ property_id: propertyId });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    return fetchApi<any>(`/calendar/events?${params.toString()}`);
  },

  async syncCalendar(propertyId: string) {
    return fetchApi<any>('/calendar/sync', {
      method: 'POST',
      body: JSON.stringify({ property_id: propertyId }),
    });
  },
};

// Cleaning Sessions API
export const cleaningApi = {
  async list(filters?: {
    property_id?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  }) {
    const params = new URLSearchParams();
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const queryString = params.toString();
    return fetchApi<any>(`/cleaning/sessions${queryString ? `?${queryString}` : ''}`);
  },

  async start(propertyId: string, notes?: string) {
    return fetchApi<any>('/cleaning/sessions', {
      method: 'POST',
      body: JSON.stringify({ property_id: propertyId, notes }),
    });
  },

  async get(sessionId: string) {
    return fetchApi<any>(`/cleaning/sessions/${sessionId}`);
  },

  async update(sessionId: string, updates: { notes?: string; status?: string }) {
    return fetchApi<any>(`/cleaning/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },

  async complete(sessionId: string, notes?: string) {
    return fetchApi<any>(`/cleaning/sessions/${sessionId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  },

  async delete(sessionId: string) {
    return fetchApi<any>(`/cleaning/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },

  async uploadPhoto(sessionId: string, file: File, photoType: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('photo_type', photoType);

    const token = localStorage.getItem('auth_token');
    const response = await fetch(
      `${API_BASE_URL}/cleaning/sessions/${sessionId}/photos`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      }
    );

    const data = await response.json();
    if (!response.ok) {
      throw new ApiError(response.status, data.error || 'Upload failed');
    }
    return data;
  },

  async getPhotos(sessionId: string) {
    return fetchApi<any>(`/cleaning/sessions/${sessionId}/photos`);
  },

  async deletePhoto(sessionId: string, fileKey: string) {
    return fetchApi<any>(`/cleaning/sessions/${sessionId}/photos?key=${fileKey}`, {
      method: 'DELETE',
    });
  },
};

export { ApiError };
