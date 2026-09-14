import React from 'react';
import clsx from 'clsx';
import { MailingStatus } from '../types';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toUpperCase();

  const getStyle = () => {
    switch (normalized) {
      case 'COMPLETED':
      case 'DELIVERED':
      case 'SENT':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'PROCESSING':
        return 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse';
      case 'SCHEDULED':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'DRAFT':
      case 'PENDING':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'FAILED':
      case 'BOUNCED':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'CANCELLED':
        return 'bg-slate-100 text-slate-600 border-slate-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getLabel = () => {
    switch (normalized) {
      case 'COMPLETED':
        return 'Завершено';
      case 'PROCESSING':
        return 'Отправляется';
      case 'SCHEDULED':
        return 'Запланировано';
      case 'DRAFT':
        return 'Черновик';
      case 'FAILED':
        return 'Ошибка';
      case 'CANCELLED':
        return 'Отменено';
      case 'PENDING':
        return 'В очереди';
      case 'SENT':
        return 'Отправлено';
      case 'DELIVERED':
        return 'Доставлено';
      case 'BOUNCED':
        return 'Отклонено';
      default:
        return status;
    }
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full border',
        getStyle(),
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
      )}
    >
      <span
        className={clsx(
          'w-1.5 h-1.5 rounded-full mr-1.5',
          normalized === 'PROCESSING' && 'bg-blue-500',
          (normalized === 'COMPLETED' || normalized === 'SENT' || normalized === 'DELIVERED') && 'bg-emerald-500',
          normalized === 'SCHEDULED' && 'bg-purple-500',
          (normalized === 'DRAFT' || normalized === 'PENDING') && 'bg-amber-500',
          (normalized === 'FAILED' || normalized === 'BOUNCED') && 'bg-rose-500',
          normalized === 'CANCELLED' && 'bg-slate-400'
        )}
      />
      {getLabel()}
    </span>
  );
};
