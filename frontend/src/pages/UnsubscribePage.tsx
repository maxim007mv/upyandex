import React, { useState } from 'react';
import { Mail, CheckCircle2, AlertCircle } from 'lucide-react';
import axios from 'axios';

export const UnsubscribePage: React.FC = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');

  const [status, setStatus] = useState<'initial' | 'loading' | 'success' | 'error'>('initial');
  const [message, setMessage] = useState('');

  const handleConfirm = async () => {
    if (!token) {
      setStatus('error');
      setMessage('Токен отписки не найден в ссылке.');
      return;
    }

    setStatus('loading');
    try {
      const res = await axios.post('/api/v1/subscribers/unsubscribe-by-token', {
        token,
      });
      setStatus('success');
      setMessage(res.data.message || 'Вы успешно отписаны от информационных рассылок.');
    } catch (err: any) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'Не удалось выполнить отписку. Ссылка устарела.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center items-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 border border-slate-200 text-center">
        <div className="w-12 h-12 bg-slate-100 text-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Mail className="w-6 h-6" />
        </div>

        <h1 className="text-xl font-bold text-slate-900 mb-2">Отписка от рассылки</h1>
        <p className="text-xs text-slate-500 mb-6">
          Вы перешли по персональной ссылке отказа от получения уведомлений.
        </p>

        {status === 'initial' && (
          <div className="space-y-4">
            <p className="text-sm text-slate-700">
              Вы уверены, что хотите отписаться от всех будущих рассылок?
            </p>
            <button
              onClick={handleConfirm}
              className="w-full py-2.5 px-4 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-xl shadow transition-colors"
            >
              Да, подтверждаю отписку
            </button>
          </div>
        )}

        {status === 'loading' && (
          <div className="text-sm text-slate-500 py-4">Обработка запроса...</div>
        )}

        {status === 'success' && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex flex-col items-center space-y-2">
            <CheckCircle2 className="w-6 h-6 text-emerald-600" />
            <span className="font-semibold text-sm">Успешно отписаны</span>
            <p>{message}</p>
          </div>
        )}

        {status === 'error' && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex flex-col items-center space-y-2">
            <AlertCircle className="w-6 h-6 text-rose-600" />
            <span className="font-semibold text-sm">Ошибка</span>
            <p>{message}</p>
          </div>
        )}
      </div>
    </div>
  );
};
