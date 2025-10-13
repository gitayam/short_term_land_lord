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

  async get(id: string) {
    return fetchApi<any>(`/tasks/${id}`);
  },

  async update(id: string, taskData: any) {
    return fetchApi<any>(`/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(taskData),
    });
  },

  async delete(id: string) {
    return fetchApi<any>(`/tasks/${id}`, {
      method: 'DELETE',
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

  // Property calendar management
  async listPropertyCalendars(propertyId: string) {
    return fetchApi<any>(`/properties/${propertyId}/calendars`);
  },

  async addPropertyCalendar(propertyId: string, data: { platform_name: string; ical_url: string }) {
    return fetchApi<any>(`/properties/${propertyId}/calendars`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updatePropertyCalendar(propertyId: string, calendarId: string, data: { platform_name?: string; ical_url?: string; is_active?: boolean }) {
    return fetchApi<any>(`/properties/${propertyId}/calendars/${calendarId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deletePropertyCalendar(propertyId: string, calendarId: string) {
    return fetchApi<any>(`/properties/${propertyId}/calendars/${calendarId}`, {
      method: 'DELETE',
    });
  },

  // Get iCal feed URL for property
  getICalFeedUrl(propertyId: string): string {
    return `${window.location.origin}/api/properties/${propertyId}/calendar.ics`;
  },

  // Block dates on property calendar
  async blockDates(propertyId: string, data: { start_date: string; end_date: string; reason?: string }) {
    return fetchApi<any>(`/properties/${propertyId}/block-dates`, {
      method: 'POST',
      body: JSON.stringify(data),
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

// Expenses API
export const expensesApi = {
  async list(filters?: {
    property_id?: string;
    category?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const queryString = params.toString();
    return fetchApi<any>(`/expenses${queryString ? `?${queryString}` : ''}`);
  },

  async get(id: string) {
    return fetchApi<any>(`/expenses/${id}`);
  },

  async create(expenseData: any) {
    return fetchApi<any>('/expenses', {
      method: 'POST',
      body: JSON.stringify(expenseData),
    });
  },

  async update(id: string, expenseData: any) {
    return fetchApi<any>(`/expenses/${id}`, {
      method: 'PUT',
      body: JSON.stringify(expenseData),
    });
  },

  async delete(id: string) {
    return fetchApi<any>(`/expenses/${id}`, {
      method: 'DELETE',
    });
  },

  async getCategories() {
    return fetchApi<any>('/expenses/categories');
  },
};

// Revenue API
export const revenueApi = {
  async list(filters?: {
    property_id?: string;
    source?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.source) params.append('source', filters.source);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const queryString = params.toString();
    return fetchApi<any>(`/revenue${queryString ? `?${queryString}` : ''}`);
  },

  async create(revenueData: any) {
    return fetchApi<any>('/revenue', {
      method: 'POST',
      body: JSON.stringify(revenueData),
    });
  },

  async getSummary(filters?: {
    property_id?: string;
    start_date?: string;
    end_date?: string;
  }) {
    const params = new URLSearchParams();
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const queryString = params.toString();
    return fetchApi<any>(`/revenue/summary${queryString ? `?${queryString}` : ''}`);
  },
};

// Invoices API
export const invoicesApi = {
  async list(filters?: {
    property_id?: string;
    booking_id?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.booking_id) params.append('booking_id', filters.booking_id);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const queryString = params.toString();
    return fetchApi<any>(`/invoices${queryString ? `?${queryString}` : ''}`);
  },

  async get(id: string) {
    return fetchApi<any>(`/invoices/${id}`);
  },

  async create(invoiceData: any) {
    return fetchApi<any>('/invoices', {
      method: 'POST',
      body: JSON.stringify(invoiceData),
    });
  },

  async update(id: string, invoiceData: any) {
    return fetchApi<any>(`/invoices/${id}`, {
      method: 'PUT',
      body: JSON.stringify(invoiceData),
    });
  },

  async delete(id: string) {
    return fetchApi<any>(`/invoices/${id}`, {
      method: 'DELETE',
    });
  },

  async send(id: string) {
    return fetchApi<any>(`/invoices/${id}/send`, {
      method: 'POST',
    });
  },

  async getPayments(id: string) {
    return fetchApi<any>(`/invoices/${id}/payments`);
  },

  async recordPayment(id: string, paymentData: any) {
    return fetchApi<any>(`/invoices/${id}/payments`, {
      method: 'POST',
      body: JSON.stringify(paymentData),
    });
  },
};

// Inventory Catalog API
export const inventoryCatalogApi = {
  async list(filters?: {
    category?: string;
    search?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (filters?.category) params.append('category', filters.category);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const queryString = params.toString();
    return fetchApi<any>(`/inventory/catalog${queryString ? `?${queryString}` : ''}`);
  },

  async get(id: string) {
    return fetchApi<any>(`/inventory/catalog/${id}`);
  },

  async create(itemData: any) {
    return fetchApi<any>('/inventory/catalog', {
      method: 'POST',
      body: JSON.stringify(itemData),
    });
  },

  async update(id: string, itemData: any) {
    return fetchApi<any>(`/inventory/catalog/${id}`, {
      method: 'PUT',
      body: JSON.stringify(itemData),
    });
  },

  async delete(id: string) {
    return fetchApi<any>(`/inventory/catalog/${id}`, {
      method: 'DELETE',
    });
  },
};

// Inventory Items API
export const inventoryItemsApi = {
  async list(filters?: {
    property_id?: string;
    category?: string;
    low_stock?: boolean;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.low_stock) params.append('low_stock', 'true');
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const queryString = params.toString();
    return fetchApi<any>(`/inventory/items${queryString ? `?${queryString}` : ''}`);
  },

  async get(id: string) {
    return fetchApi<any>(`/inventory/items/${id}`);
  },

  async create(itemData: any) {
    return fetchApi<any>('/inventory/items', {
      method: 'POST',
      body: JSON.stringify(itemData),
    });
  },

  async update(id: string, itemData: any) {
    return fetchApi<any>(`/inventory/items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(itemData),
    });
  },

  async delete(id: string) {
    return fetchApi<any>(`/inventory/items/${id}`, {
      method: 'DELETE',
    });
  },

  async adjust(id: string, adjustment: number) {
    return fetchApi<any>(`/inventory/items/${id}/adjust`, {
      method: 'POST',
      body: JSON.stringify({ adjustment }),
    });
  },
};

// Guidebook API
export const guidebookApi = {
  async get(propertyId: string) {
    return fetchApi<any>(`/guidebook/${propertyId}`);
  },

  async create(propertyId: string, guidebookData: any) {
    return fetchApi<any>(`/guidebook/${propertyId}`, {
      method: 'POST',
      body: JSON.stringify(guidebookData),
    });
  },

  async update(propertyId: string, guidebookData: any) {
    return fetchApi<any>(`/guidebook/${propertyId}`, {
      method: 'PUT',
      body: JSON.stringify(guidebookData),
    });
  },

  async delete(propertyId: string) {
    return fetchApi<any>(`/guidebook/${propertyId}`, {
      method: 'DELETE',
    });
  },
};

// Guest Portal API (public - no auth required)
export const guestPortalApi = {
  async getByAccessCode(accessCode: string) {
    // Bypass auth for public endpoint
    const response = await fetch(`${API_BASE_URL}/guest-portal/${accessCode}`);
    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(response.status, data.error || data.message || 'An error occurred');
    }

    return data;
  },
};

// Access Codes API
export const accessCodesApi = {
  async list(filters?: {
    property_id?: string;
    status?: string;
  }) {
    const params = new URLSearchParams();
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.status) params.append('status', filters.status);

    const queryString = params.toString();
    return fetchApi<any>(`/access-codes${queryString ? `?${queryString}` : ''}`);
  },

  async create(codeData: any) {
    return fetchApi<any>('/access-codes', {
      method: 'POST',
      body: JSON.stringify(codeData),
    });
  },
};

// Recommendations API
export const recommendationsApi = {
  async list(propertyId: string) {
    return fetchApi<any>(`/recommendations/${propertyId}`);
  },

  async create(propertyId: string, recommendationData: any) {
    return fetchApi<any>(`/recommendations/${propertyId}`, {
      method: 'POST',
      body: JSON.stringify(recommendationData),
    });
  },
};

// Messages API (Internal Messaging)
export const messagesApi = {
  async list(type: 'inbox' | 'sent' | 'unread' = 'inbox', filters?: {
    property_id?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams({ type });
    if (filters?.property_id) params.append('property_id', filters.property_id);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    return fetchApi<any>(`/messages?${params.toString()}`);
  },

  async send(messageData: {
    recipient_id: string;
    subject?: string;
    body: string;
    priority?: string;
    property_id?: string;
    task_id?: string;
  }) {
    return fetchApi<any>('/messages', {
      method: 'POST',
      body: JSON.stringify(messageData),
    });
  },

  async markAsRead(messageId: string) {
    return fetchApi<any>(`/messages/${messageId}/read`, {
      method: 'PUT',
    });
  },
};

// Message Templates API
export const messageTemplatesApi = {
  async list(filters?: {
    category?: string;
    active?: boolean;
  }) {
    const params = new URLSearchParams();
    if (filters?.category) params.append('category', filters.category);
    if (filters?.active !== undefined) params.append('active', filters.active.toString());

    const queryString = params.toString();
    return fetchApi<any>(`/message-templates${queryString ? `?${queryString}` : ''}`);
  },

  async create(templateData: {
    name: string;
    category: string;
    subject?: string;
    body: string;
    variables?: string[];
    channel?: 'email' | 'sms' | 'both';
    is_active?: boolean;
  }) {
    return fetchApi<any>('/message-templates', {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  },
};

// SMS API
export const smsApi = {
  async send(smsData: {
    recipient_phone: string;
    recipient_name?: string;
    recipient_user_id?: string;
    message_body: string;
    template_id?: string;
    property_id?: string;
    booking_id?: string;
  }) {
    return fetchApi<any>('/sms/send', {
      method: 'POST',
      body: JSON.stringify(smsData),
    });
  },
};

export { ApiError };
