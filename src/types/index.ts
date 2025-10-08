export interface User {
  userId: number;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  email_verified: boolean;
}

export type UserRole =
  | 'admin'
  | 'property_owner'
  | 'property_manager'
  | 'service_staff'
  | 'tenant'
  | 'property_guest';

export interface Property {
  id: number;
  name: string;
  address: string;
  city?: string;
  state?: string;
  zip_code?: string;
  property_type?: string;
  status?: string;
  bedrooms?: number;
  bathrooms?: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string;
  property_id?: number;
  property_name?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export type TaskStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface CalendarEvent {
  id: number;
  property_id: number;
  title: string;
  start_date: string;
  end_date: string;
  source: string;
  guest_name?: string;
  guest_count?: number;
  booking_amount?: number;
  booking_status?: string;
  platform_name?: string;
}

export interface CleaningSession {
  id: number;
  property_id: number;
  cleaner_id: number;
  start_time: string;
  end_time?: string;
  status: CleaningSessionStatus;
  notes?: string;
  property_name?: string;
  property_address?: string;
  cleaner_first_name?: string;
  cleaner_last_name?: string;
  created_at: string;
  updated_at: string;
}

export type CleaningSessionStatus = 'in_progress' | 'completed' | 'cancelled';

export interface CleaningPhoto {
  key: string;
  url: string;
  type: 'image' | 'video';
  photoType: 'before' | 'after' | 'issue' | 'general';
  size: number;
  contentType: string;
  uploadedBy: number;
  uploadedAt: string;
  originalName: string;
}
