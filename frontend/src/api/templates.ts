import { apiClient } from './client';
import { MessageTemplate, TemplatePreviewResponse } from '../types';

export const templatesApi = {
  list: async (): Promise<MessageTemplate[]> => {
    const res = await apiClient.get<MessageTemplate[]>('/templates');
    return res.data;
  },

  get: async (id: string): Promise<MessageTemplate> => {
    const res = await apiClient.get<MessageTemplate>(`/templates/${id}`);
    return res.data;
  },

  create: async (data: {
    title: string;
    subject: string;
    body_content: string;
    required_variables?: string[];
  }): Promise<MessageTemplate> => {
    const res = await apiClient.post<MessageTemplate>('/templates', data);
    return res.data;
  },

  update: async (
    id: string,
    data: {
      title?: string;
      subject?: string;
      body_content?: string;
      required_variables?: string[];
    }
  ): Promise<MessageTemplate> => {
    const res = await apiClient.put<MessageTemplate>(`/templates/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/templates/${id}`);
  },

  preview: async (id: string, variables: Record<string, any>): Promise<TemplatePreviewResponse> => {
    const res = await apiClient.post<TemplatePreviewResponse>(`/templates/${id}/preview`, {
      variables,
    });
    return res.data;
  },
};
