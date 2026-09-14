import React, { useEffect, useState } from 'react';
import {
  Users,
  Send,
  CheckCircle,
  AlertTriangle,
  Plus,
  Clock,
  ArrowRight,
  RefreshCw,
  Server,
  Zap,
} from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { ProgressBar } from '../components/ProgressBar';
import { statsApi } from '../api/stats';
import { GlobalStats } from '../types';

interface DashboardPageProps {
  onNavigate: (tab: string, detailId?: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const [stats, setStats] = useState<GlobalStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const data = await statsApi.getOverview();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top action row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Обзор системы</h1>
          <p className="text-sm text-slate-500 mt-1">
            Мониторинг очередей, статусов доставки и управление информационными кампаниями
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchStats}
            title="Обновить данные"
            className="p-2.5 rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => onNavigate('mailing-create')}
            className="flex items-center px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 shadow-sm shadow-brand-500/20 transition-all"
          >
            <Plus className="w-4 h-4 mr-2" />
            Создать рассылку
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="База подписчиков"
          value={stats?.subscribers.total || 0}
          subtitle={`${stats?.subscribers.active || 0} активных получателей`}
          icon={<Users className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Кампании рассылок"
          value={stats?.mailings.total || 0}
          subtitle={`${stats?.mailings.active || 0} в процессе, ${stats?.mailings.scheduled || 0} запланировано`}
          icon={<Send className="w-6 h-6" />}
          color="purple"
        />
        <StatCard
          title="Отправлено писем"
          value={stats?.messages.sent || 0}
          subtitle={`В очереди: ${stats?.messages.pending || 0}, Ошибок: ${stats?.messages.failed || 0}`}
          icon={<CheckCircle className="w-6 h-6" />}
          color="emerald"
        />
        <StatCard
          title="Успешность доставки"
          value={`${stats?.messages.delivery_rate_percent || 100}%`}
          subtitle="Гарантия доставки и идемпотентность"
          icon={<Zap className="w-6 h-6" />}
          color="amber"
        />
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <button
          onClick={() => onNavigate('mailing-create')}
          className="p-5 text-left rounded-2xl bg-white border border-slate-200 hover:border-brand-300 hover:shadow-md transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center mb-3 group-hover:bg-brand-600 group-hover:text-white transition-colors">
            <Send className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 mb-1">Новая кампания</h3>
          <p className="text-xs text-slate-500">
            Запустите пошаговый мастер: выберите шаблон, сегмент получателей и расписание
          </p>
        </button>

        <button
          onClick={() => onNavigate('subscribers')}
          className="p-5 text-left rounded-2xl bg-white border border-slate-200 hover:border-brand-300 hover:shadow-md transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
            <Users className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 mb-1">Импорт базы получателей</h3>
          <p className="text-xs text-slate-500">
            Загрузите список контактов через CSV файл с тегами и контактными данными
          </p>
        </button>

        <button
          onClick={() => onNavigate('templates')}
          className="p-5 text-left rounded-2xl bg-white border border-slate-200 hover:border-brand-300 hover:shadow-md transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-3 group-hover:bg-purple-600 group-hover:text-white transition-colors">
            <Server className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 mb-1">Редактор шаблонов</h3>
          <p className="text-xs text-slate-500">
            Создайте адаптивный HTML-макет письма с переменными Jinja2 и мгновенным превью
          </p>
        </button>
      </div>

      {/* Recent Mailings List */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Недавние рассылки</h2>
            <p className="text-xs text-slate-500">Статусы выполнения и прогресс отправки</p>
          </div>
          <button
            onClick={() => onNavigate('mailings')}
            className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center"
          >
            Все рассылки
            <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </button>
        </div>

        {stats?.recent_mailings && stats.recent_mailings.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {stats.recent_mailings.map((m) => (
              <div
                key={m.id}
                onClick={() => onNavigate('mailing-detail', m.id)}
                className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50/80 cursor-pointer transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2.5">
                    <span className="font-semibold text-sm text-slate-900">{m.title}</span>
                    <StatusBadge status={m.status} size="sm" />
                  </div>
                  <div className="flex items-center text-xs text-slate-400 space-x-2">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(m.created_at).toLocaleString('ru-RU')}</span>
                    <span>•</span>
                    <span>Всего получателей: {m.total_count}</span>
                  </div>
                </div>

                <div className="w-full md:w-64 shrink-0">
                  <ProgressBar
                    total={m.total_count}
                    success={m.success_count}
                    failed={m.failed_count}
                    showLabels={true}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-slate-400 text-sm">
            Пока нет созданных рассылок. Нажмите «Создать рассылку», чтобы начать.
          </div>
        )}
      </div>

      {/* Architecture badge */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 to-slate-800 p-6 text-white shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="space-y-1 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Архитектурный конвейер активен
            </span>
          </div>
          <p className="text-sm text-slate-300">
            Асинхронная веерная отправка: Celery Worker Pool + Redis Broker + Safe Idempotency Locks
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono bg-slate-800/80 px-4 py-2 rounded-xl border border-slate-700">
          <span className="text-emerald-400">● 20 msg/sec</span>
          <span className="text-slate-500">|</span>
          <span className="text-blue-400">Backoff 2^N</span>
          <span className="text-slate-500">|</span>
          <span className="text-amber-400">DLQ Ready</span>
        </div>
      </div>
    </div>
  );
};
