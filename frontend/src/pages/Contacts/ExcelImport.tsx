import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { contactsApi } from '@/services/contacts';
import * as XLSX from 'xlsx';

interface ParsedRow {
  [key: string]: string;
}

export default function ExcelImport() {
  const { t } = useTranslation('contacts');
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [rows, setRows] = useState<ParsedRow[]>([]);
  const [headers, setHeaders] = useState<string[]>([]);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleDownloadTemplate = async () => {
    try {
      const res = await contactsApi.downloadTemplate();
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'contact_import_template.xlsx';
      a.click();
      URL.revokeObjectURL(url);
    } catch { /* ignore */ }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > 10 * 1024 * 1024) {
      alert('文件大小不能超过 10MB');
      return;
    }
    setFile(f);
    setResult(null);

    const reader = new FileReader();
    reader.onload = (ev) => {
      const data = new Uint8Array(ev.target?.result as ArrayBuffer);
      const wb = XLSX.read(data, { type: 'array' });
      const ws = wb.Sheets[wb.SheetNames[0]];
      const json = XLSX.utils.sheet_to_json<ParsedRow>(ws, { defval: '' });
      if (json.length > 0) {
        setHeaders(Object.keys(json[0]));
        setRows(json);
      }
    };
    reader.readAsArrayBuffer(f);
  };

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    try {
      const res = await contactsApi.importContacts(file);
      setResult(res.data.data);
    } catch { /* ignore */ }
    setImporting(false);
  };

  const errorRows = rows.filter((r) => !(r['姓名'] || r['name'] || '').toString().trim());

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <button onClick={handleDownloadTemplate} className="btn-secondary text-sm">
          {t('downloadTemplate')}
        </button>
        <button onClick={() => fileRef.current?.click()} className="btn-primary text-sm">
          {t('uploadFile')}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".xlsx,.xls"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {file && <p className="text-sm text-text-secondary">{file.name}</p>}

      {rows.length > 0 && (
        <>
          <div className="text-sm text-text-secondary">
            共 {rows.length} 行，预计新增 {rows.filter((r) => !(r['客户ID（更新时填写）'] || r['id'] || '').toString().trim()).length} 条，
            更新 {rows.filter((r) => (r['客户ID（更新时填写）'] || r['id'] || '').toString().trim()).length} 条，
            {errorRows.length > 0 && <span className="text-red-400">{errorRows.length} 行有问题</span>}
          </div>

          <div className="overflow-x-auto max-h-80 border border-dark-border rounded-lg">
            <table className="w-full text-xs">
              <thead className="bg-dark-hover sticky top-0">
                <tr>
                  <th className="px-2 py-1 text-left text-text-muted">#</th>
                  {headers.slice(0, 6).map((h) => (
                    <th key={h} className="px-2 py-1 text-left text-text-muted">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 50).map((row, i) => {
                  const hasError = !(row['姓名'] || row['name'] || '').toString().trim();
                  return (
                    <tr key={i} className={hasError ? 'bg-red-500/10' : 'hover:bg-dark-hover'}>
                      <td className="px-2 py-1 text-text-muted">{i + 1}</td>
                      {headers.slice(0, 6).map((h) => (
                        <td key={h} className="px-2 py-1 text-text-secondary truncate max-w-[120px]">
                          {String(row[h] || '')}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <button onClick={handleImport} disabled={importing} className="btn-primary">
            {importing ? '...' : t('confirmImport')}
          </button>
        </>
      )}

      {result && (
        <div className="card p-4 space-y-1 text-sm">
          <h4 className="font-semibold text-text-primary">{t('importResult')}</h4>
          <p className="text-text-secondary">{t('totalRows')}: {result.total}</p>
          <p className="text-green-400">{t('inserted')}: {result.inserted}</p>
          <p className="text-blue-400">{t('updated')}: {result.updated}</p>
          <p className="text-yellow-400">{t('skipped')}: {result.skipped}</p>
          {result.errors?.length > 0 && (
            <div className="mt-2">
              <p className="text-red-400">{t('errors')}:</p>
              {result.errors.map((e: any, i: number) => (
                <p key={i} className="text-xs text-red-300">行{e.row}: {e.field} - {e.message}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
