import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Send,
  FileText,
  Users,
  Calendar,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { templatesApi } from '../api/templates';
import { subscribersApi } from '../api/subscribers';
import { mailingsApi } from '../api/mailings';
import { MessageTemplate } from '../types';

interface MailingCreatePageProps {
  onNavigate: (tab: string, detailId?: string) => void;
}

export const MailingCreatePage: React.FC<MailingCreatePageProps> = ({ onNavigate }) => {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  const [templates, setTemplates] = useState<MessageTemplate[]>([]);

  // Audience
  const [targetType, setTargetType] = useState<'all' | 'tags'>('all');
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [estimatedAudience, setEstimatedAudience] = useState<number>(0);

  // Schedule
  const [dispatchType, setDispatchType] = useState<'now' | 'schedule'>('now');
  const [scheduleDateTime, setScheduleDateTime] = useState('');

  useEffect(() => {
    const loadInitial = async () => {
      try {
        const [tplList, tags] = await Promise.all([
          templatesApi.list(),
          subscribersApi.getTags(),
        ]);
        setTemplates(tplList);
        if (tplList.length > 0) setSelectedTemplateId(tplList[0].id);
        setAvailableTags(tags);
      } catch (err) {
        console.error(err);
      }
    };
    loadInitial();
  }, []);

  // Recalculate audience estimation
  useEffect(() => {
    const calcAudience = async () => {
      try {
        const params: any = { is_active: true, size: 1 };
        if (targetType === 'tags' && selectedTags.length > 0) {
          // fetch count for tag
          params.tag = selectedTags[0]; // representative estimation
        }
        const data = await subscribersApi.list(params);
        setEstimatedAudience(data.total);
      } catch (err) {
        console.error(err);
      }
    };
    calcAudience();
  }, [targetType, selectedTags]);

  const handleTagToggle = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleNext = () => {
    setError(null);
    if (step === 1) {
      if (!title.trim()) {
        setError('Пожалуйста, введите название рассылки');
        return;
      }
    } else if (step === 2) {
      if (!selectedTemplateId) {
        setError('Пожалуйста, выберите шаблон письма');
        return;
      }
    }
    setStep((s) => Math.min(4, s + 1));
  };

  const handlePrev = () => {
    setError(null);
    setStep((s) => Math.max(1, s - 1));
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const recipientFilter: Record<string, any> = { is_active: true };
      if (targetType === 'tags' && selectedTags.length > 0) {
        recipientFilter.tags = selectedTags;
      }

      let scheduledAtIso: string | null = null;
      if (dispatchType === 'schedule' && scheduleDateTime) {
        scheduledAtIso = new Date(scheduleDateTime).toISOString();
      }

      const created = await mailingsApi.create({
        title,
        description: description || undefined,
        template_id: selectedTemplateId,
        recipient_filter: recipientFilter,
        scheduled_at: scheduledAtIso,
      });

      // Navigate to detail page
      onNavigate('mailing-detail', created.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при создании рассылки');
      setIsLoading(false);
    }
  };

  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <button
        onClick={() => onNavigate('mailings')}
        className="flex items-center text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1.5" />
        Вернуться к списку рассылок
      </button>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Мастер создания рассылки
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Пошаговая настройка аудитории, параметров отправки и расписания
        </p>
      </div>

      {/* Steps Indicator */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
        {[
          { num: 1, label: 'Параметры', icon: FileText },
          { num: 2, label: 'Шаблон', icon: Sparkles },
          { num: 3, label: 'Аудитория', icon: Users },
          { num: 4, label: 'Запуск', icon: Send },
        ].map((st) => {
          const Icon = st.icon;
          const isDone = step > st.num;
          const isCurrent = step === st.num;
          return (
            <div key={st.num} className="flex items-center space-x-2">
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold transition-colors ${
                  isDone
                    ? 'bg-emerald-500 text-white'
                    : isCurrent
                    ? 'bg-brand-600 text-white shadow-sm shadow-brand-500/30'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                {isDone ? <Check className="w-4 h-4" /> : st.num}
              </div>
              <span
                className={`text-xs font-semibold hidden sm:inline ${
                  isCurrent ? 'text-slate-900' : 'text-slate-400'
                }`}
              >
                {st.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Step Content */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm min-h-[350px]">
        {/* Step 1 */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-base font-bold text-slate-900">
              Шаг 1: Основные сведения о кампании
            </h2>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Название кампании *
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Релиз платформы v1.0.0 — анонс для подписчиков"
                className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Описание / примечания (необязательно)
              </label>
              <textarea
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Внутренняя заметка о цели рассылки и ожидаемом отклике"
                className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>
        )}

        {/* Step 2 */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-base font-bold text-slate-900">
              Шаг 2: Выберите макет письма
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map((tpl) => (
                <div
                  key={tpl.id}
                  onClick={() => setSelectedTemplateId(tpl.id)}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                    selectedTemplateId === tpl.id
                      ? 'border-brand-600 bg-brand-50/30 shadow-sm'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-bold text-sm text-slate-900">{tpl.title}</h4>
                    {selectedTemplateId === tpl.id && (
                      <span className="w-5 h-5 rounded-full bg-brand-600 text-white flex items-center justify-center text-[10px]">
                        ✓
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 truncate mb-2">Тема: {tpl.subject}</p>
                  <div className="flex flex-wrap gap-1">
                    {tpl.required_variables.slice(0, 3).map((v) => (
                      <span
                        key={v}
                        className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono"
                      >
                        {v}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 3 */}
        {step === 3 && (
          <div className="space-y-5">
            <h2 className="text-base font-bold text-slate-900">
              Шаг 3: Сегментация аудитории получателей
            </h2>
            <div className="space-y-3">
              <label
                onClick={() => setTargetType('all')}
                className={`flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  targetType === 'all'
                    ? 'border-brand-600 bg-brand-50/30'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <input
                  type="radio"
                  name="targetType"
                  checked={targetType === 'all'}
                  onChange={() => setTargetType('all')}
                  className="mt-0.5 text-brand-600 focus:ring-brand-500"
                />
                <div className="ml-3">
                  <span className="block text-sm font-bold text-slate-900">
                    Все активные подписчики (Opt-in)
                  </span>
                  <span className="block text-xs text-slate-500 mt-0.5">
                    Отправить сообщение всем контактам, подтвердившим согласие на рассылку
                  </span>
                </div>
              </label>

              <label
                onClick={() => setTargetType('tags')}
                className={`flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  targetType === 'tags'
                    ? 'border-brand-600 bg-brand-50/30'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <input
                  type="radio"
                  name="targetType"
                  checked={targetType === 'tags'}
                  onChange={() => setTargetType('tags')}
                  className="mt-0.5 text-brand-600 focus:ring-brand-500"
                />
                <div className="ml-3">
                  <span className="block text-sm font-bold text-slate-900">
                    Сегментация по тегам
                  </span>
                  <span className="block text-xs text-slate-500 mt-0.5">
                    Отправить только адресатам с определенными интересами или категориями
                  </span>
                </div>
              </label>
            </div>

            {targetType === 'tags' && (
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <p className="text-xs font-semibold text-slate-700 uppercase">
                  Выберите целевые теги:
                </p>
                <div className="flex flex-wrap gap-2">
                  {availableTags.map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => handleTagToggle(tag)}
                      className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors ${
                        selectedTags.includes(tag)
                          ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                          : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-100'
                      }`}
                    >
                      #{tag}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center justify-between">
              <span>Целевых получателей в базе:</span>
              <strong className="text-sm font-bold">{estimatedAudience} адресатов</strong>
            </div>
          </div>
        )}

        {/* Step 4 */}
        {step === 4 && (
          <div className="space-y-5">
            <h2 className="text-base font-bold text-slate-900">
              Шаг 4: Расписание и подтверждение запуска
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label
                onClick={() => setDispatchType('now')}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  dispatchType === 'now'
                    ? 'border-brand-600 bg-brand-50/30'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <input
                  type="radio"
                  name="dispatchType"
                  checked={dispatchType === 'now'}
                  onChange={() => setDispatchType('now')}
                  className="text-brand-600 focus:ring-brand-500"
                />
                <span className="ml-2 text-sm font-bold text-slate-900">
                  Немедленный запуск
                </span>
                <p className="text-xs text-slate-500 mt-1">
                  Пакеты задач будут сформированы и поставлены в Celery очередь сразу после создания
                </p>
              </label>

              <label
                onClick={() => setDispatchType('schedule')}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  dispatchType === 'schedule'
                    ? 'border-brand-600 bg-brand-50/30'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <input
                  type="radio"
                  name="dispatchType"
                  checked={dispatchType === 'schedule'}
                  onChange={() => setDispatchType('schedule')}
                  className="text-brand-600 focus:ring-brand-500"
                />
                <span className="ml-2 text-sm font-bold text-slate-900">
                  Запланировать по времени
                </span>
                <p className="text-xs text-slate-500 mt-1">
                  Celery Beat запустит рассылку точно в указанное время
                </p>
              </label>
            </div>

            {dispatchType === 'schedule' && (
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <label className="block text-xs font-semibold text-slate-700 uppercase">
                  Дата и время отправки
                </label>
                <input
                  type="datetime-local"
                  required
                  value={scheduleDateTime}
                  onChange={(e) => setScheduleDateTime(e.target.value)}
                  className="px-3.5 py-2 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            )}

            {/* Summary card */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-2">
              <p className="font-bold text-slate-800 text-sm">Сводные параметры кампании:</p>
              <div className="grid grid-cols-2 gap-2 text-slate-600">
                <div>
                  <span className="text-slate-400">Название:</span> {title}
                </div>
                <div>
                  <span className="text-slate-400">Шаблон:</span> {selectedTemplate?.title}
                </div>
                <div>
                  <span className="text-slate-400">Сегмент:</span>{' '}
                  {targetType === 'all' ? 'Все активные' : selectedTags.join(', ') || 'Без тегов'}
                </div>
                <div>
                  <span className="text-slate-400">Режим запуска:</span>{' '}
                  {dispatchType === 'now' ? 'Немедленно' : scheduleDateTime || 'По времени'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Control Buttons */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          disabled={step === 1}
          onClick={handlePrev}
          className="flex items-center px-4 py-2.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 disabled:opacity-40 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          Назад
        </button>

        {step < 4 ? (
          <button
            type="button"
            onClick={handleNext}
            className="flex items-center px-5 py-2.5 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-sm shadow-brand-500/20 transition-all"
          >
            Далее
            <ArrowRight className="w-4 h-4 ml-1.5" />
          </button>
        ) : (
          <button
            type="button"
            disabled={isLoading}
            onClick={handleSubmit}
            className="flex items-center px-6 py-2.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm shadow-emerald-500/20 transition-all disabled:opacity-50"
          >
            <Send className="w-4 h-4 mr-2" />
            {isLoading
              ? 'Создание...'
              : dispatchType === 'now'
              ? 'Создать и запустить сейчас'
              : 'Запланировать кампанию'}
          </button>
        )}
      </div>
    </div>
  );
};
