import { apiClient } from './client';
import { Subscriber, SubscriberListResponse, BatchImportResult } from '../types';

export const subscribersApi = {
  list: async (params?: {
    page?: number;
    size?: number;
    search?: string;
    tag?: string;
    is_active?: boolean;
  }): Promise<SubscriberListResponse> => {
    const res = await apiClient.get<SubscriberListResponse>('/subscribers', { params });
    return res.data;
  },

  getTags: async (): Promise<string[]> => {
    const res = await apiClient.get<string[]>('/subscribers/tags');
    return res.data;
  },

  get: async (id: string): Promise<Subscriber> => {
    const res = await apiClient.get<Subscriber>(`/subscribers/${id}`);
    return res.data;
  },

  create: async (data: {
    email: string;
    full_name?: string;
    phone?: string;
    tags_attributes?: string[];
    is_active?: boolean;
  }): Promise<Subscriber> => {
    const res = await apiClient.post<Subscriber>('/subscribers', data);
    return res.data;
  },

  update: async (
    id: string,
    data: {
      email?: string;
      full_name?: string;
      phone?: string;
      tags_attributes?: string[];
      is_active?: boolean;
    }
  ): Promise<Subscriber> => {
    const res = await apiClient.put<Subscriber>(`/subscribers/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/subscribers/${id}`);
  },

  importCsv: async (file: File): Promise<BatchImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<BatchImportResult>('/subscribers/import-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  unsubscribe: async (id: string): Promise<Subscriber> => {
    const res = await apiClient.patch<Subscriber>(`/subscribers/${id}/unsubscribe`);
    return res.data;
  },
};
