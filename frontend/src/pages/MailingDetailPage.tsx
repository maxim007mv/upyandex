import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Play,
  XCircle,
  RotateCcw,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Send,
  Mail,
  Zap,
} from 'lucide-react';
import { mailingsApi } from '../api/mailings';
import { Mailing, MailingStats, DeliveryLog } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ProgressBar } from '../components/ProgressBar';
import { StatCard } from '../components/StatCard';

interface MailingDetailPageProps {
  mailingId: string;
  onNavigate: (tab: string, detailId?: string) => void;
}

export const MailingDetailPage: React.FC<MailingDetailPageProps> = ({
  mailingId,
  onNavigate,
}) => {
  const [mailing, setMailing] = useState<Mailing | null>(null);
  const [stats, setStats] = useState<MailingStats | null>(null);
  const [messages, setMessages] = useState<DeliveryLog[]>([]);
  const [totalMessages, setTotalMessages] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [size] = useState(25);
  const [isLoading, setIsLoading] = useState(false);

  const fetchDetails = async () => {
    try {
      const [m, s] = await Promise.all([
        mailingsApi.get(mailingId),
        mailingsApi.stats(mailingId),
      ]);
      setMailing(m);
      setStats(s);

      const logs = await mailingsApi.messages(mailingId, {
        page,
        size,
        status: statusFilter || undefined,
      });
      setMessages(logs.items);
      setTotalMessages(logs.total);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDetails();
    // Auto-refresh when processing
    const interval = setInterval(() => {
      if (mailing?.status === 'PROCESSING') {
        fetchDetails();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [mailingId, page, statusFilter, mailing?.status]);

  const handleStart = async () => {
    try {
      await mailingsApi.start(mailingId);
      fetchDetails();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Не удалось запустить');
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Отменить рассылку?')) return;
    try {
      await mailingsApi.cancel(mailingId);
      fetchDetails();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Не удалось отменить');
    }
  };

  const handleRetryFailed = async () => {
    try {
      const res = await mailingsApi.retryFailed(mailingId);
      alert(`Отправлено на повтор: ${res.retried_count}`);
      fetchDetails();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка повтора');
    }
  };

  if (!mailing) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" />
        Загрузка сведений о рассылке...
      </div>
    );
  }

  const deliveryRate = stats?.delivery_rate_percent || 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Back button */}
      <button
        onClick={() => onNavigate('mailings')}
        className="flex items-center text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1.5" />
        Вернуться ко всем рассылкам
      </button>

      {/* Header card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold text-slate-900">{mailing.title}</h1>
            <StatusBadge status={mailing.status} />
          </div>
          {mailing.description && (
            <p className="text-xs text-slate-500">{mailing.description}</p>
          )}
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 pt-1">
            <span className="font-mono text-[11px]">ID: {mailing.id}</span>
            <span>•</span>
            <span>Шаблон: {mailing.template?.title || '—'}</span>
            <span>•</span>
            <span>
              Создано: {new Date(mailing.created_at).toLocaleString('ru-RU')}
            </span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={fetchDetails}
            className="p-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50"
            title="Обновить"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {(mailing.status === 'DRAFT' || mailing.status === 'SCHEDULED') && (
            <button
              onClick={handleStart}
              className="flex items-center px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm transition-colors"
            >
              <Play className="w-3.5 h-3.5 mr-1.5 fill-white" />
              Запустить сейчас
            </button>
          )}

          {(mailing.status === 'PROCESSING' || mailing.status === 'SCHEDULED') && (
            <button
              onClick={handleCancel}
              className="flex items-center px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
            >
              <XCircle className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
              Остановить
            </button>
          )}

          {stats && stats.failed_count > 0 && mailing.status !== 'PROCESSING' && (
            <button
              onClick={handleRetryFailed}
              className="flex items-center px-4 py-2.5 rounded-xl text-xs font-semibold text-amber-800 bg-amber-50 border border-amber-200 hover:bg-amber-100 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1.5 text-amber-600" />
              Повторить ошибки ({stats.failed_count})
            </button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Всего получателей"
          value={stats?.total_count || mailing.total_count}
          icon={<Mail className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          title="Успешно отправлено"
          value={stats?.success_count || mailing.success_count}
          icon={<CheckCircle2 className="w-5 h-5" />}
          color="emerald"
        />
        <StatCard
          title="Ошибки доставки"
          value={stats?.failed_count || mailing.failed_count}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="rose"
        />
        <StatCard
          title="В очереди"
          value={stats?.pending_count || 0}
          icon={<Clock className="w-5 h-5" />}
          color="amber"
        />
        <StatCard
          title="Доставляемость"
          value={`${deliveryRate}%`}
          subtitle={
            stats?.duration_seconds ? `Время: ${stats.duration_seconds} сек.` : undefined
          }
          icon={<Zap className="w-5 h-5" />}
          color="purple"
        />
      </div>

      {/* Progress Bar Card */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
        <h3 className="text-xs font-semibold text-slate-700 uppercase">
          Прогресс выполнения кампании
        </h3>
        <ProgressBar
          total={stats?.total_count || mailing.total_count}
          success={stats?.success_count || mailing.success_count}
          failed={stats?.failed_count || mailing.failed_count}
        />
      </div>

      {/* Delivery Logs Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Журнал отправки (Delivery Log)</h3>
            <p className="text-xs text-slate-500">Детализация по каждому атомарному письму</p>
          </div>

          <div className="flex items-center space-x-1">
            {[
              { id: '', label: 'Все' },
              { id: 'SENT', label: 'Успешно' },
              { id: 'FAILED', label: 'Ошибки' },
              { id: 'PENDING', label: 'В очереди' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => {
                  setStatusFilter(f.id);
                  setPage(1);
                }}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  statusFilter === f.id
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-[11px] uppercase font-semibold text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Адресат</th>
                <th className="px-6 py-3">Канал</th>
                <th className="px-6 py-3">Статус</th>
                <th className="px-6 py-3">Попыток</th>
                <th className="px-6 py-3">Текст ошибки</th>
                <th className="px-6 py-3">Время отправки</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {messages.length > 0 ? (
                messages.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50/70">
                    <td className="px-6 py-3.5">
                      <div className="font-semibold text-slate-900">{d.recipient_name || '—'}</div>
                      <div className="text-slate-500 font-mono text-[11px]">
                        {d.recipient_email}
                      </div>
                    </td>
                    <td className="px-6 py-3.5 font-mono text-[11px] text-slate-600">
                      {d.channel}
                    </td>
                    <td className="px-6 py-3.5">
                      <StatusBadge status={d.status} size="sm" />
                    </td>
                    <td className="px-6 py-3.5 font-mono">{d.retry_count}</td>
                    <td className="px-6 py-3.5 max-w-xs truncate text-rose-600 font-mono text-[11px]">
                      {d.error_message || '—'}
                    </td>
                    <td className="px-6 py-3.5 text-slate-400">
                      {d.sent_at
                        ? new Date(d.sent_at).toLocaleTimeString('ru-RU')
                        : 'В ожидании'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-slate-400">
                    Сообщения не найдены
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
