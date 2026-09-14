import React, { useEffect, useState } from 'react';
import {
  Send,
  Plus,
  Play,
  XCircle,
  RotateCcw,
  Clock,
  Trash2,
  Eye,
  RefreshCw,
} from 'lucide-react';
import { mailingsApi } from '../api/mailings';
import { Mailing } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ProgressBar } from '../components/ProgressBar';

interface MailingsPageProps {
  onNavigate: (tab: string, detailId?: string) => void;
}

export const MailingsPage: React.FC<MailingsPageProps> = ({ onNavigate }) => {
  const [mailings, setMailings] = useState<Mailing[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(15);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const fetchMailings = async () => {
    setIsLoading(true);
    try {
      const data = await mailingsApi.list({
        page,
        size,
        status: statusFilter || undefined,
      });
      setMailings(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load mailings', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMailings();
    // Auto-poll active mailings every 5s
    const interval = setInterval(fetchMailings, 5000);
    return () => clearInterval(interval);
  }, [page, statusFilter]);

  const handleStart = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await mailingsApi.start(id);
      fetchMailings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Не удалось запустить рассылку');
    }
  };

  const handleCancel = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Отменить эту рассылку? Отправка оставшихся писем будет остановлена.')) return;
    try {
      await mailingsApi.cancel(id);
      fetchMailings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Не удалось отменить рассылку');
    }
  };

  const handleRetryFailed = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await mailingsApi.retryFailed(id);
      alert(`Повторно отправлено: ${res.retried_count}`);
      fetchMailings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка повторной отправки');
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Удалить кампанию и журнал ее отправки?')) return;
    try {
      await mailingsApi.delete(id);
      fetchMailings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка при удалении');
    }
  };

  const tabs = [
    { id: '', label: 'Все' },
    { id: 'PROCESSING', label: 'В процессе' },
    { id: 'SCHEDULED', label: 'Запланированные' },
    { id: 'COMPLETED', label: 'Завершенные' },
    { id: 'DRAFT', label: 'Черновики' },
    { id: 'FAILED', label: 'С ошибками' },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Кампании и рассылки</h1>
          <p className="text-sm text-slate-500 mt-1">
            Контроль очередей, пакетная отправка и аналитика доставки сообщений
          </p>
        </div>
        <button
          onClick={() => onNavigate('mailing-create')}
          className="flex items-center px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 shadow-sm shadow-brand-500/20 transition-all"
        >
          <Plus className="w-4 h-4 mr-2" />
          Создать рассылку
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-1 border-b border-slate-200 overflow-x-auto pb-px">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setStatusFilter(tab.id);
              setPage(1);
            }}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-xl border-b-2 transition-colors whitespace-nowrap ${
              statusFilter === tab.id
                ? 'border-brand-600 text-brand-600 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Mailings Table / List */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        {mailings.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {mailings.map((m) => (
              <div
                key={m.id}
                onClick={() => onNavigate('mailing-detail', m.id)}
                className="p-5 hover:bg-slate-50/70 cursor-pointer transition-colors flex flex-col lg:flex-row lg:items-center justify-between gap-4"
              >
                {/* Left: Info */}
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-bold text-base text-slate-900 truncate">{m.title}</h3>
                    <StatusBadge status={m.status} />
                  </div>
                  {m.description && (
                    <p className="text-xs text-slate-500 line-clamp-1">{m.description}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                    <span className="flex items-center">
                      <Clock className="w-3.5 h-3.5 mr-1" />
                      {m.scheduled_at
                        ? `Запланировано: ${new Date(m.scheduled_at).toLocaleString('ru-RU')}`
                        : `Создано: ${new Date(m.created_at).toLocaleString('ru-RU')}`}
                    </span>
                    {m.template && (
                      <span>
                        Шаблон: <strong className="text-slate-600">{m.template.title}</strong>
                      </span>
                    )}
                  </div>
                </div>

                {/* Center: Progress */}
                <div className="w-full lg:w-72 shrink-0">
                  <ProgressBar
                    total={m.total_count}
                    success={m.success_count}
                    failed={m.failed_count}
                  />
                </div>

                {/* Right: Actions */}
                <div className="flex items-center space-x-2 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-100">
                  {(m.status === 'DRAFT' || m.status === 'SCHEDULED') && (
                    <button
                      onClick={(e) => handleStart(m.id, e)}
                      title="Запустить немедленно"
                      className="flex items-center text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-colors"
                    >
                      <Play className="w-3 h-3 mr-1 text-emerald-600 fill-emerald-600" />
                      Старт
                    </button>
                  )}

                  {(m.status === 'PROCESSING' || m.status === 'SCHEDULED') && (
                    <button
                      onClick={(e) => handleCancel(m.id, e)}
                      title="Остановить отправку"
                      className="flex items-center text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
                    >
                      <XCircle className="w-3.5 h-3.5 mr-1 text-slate-500" />
                      Отмена
                    </button>
                  )}

                  {m.failed_count > 0 && m.status !== 'PROCESSING' && (
                    <button
                      onClick={(e) => handleRetryFailed(m.id, e)}
                      title="Повторить отправку сообщений с ошибкой"
                      className="flex items-center text-xs font-semibold px-3 py-1.5 rounded-lg bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 transition-colors"
                    >
                      <RotateCcw className="w-3 h-3 mr-1 text-amber-600" />
                      Ретрай ({m.failed_count})
                    </button>
                  )}

                  <button
                    onClick={() => onNavigate('mailing-detail', m.id)}
                    className="p-2 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
                    title="Журнал и статистика"
                  >
                    <Eye className="w-4 h-4" />
                  </button>

                  {m.status !== 'PROCESSING' && (
                    <button
                      onClick={(e) => handleDelete(m.id, e)}
                      className="p-2 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                      title="Удалить"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 text-slate-400 text-sm">
            В этом разделе нет рассылок. Создайте новую рассылку через мастер кампаний.
          </div>
        )}
      </div>
    </div>
  );
};
