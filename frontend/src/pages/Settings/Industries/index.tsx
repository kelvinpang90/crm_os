import { useState } from 'react';
import { useTranslation } from 'react-i18next';

const DEFAULT_INDUSTRIES = [
  '互联网/IT', '金融', '房地产', '教育', '医疗健康',
  '制造业', '零售/电商', '物流', '餐饮', '咨询服务',
  '广告/传媒', '法律', '农业', '能源', '其他',
];

export default function IndustriesPage() {
  const { t } = useTranslation('settings');
  const tc = useTranslation().t;
  const [industries, setIndustries] = useState(DEFAULT_INDUSTRIES);
  const [newIndustry, setNewIndustry] = useState('');

  const handleAdd = () => {
    const val = newIndustry.trim();
    if (!val || industries.includes(val)) return;
    setIndustries([...industries, val]);
    setNewIndustry('');
  };

  const handleRemove = (industry: string) => {
    setIndustries(industries.filter((i) => i !== industry));
  };

  return (
    <div>
      <h2 className="text-lg font-semibold text-text-primary mb-4">{t('industries')}</h2>

      <div className="bg-dark-card border border-dark-border rounded-xl p-4">
        <div className="flex gap-2 mb-4">
          <input
            className="input flex-1 text-sm"
            placeholder="添加行业..."
            value={newIndustry}
            onChange={(e) => setNewIndustry(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          />
          <button onClick={handleAdd} className="btn-primary text-sm px-4 py-2">
            添加
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {industries.map((industry) => (
            <span
              key={industry}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-dark-hover rounded-lg text-sm text-text-secondary"
            >
              {industry}
              <button
                onClick={() => handleRemove(industry)}
                className="text-text-muted hover:text-red-400 text-xs"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      <p className="text-xs text-text-muted mt-3">
        行业配置用于客户的行业分类。添加或移除行业将影响新建客户时的可选项。
      </p>
    </div>
  );
}
