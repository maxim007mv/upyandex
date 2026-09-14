export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  phone?: string | null;
  role: 'ADMIN' | 'CLIENT' | 'SUBSCRIBER';
  is_active: boolean;
  tags_attributes: string[];
  created_at: string;
}

export interface Subscriber {
  id: string;
  email: string;
  full_name?: string | null;
  phone?: string | null;
  role: string;
  is_active: boolean;
  tags_attributes: string[];
  created_at: string;
  updated_at: string;
}

export interface SubscriberListResponse {
  items: Subscriber[];
  total: number;
  page: number;
  size: number;
}

export interface BatchImportError {
  line: number;
  email?: string;
  error: string;
}

export interface BatchImportResult {
  total_processed: number;
  added: number;
  updated: number;
  errors: BatchImportError[];
}

export interface MessageTemplate {
  id: string;
  title: string;
  subject: string;
  body_content: string;
  required_variables: string[];
  created_at: string;
  updated_at: string;
}

export interface TemplatePreviewResponse {
  rendered_subject: string;
  rendered_body: string;
  detected_variables: string[];
}

export type MailingStatus = 'DRAFT' | 'SCHEDULED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface Mailing {
  id: string;
  title: string;
  description?: string | null;
  author_id?: string | null;
  template_id: string;
  status: MailingStatus;
  recipient_filter: Record<string, any>;
  scheduled_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  total_count: number;
  success_count: number;
  failed_count: number;
  created_at: string;
  updated_at: string;
  template?: MessageTemplate;
  author?: User;
}

export interface MailingListResponse {
  items: Mailing[];
  total: number;
  page: number;
  size: number;
}

export interface MailingStats {
  mailing_id: string;
  title: string;
  status: MailingStatus;
  total_count: number;
  success_count: number;
  failed_count: number;
  pending_count: number;
  delivery_rate_percent: number;
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds?: number | null;
  chart_data?: {
    sent: number;
    failed: number;
    pending: number;
  };
}

export interface DeliveryLog {
  id: string;
  mailing_id: string;
  recipient_id: string;
  recipient_email: string;
  recipient_name?: string | null;
  channel: 'EMAIL' | 'TELEGRAM' | 'SMS';
  status: 'PENDING' | 'SENT' | 'DELIVERED' | 'FAILED' | 'BOUNCED';
  retry_count: number;
  error_message?: string | null;
  sent_at?: string | null;
  updated_at: string;
}

export interface DeliveryListResponse {
  items: DeliveryLog[];
  total: number;
  page: number;
  size: number;
}

export interface GlobalStats {
  subscribers: {
    total: number;
    active: number;
    inactive: number;
  };
  mailings: {
    total: number;
    active: number;
    scheduled: number;
    completed: number;
  };
  messages: {
    total: number;
    sent: number;
    failed: number;
    pending: number;
    delivery_rate_percent: number;
  };
  templates_count: number;
  recent_mailings: Array<{
    id: string;
    title: string;
    status: MailingStatus;
    total_count: number;
    success_count: number;
    failed_count: number;
    created_at: string;
  }>;
}
