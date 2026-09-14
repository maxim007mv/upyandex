import { apiClient } from './client';
import { Mailing, MailingListResponse, MailingStats, DeliveryListResponse } from '../types';

export const mailingsApi = {
  list: async (params?: {
    page?: number;
    size?: number;
    status?: string;
  }): Promise<MailingListResponse> => {
    const res = await apiClient.get<MailingListResponse>('/mailings', { params });
    return res.data;
  },

  get: async (id: string): Promise<Mailing> => {
    const res = await apiClient.get<Mailing>(`/mailings/${id}`);
    return res.data;
  },

  create: async (data: {
    title: string;
    description?: string;
    template_id: string;
    recipient_filter: Record<string, any>;
    scheduled_at?: string | null;
  }): Promise<Mailing> => {
    const res = await apiClient.post<Mailing>('/mailings', data);
    return res.data;
  },

  update: async (
    id: string,
    data: {
      title?: string;
      description?: string;
      template_id?: string;
      recipient_filter?: Record<string, any>;
      scheduled_at?: string | null;
    }
  ): Promise<Mailing> => {
    const res = await apiClient.put<Mailing>(`/mailings/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/mailings/${id}`);
  },

  start: async (id: string): Promise<Mailing> => {
    const res = await apiClient.post<Mailing>(`/mailings/${id}/start`);
    return res.data;
  },

  cancel: async (id: string): Promise<Mailing> => {
    const res = await apiClient.post<Mailing>(`/mailings/${id}/cancel`);
    return res.data;
  },

  stats: async (id: string): Promise<MailingStats> => {
    const res = await apiClient.get<MailingStats>(`/mailings/${id}/stats`);
    return res.data;
  },

  messages: async (
    id: string,
    params?: {
      page?: number;
      size?: number;
      status?: string;
    }
  ): Promise<DeliveryListResponse> => {
    const res = await apiClient.get<DeliveryListResponse>(`/mailings/${id}/messages`, { params });
    return res.data;
  },

  retryFailed: async (id: string): Promise<{ retried_count: number; message: string }> => {
    const res = await apiClient.post<{ retried_count: number; message: string }>(
      `/mailings/${id}/retry-failed`
    );
    return res.data;
  },
};
