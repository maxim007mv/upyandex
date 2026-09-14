import React, { useEffect, useState } from 'react';
import {
  FileText,
  Plus,
  Eye,
  Edit2,
  Trash2,
  Code2,
  CheckCircle2,
  AlertCircle,
  Copy,
  Sparkles,
} from 'lucide-react';
import { templatesApi } from '../api/templates';
import { MessageTemplate, TemplatePreviewResponse } from '../types';
import { Modal } from '../components/Modal';

export const TemplatesPage: React.FC = () => {
  const [templates, setTemplates] = useState<MessageTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [activeTemplate, setActiveTemplate] = useState<MessageTemplate | null>(null);

  // Form
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [bodyContent, setBodyContent] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  // Preview state
  const [previewVariablesJson, setPreviewVariablesJson] = useState('{\n  "user": {\n    "full_name": "Иван Тестовый",\n    "email": "ivan.test@example.com"\n  },\n  "unsubscribe_url": "http://localhost:5173/unsubscribe?token=demo"\n}');
  const [previewResult, setPreviewResult] = useState<TemplatePreviewResponse | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const fetchTemplates = async () => {
    setIsLoading(true);
    try {
      const data = await templatesApi.list();
      setTemplates(data);
    } catch (err) {
      console.error('Failed to load templates', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleOpenCreate = () => {
    setTitle('');
    setSubject('');
    setBodyContent(`<h2>Здравствуйте, {{ user.full_name }}!</h2>
<p>Текст вашего информационного сообщения здесь...</p>
<hr />
<p style="font-size: 12px; color: #777;">
  <a href="{{ unsubscribe_url }}">Отписаться от рассылки</a>
</p>`);
    setFormError(null);
    setIsCreateOpen(true);
  };

  const handleOpenEdit = (tpl: MessageTemplate) => {
    setActiveTemplate(tpl);
    setTitle(tpl.title);
    setSubject(tpl.subject);
    setBodyContent(tpl.body_content);
    setFormError(null);
    setIsEditOpen(true);
  };

  const handleSaveCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      await templatesApi.create({
        title,
        subject,
        body_content: bodyContent,
      });
      setIsCreateOpen(false);
      fetchTemplates();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Ошибка сохранения шаблона');
    }
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeTemplate) return;
    setFormError(null);
    try {
      await templatesApi.update(activeTemplate.id, {
        title,
        subject,
        body_content: bodyContent,
      });
      setIsEditOpen(false);
      fetchTemplates();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Ошибка обновления шаблона');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Удалить этот шаблон?')) return;
    try {
      await templatesApi.delete(id);
      fetchTemplates();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка при удалении шаблона');
    }
  };

  const handleOpenPreview = async (tpl: MessageTemplate) => {
    setActiveTemplate(tpl);
    setPreviewError(null);
    setIsPreviewOpen(true);

    // Initial render
    try {
      const vars = JSON.parse(previewVariablesJson);
      const res = await templatesApi.preview(tpl.id, vars);
      setPreviewResult(res);
    } catch (err: any) {
      setPreviewError('Не удалось выполнить рендер предпросмотра');
    }
  };

  const handleUpdatePreview = async () => {
    if (!activeTemplate) return;
    setPreviewError(null);
    try {
      const parsed = JSON.parse(previewVariablesJson);
      const res = await templatesApi.preview(activeTemplate.id, parsed);
      setPreviewResult(res);
    } catch (err: any) {
      setPreviewError(err.message || 'Ошибка парсинга JSON переменных');
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Шаблоны писем</h1>
          <p className="text-sm text-slate-500 mt-1">
            Jinja2-разметка с автоматической валидацией синтаксиса и подстановкой переменных
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="flex items-center px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 shadow-sm shadow-brand-500/20 transition-all"
        >
          <Plus className="w-4 h-4 mr-2" />
          Новый шаблон
        </button>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((tpl) => (
          <div
            key={tpl.id}
            className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-bold text-base text-slate-900 leading-snug">{tpl.title}</h3>
                <span className="shrink-0 p-1.5 bg-slate-100 rounded-lg text-slate-500">
                  <FileText className="w-4 h-4" />
                </span>
              </div>

              <div className="space-y-2 mt-3">
                <div className="text-xs">
                  <span className="font-semibold text-slate-500 uppercase text-[10px]">Тема:</span>
                  <p className="text-slate-800 font-medium truncate">{tpl.subject}</p>
                </div>

                <div className="text-xs">
                  <span className="font-semibold text-slate-500 uppercase text-[10px]">
                    Переменные:
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {tpl.required_variables && tpl.required_variables.length > 0 ? (
                      tpl.required_variables.map((v) => (
                        <span
                          key={v}
                          className="px-2 py-0.5 rounded text-[11px] font-mono bg-purple-50 text-purple-700 border border-purple-200"
                        >
                          {`{{ ${v} }}`}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-400 text-xs">Нет переменных</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-5 mt-5 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                {new Date(tpl.created_at).toLocaleDateString('ru-RU')}
              </span>
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => handleOpenPreview(tpl)}
                  className="flex items-center text-xs font-semibold px-2.5 py-1.5 text-brand-600 bg-brand-50 hover:bg-brand-100 rounded-lg transition-colors"
                >
                  <Eye className="w-3.5 h-3.5 mr-1" />
                  Превью
                </button>
                <button
                  onClick={() => handleOpenEdit(tpl)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(tpl.id)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Создать шаблон письма"
        maxWidth="2xl"
      >
        <form onSubmit={handleSaveCreate} className="space-y-4">
          {formError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Название шаблона *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Новостной дайджест"
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Тема письма (Subject) *
            </label>
            <input
              type="text"
              required
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Привет, {{ user.full_name }}! Специальное предложение"
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono text-xs"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1 flex items-center justify-between">
              <span>Тело письма (HTML / Jinja2) *</span>
              <span className="text-[11px] text-slate-400 font-normal lowercase">
                доступны: <code>{'{{ user.full_name }}'}</code>, <code>{'{{ unsubscribe_url }}'}</code>
              </span>
            </label>
            <textarea
              required
              rows={10}
              value={bodyContent}
              onChange={(e) => setBodyContent(e.target.value)}
              className="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="flex justify-end space-x-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsCreateOpen(false)}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-sm"
            >
              Создать шаблон
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Редактировать шаблон"
        maxWidth="2xl"
      >
        <form onSubmit={handleSaveEdit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Название шаблона *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Тема письма *
            </label>
            <input
              type="text"
              required
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full px-3.5 py-2 text-sm font-mono text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Тело письма (HTML / Jinja2) *
            </label>
            <textarea
              required
              rows={10}
              value={bodyContent}
              onChange={(e) => setBodyContent(e.target.value)}
              className="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="flex justify-end space-x-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsEditOpen(false)}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-sm"
            >
              Сохранить изменения
            </button>
          </div>
        </form>
      </Modal>

      {/* Live Preview Modal */}
      <Modal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        title={`Предпросмотр: ${activeTemplate?.title || ''}`}
        maxWidth="3xl"
      >
        <div className="space-y-4">
          {previewError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{previewError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Variables editor */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700 uppercase flex items-center justify-between">
                <span>Тестовые переменные (JSON)</span>
                <button
                  type="button"
                  onClick={handleUpdatePreview}
                  className="text-brand-600 hover:text-brand-700 font-bold lowercase text-[11px] flex items-center"
                >
                  <Sparkles className="w-3 h-3 mr-1" />
                  Перерендерить
                </button>
              </label>
              <textarea
                rows={12}
                value={previewVariablesJson}
                onChange={(e) => setPreviewVariablesJson(e.target.value)}
                className="w-full px-3 py-2 text-xs font-mono bg-slate-900 text-emerald-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            {/* Rendered result */}
            <div className="space-y-2 flex flex-col">
              <label className="block text-xs font-semibold text-slate-700 uppercase">
                Результат рендера
              </label>
              <div className="flex-1 bg-white border border-slate-200 rounded-xl p-4 shadow-inner overflow-y-auto max-h-[300px]">
                <div className="pb-3 mb-3 border-b border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    Тема письма:
                  </span>
                  <p className="text-xs font-bold text-slate-900 mt-0.5">
                    {previewResult?.rendered_subject || '—'}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Тело письма:
                  </span>
                  <div
                    className="text-xs text-slate-700 prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{
                      __html: previewResult?.rendered_body || '<p class="text-slate-400">Пусто</p>',
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              onClick={() => setIsPreviewOpen(false)}
              className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl"
            >
              Закрыть
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
