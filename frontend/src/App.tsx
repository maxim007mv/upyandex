import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { MailingsPage } from './pages/MailingsPage';
import { MailingCreatePage } from './pages/MailingCreatePage';
import { MailingDetailPage } from './pages/MailingDetailPage';
import { SubscribersPage } from './pages/SubscribersPage';
import { TemplatesPage } from './pages/TemplatesPage';
import { UnsubscribePage } from './pages/UnsubscribePage';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [selectedMailingId, setSelectedMailingId] = useState<string | null>(null);

  // Check for public unsubscribe route
  if (window.location.pathname.startsWith('/unsubscribe')) {
    return <UnsubscribePage />;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white text-sm">
        <div className="flex items-center space-x-3">
          <div className="w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          <span>Загрузка платформы...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const handleNavigate = (tab: string, detailId?: string) => {
    if (detailId) {
      setSelectedMailingId(detailId);
    }
    setCurrentTab(tab);
  };

  const getTitle = () => {
    switch (currentTab) {
      case 'dashboard':
        return 'Панель управления';
      case 'mailings':
        return 'Кампании и рассылки';
      case 'mailing-create':
        return 'Мастер создания рассылки';
      case 'mailing-detail':
        return 'Детализация кампании';
      case 'subscribers':
        return 'База подписчиков';
      case 'templates':
        return 'Шаблоны писем';
      default:
        return 'Управление рассылками';
    }
  };

  return (
    <Layout currentTab={currentTab} onSelectTab={handleNavigate} title={getTitle()}>
      {currentTab === 'dashboard' && <DashboardPage onNavigate={handleNavigate} />}
      {currentTab === 'mailings' && <MailingsPage onNavigate={handleNavigate} />}
      {currentTab === 'mailing-create' && <MailingCreatePage onNavigate={handleNavigate} />}
      {currentTab === 'mailing-detail' && selectedMailingId && (
        <MailingDetailPage mailingId={selectedMailingId} onNavigate={handleNavigate} />
      )}
      {currentTab === 'subscribers' && <SubscribersPage />}
      {currentTab === 'templates' && <TemplatesPage />}
    </Layout>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
