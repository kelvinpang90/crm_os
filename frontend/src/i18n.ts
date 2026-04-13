import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import zhCommon from '@/locales/zh/common.json';
import zhDashboard from '@/locales/zh/dashboard.json';
import zhContacts from '@/locales/zh/contacts.json';
import zhTasks from '@/locales/zh/tasks.json';
import zhInbox from '@/locales/zh/inbox.json';
import zhSettings from '@/locales/zh/settings.json';

import enCommon from '@/locales/en/common.json';
import enDashboard from '@/locales/en/dashboard.json';
import enContacts from '@/locales/en/contacts.json';
import enTasks from '@/locales/en/tasks.json';
import enInbox from '@/locales/en/inbox.json';
import enSettings from '@/locales/en/settings.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      zh: {
        common: zhCommon,
        dashboard: zhDashboard,
        contacts: zhContacts,
        tasks: zhTasks,
        inbox: zhInbox,
        settings: zhSettings,
      },
      en: {
        common: enCommon,
        dashboard: enDashboard,
        contacts: enContacts,
        tasks: enTasks,
        inbox: enInbox,
        settings: enSettings,
      },
    },
    fallbackLng: 'zh',
    defaultNS: 'common',
    ns: ['common', 'dashboard', 'contacts', 'tasks', 'inbox', 'settings'],
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'language',
    },
  });

export default i18n;
