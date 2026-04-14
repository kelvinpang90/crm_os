import { useTranslation } from 'react-i18next';

const INTEGRATIONS = [
  {
    name: 'WhatsApp Business',
    icon: '💬',
    description: 'WhatsApp Cloud API 集成，自动接收和发送消息',
    envKeys: ['WHATSAPP_TOKEN', 'WHATSAPP_PHONE_ID', 'WHATSAPP_VERIFY_TOKEN'],
    status: 'configured',
  },
  {
    name: 'Email (IMAP/SMTP)',
    icon: '📧',
    description: '邮件收发集成，支持 IMAP 轮询和 SMTP 发送',
    envKeys: ['IMAP_HOST', 'SMTP_HOST', 'EMAIL_USER', 'EMAIL_PASSWORD'],
    status: 'configured',
  },
];

export default function IntegrationsPage() {
  const { t } = useTranslation('settings');

  return (
    <div>
      <h2 className="text-lg font-semibold text-text-primary mb-4">{t('integrations')}</h2>
      <div className="space-y-4">
        {INTEGRATIONS.map((integration) => (
          <div
            key={integration.name}
            className="bg-dark-card border border-dark-border rounded-xl p-4"
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">{integration.icon}</span>
              <div>
                <h3 className="text-sm font-semibold text-text-primary">{integration.name}</h3>
                <p className="text-xs text-text-muted">{integration.description}</p>
              </div>
              <span className="ml-auto text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-400">
                可用
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {integration.envKeys.map((key) => (
                <span key={key} className="text-xs px-2 py-1 bg-dark-hover rounded text-text-muted font-mono">
                  {key}
                </span>
              ))}
            </div>
            <p className="text-xs text-text-muted mt-2">
              通过环境变量 (.env) 配置。配置完成后重启服务生效。
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
