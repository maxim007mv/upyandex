import React, { useEffect, useState } from 'react';
import {
  Users,
  UserPlus,
  Upload,
  Search,
  Tag,
  CheckCircle2,
  XCircle,
  Trash2,
  Edit2,
  RefreshCw,
  AlertCircle,
  FileText,
} from 'lucide-react';
import { subscribersApi } from '../api/subscribers';
import { Subscriber, BatchImportResult } from '../types';
import { Modal } from '../components/Modal';

export const SubscribersPage: React.FC = () => {
  const [subscribers, setSubscribers] = useState<Subscriber[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(15);
  const [search, setSearch] = useState('');
  const [selectedTag, setSelectedTag] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [allTags, setAllTags] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Modals
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [editingSub, setEditingSub] = useState<Subscriber | null>(null);

  // Form states
  const [formEmail, setFormEmail] = useState('');
  const [formName, setFormName] = useState('');
  const [formPhone, setFormPhone] = useState('');
  const [formTags, setFormTags] = useState('');
  const [formActive, setFormActive] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

  // Import state
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importResult, setImportResult] = useState<BatchImportResult | null>(null);

  const fetchSubscribers = async () => {
    setIsLoading(true);
    try {
      const is_active_val =
        activeFilter === 'active' ? true : activeFilter === 'inactive' ? false : undefined;

      const data = await subscribersApi.list({
        page,
        size,
        search: search || undefined,
        tag: selectedTag || undefined,
        is_active: is_active_val,
      });
      setSubscribers(data.items);
      setTotal(data.total);

      // fetch tags
      const tags = await subscribersApi.getTags();
      setAllTags(tags);
    } catch (err) {
      console.error('Failed to load subscribers', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscribers();
  }, [page, search, selectedTag, activeFilter]);

  const handleOpenAdd = () => {
    setFormEmail('');
    setFormName('');
    setFormPhone('');
    setFormTags('');
    setFormActive(true);
    setFormError(null);
    setIsAddOpen(true);
  };

  const handleOpenEdit = (sub: Subscriber) => {
    setEditingSub(sub);
    setFormEmail(sub.email);
    setFormName(sub.full_name || '');
    setFormPhone(sub.phone || '');
    setFormTags((sub.tags_attributes || []).join(', '));
    setFormActive(sub.is_active);
    setFormError(null);
    setIsEditOpen(true);
  };

  const handleSaveAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      const tagsList = formTags
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      await subscribersApi.create({
        email: formEmail,
        full_name: formName || undefined,
        phone: formPhone || undefined,
        tags_attributes: tagsList,
        is_active: formActive,
      });
      setIsAddOpen(false);
      fetchSubscribers();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Ошибка при сохранении');
    }
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSub) return;
    setFormError(null);
    try {
      const tagsList = formTags
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      await subscribersApi.update(editingSub.id, {
        email: formEmail,
        full_name: formName || undefined,
        phone: formPhone || undefined,
        tags_attributes: tagsList,
        is_active: formActive,
      });
      setIsEditOpen(false);
      fetchSubscribers();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Ошибка при обновлении');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Вы действительно хотите удалить этого подписчика?')) return;
    try {
      await subscribersApi.delete(id);
      fetchSubscribers();
    } catch (err) {
      alert('Ошибка при удалении');
    }
  };

  const handleToggleUnsubscribe = async (sub: Subscriber) => {
    try {
      if (sub.is_active) {
        await subscribersApi.unsubscribe(sub.id);
      } else {
        await subscribersApi.update(sub.id, { is_active: true });
      }
      fetchSubscribers();
    } catch (err) {
      alert('Ошибка при изменении статуса');
    }
  };

  const handleImportCsv = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;
    setImportLoading(true);
    setImportResult(null);
    try {
      const result = await subscribersApi.importCsv(importFile);
      setImportResult(result);
      fetchSubscribers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка при импорте CSV');
    } finally {
      setImportLoading(false);
    }
  };

  const totalPages = Math.ceil(total / size) || 1;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">База подписчиков</h1>
          <p className="text-sm text-slate-500 mt-1">
            Сегментация по тегам, контактным данным и истории активности
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              setImportResult(null);
              setImportFile(null);
              setIsImportOpen(true);
            }}
            className="flex items-center px-4 py-2.5 rounded-xl text-sm font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <Upload className="w-4 h-4 mr-2 text-slate-500" />
            Импорт CSV
          </button>
          <button
            onClick={handleOpenAdd}
            className="flex items-center px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 shadow-sm shadow-brand-500/20 transition-all"
          >
            <UserPlus className="w-4 h-4 mr-2" />
            Добавить подписчика
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Поиск по email, имени или телефону..."
              className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
            />
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <select
              value={selectedTag}
              onChange={(e) => {
                setSelectedTag(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-700 w-full sm:w-44"
            >
              <option value="">Все теги</option>
              {allTags.map((t) => (
                <option key={t} value={t}>
                  🏷️ {t}
                </option>
              ))}
            </select>

            <select
              value={activeFilter}
              onChange={(e) => {
                setActiveFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-700 w-full sm:w-40"
            >
              <option value="all">Все статусы</option>
              <option value="active">Активные</option>
              <option value="inactive">Отписавшиеся</option>
            </select>

            <button
              onClick={fetchSubscribers}
              className="p-2 text-slate-500 hover:text-slate-800 rounded-xl hover:bg-slate-100 border border-slate-200"
              title="Обновить"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Tag pills */}
        {allTags.length > 0 && (
          <div className="flex items-center flex-wrap gap-1.5 pt-2 border-t border-slate-100">
            <span className="text-xs text-slate-400 font-medium mr-1">Быстрые теги:</span>
            {allTags.slice(0, 8).map((tag) => (
              <button
                key={tag}
                onClick={() => {
                  setSelectedTag(selectedTag === tag ? '' : tag);
                  setPage(1);
                }}
                className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                  selectedTag === tag
                    ? 'bg-brand-50 border-brand-300 text-brand-700 font-semibold'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                }`}
              >
                #{tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3.5">Получатель</th>
                <th className="px-6 py-3.5">Телефон</th>
                <th className="px-6 py-3.5">Теги сегментации</th>
                <th className="px-6 py-3.5">Статус</th>
                <th className="px-6 py-3.5">Дата добавления</th>
                <th className="px-6 py-3.5 text-right">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {subscribers.length > 0 ? (
                subscribers.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900">{sub.full_name || '—'}</div>
                      <div className="text-xs text-slate-500 font-mono">{sub.email}</div>
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-slate-600">
                      {sub.phone || '—'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {sub.tags_attributes && sub.tags_attributes.length > 0 ? (
                          sub.tags_attributes.map((t) => (
                            <span
                              key={t}
                              className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200"
                            >
                              #{t}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {sub.is_active ? (
                        <span className="inline-flex items-center text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-500" />
                          Активен
                        </span>
                      ) : (
                        <span className="inline-flex items-center text-xs font-medium text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
                          <XCircle className="w-3.5 h-3.5 mr-1 text-rose-500" />
                          Отписан
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {new Date(sub.created_at).toLocaleDateString('ru-RU')}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-1">
                        <button
                          onClick={() => handleToggleUnsubscribe(sub)}
                          title={sub.is_active ? 'Отписать' : 'Активировать'}
                          className={`p-1.5 rounded-lg border text-xs transition-colors ${
                            sub.is_active
                              ? 'text-amber-600 border-amber-200 hover:bg-amber-50'
                              : 'text-emerald-600 border-emerald-200 hover:bg-emerald-50'
                          }`}
                        >
                          {sub.is_active ? 'Отписать' : 'Включить'}
                        </button>
                        <button
                          onClick={() => handleOpenEdit(sub)}
                          title="Редактировать"
                          className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(sub.id)}
                          title="Удалить"
                          className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-400 text-sm">
                    Подписчики не найдены. Измените параметры фильтрации или импортируйте контакты.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>
            Показано {subscribers.length} из {total} подписчиков
          </span>
          <div className="flex items-center space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
            >
              Назад
            </button>
            <span className="font-semibold text-slate-700">
              {page} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
            >
              Вперед
            </button>
          </div>
        </div>
      </div>

      {/* Add Modal */}
      <Modal isOpen={isAddOpen} onClose={() => setIsAddOpen(false)} title="Новый подписчик">
        <form onSubmit={handleSaveAdd} className="space-y-4">
          {formError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Email *
            </label>
            <input
              type="email"
              required
              value={formEmail}
              onChange={(e) => setFormEmail(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="user@example.com"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              ФИО
            </label>
            <input
              type="text"
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Иван Иванов"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Телефон
            </label>
            <input
              type="text"
              value={formPhone}
              onChange={(e) => setFormPhone(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="+79991234567"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Теги (через запятую)
            </label>
            <input
              type="text"
              value={formTags}
              onChange={(e) => setFormTags(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="vip, marketing, developers"
            />
          </div>
          <div className="flex items-center space-x-2 pt-2">
            <input
              type="checkbox"
              id="formActiveCheck"
              checked={formActive}
              onChange={(e) => setFormActive(e.target.checked)}
              className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            <label htmlFor="formActiveCheck" className="text-xs font-medium text-slate-700">
              Подписка активна (Opt-in)
            </label>
          </div>

          <div className="flex justify-end space-x-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsAddOpen(false)}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-sm"
            >
              Сохранить
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal isOpen={isEditOpen} onClose={() => setIsEditOpen(false)} title="Редактировать подписчика">
        <form onSubmit={handleSaveEdit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Email *
            </label>
            <input
              type="email"
              required
              value={formEmail}
              onChange={(e) => setFormEmail(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              ФИО
            </label>
            <input
              type="text"
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Телефон
            </label>
            <input
              type="text"
              value={formPhone}
              onChange={(e) => setFormPhone(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Теги (через запятую)
            </label>
            <input
              type="text"
              value={formTags}
              onChange={(e) => setFormTags(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="flex items-center space-x-2 pt-2">
            <input
              type="checkbox"
              id="editActiveCheck"
              checked={formActive}
              onChange={(e) => setFormActive(e.target.checked)}
              className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            <label htmlFor="editActiveCheck" className="text-xs font-medium text-slate-700">
              Подписка активна
            </label>
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
              Обновить
            </button>
          </div>
        </form>
      </Modal>

      {/* CSV Import Modal */}
      <Modal isOpen={isImportOpen} onClose={() => setIsImportOpen(false)} title="Импорт подписчиков из CSV">
        <form onSubmit={handleImportCsv} className="space-y-4">
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 space-y-1.5">
            <p className="font-semibold text-slate-800">Формат файла CSV:</p>
            <p className="font-mono bg-white p-2 rounded border border-slate-200 text-[11px] text-slate-800">
              email,full_name,phone,tags<br />
              alex@company.com,Алексей Иванов,+79990001122,vip;marketing<br />
              dmitry@mail.ru,Дмитрий,,developers
            </p>
            <p className="text-[11px] text-slate-500">
              * Заголовок <code>email</code> обязателен. Кодировка UTF-8 или CP1251.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Выберите CSV файл
            </label>
            <input
              type="file"
              accept=".csv,text/csv"
              required
              onChange={(e) => setImportFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
            />
          </div>

          {importResult && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs space-y-1">
              <p className="font-semibold text-emerald-800 flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-1.5 text-emerald-600" />
                Импорт успешно выполнен:
              </p>
              <ul className="list-disc list-inside text-emerald-700">
                <li>Добавлено новых: {importResult.added}</li>
                <li>Обновлено существующих: {importResult.updated}</li>
                {importResult.errors.length > 0 && (
                  <li className="text-rose-700">
                    Ошибок в строках: {importResult.errors.length}
                  </li>
                )}
              </ul>
            </div>
          )}

          <div className="flex justify-end space-x-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsImportOpen(false)}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
            >
              Закрыть
            </button>
            <button
              type="submit"
              disabled={importLoading || !importFile}
              className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-sm disabled:opacity-50"
            >
              {importLoading ? 'Загрузка...' : 'Загрузить и обработать'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
