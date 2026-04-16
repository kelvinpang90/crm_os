// === User ===
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'manager' | 'sales';
  avatar_url: string | null;
  language: string;
  manager_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// === Contact ===
export type ContactStatus = 'lead' | 'following' | 'negotiating' | 'won' | 'lost';
export type Priority = 'high' | 'mid' | 'low';

export interface Contact {
  id: string;
  name: string;
  company: string | null;
  industry: string | null;
  status: ContactStatus;
  priority: Priority;
  deal_value: number;
  email: string | null;
  phone: string | null;
  address: string | null;
  notes: string | null;
  assigned_to: string | null;
  assigned_to_name?: string | null;
  last_contact: string | null;
  tags: string[] | null;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
}

// === Activity ===
export type ActivityType = '电话' | '邮件' | '会面' | 'WhatsApp' | '其他' | '状态变更';

export interface Activity {
  id: string;
  contact_id: string;
  user_id: string;
  type: ActivityType;
  content: string | null;
  follow_date: string;
  created_at: string;
  user_name?: string;
}

// === Task ===
export interface Task {
  id: string;
  title: string;
  contact_id: string | null;
  assigned_to: string | null;
  priority: Priority;
  due_date: string | null;
  is_done: boolean;
  done_at: string | null;
  created_at: string;
  updated_at: string;
  contact_name?: string;
  assigned_to_name?: string;
}

// === Message ===
export type MessageChannel = 'whatsapp' | 'email';
export type MessageDirection = 'inbound' | 'outbound';

export interface Message {
  id: string;
  contact_id: string | null;
  channel: MessageChannel;
  direction: MessageDirection;
  sender_id: string;
  recipient_id: string;
  subject: string | null;
  body: string;
  external_id: string | null;
  is_read: boolean;
  assigned_to: string | null;
  created_at: string;
  contact_name?: string;
}

// === Routing Rule ===
export type RoutingStrategy = 'workload' | 'region' | 'win_rate';

export interface RoutingRule {
  id: string;
  name: string;
  is_active: boolean;
  priority: number;
  strategy: RoutingStrategy;
  conditions: Record<string, unknown> | null;
  target_users: string[] | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

// === Sales Target ===
export interface SalesTarget {
  id: string;
  user_id: string;
  year: number;
  month: number;
  target_amount: number;
  target_count: number;
  created_at: string;
  updated_at: string;
}

// === API Response ===
export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  message: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
  };
}
