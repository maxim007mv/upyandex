import { apiClient } from './client';
import { GlobalStats } from '../types';

export const statsApi = {
  getOverview: async (): Promise<GlobalStats> => {
    const res = await apiClient.get<GlobalStats>('/stats/overview');
    return res.data;
  },
};
